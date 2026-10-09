# LLMProvider backed by the OpenAI Chat Completions API, streamed token by token, with a tool-calling loop.
# ICS layer: provider
# CRD component: be.OpenAIProvider.stream_chat
# Called by: core/dependencies.py (LLM_PROVIDER=openai), feature_chat/services/service_stream_answer.py
# Calls: OpenAI API (HTTPS, needs OPENAI_API_KEY); the tool functions it is given
# Step: added in step 4 (Stream answers); changed in step 5: executes tool calls (concurrently) between streamed rounds

import asyncio  # several tool calls requested in one round run concurrently
import inspect  # reads a tool's parameters to describe it to the model
import json  # tool arguments arrive as JSON text; results go back as JSON text
from typing import Any, AsyncIterator, Callable  # types of the LLMProvider contract

from openai import AsyncOpenAI  # official async client

# Safety net: a model that keeps asking for tools stops after this many rounds.
MAX_TOOL_ROUNDS = 3


def _tool_schema(fn: Callable[..., Any]) -> dict:
    """Describe a Python tool to OpenAI: its name, docstring and string parameters."""
    params = list(inspect.signature(fn).parameters)
    return {
        "type": "function",
        "function": {
            "name": fn.__name__,
            "description": (fn.__doc__ or "").strip(),
            # Our tools take string arguments only (e.g. shipment_id), all required.
            "parameters": {"type": "object", "properties": {p: {"type": "string"} for p in params}, "required": params},
        },
    }


class OpenAIProvider:
    """Streams answers from an OpenAI chat model and runs the tools it asks for."""

    def __init__(self, api_key: str, model: str, client: Any = None) -> None:
        """api_key: OPENAI_API_KEY. model: e.g. gpt-4o-mini. client: injected only by tests (a stub)."""
        # One client per process (built once by core/dependencies.py): it keeps the HTTP connection pool.
        self._client = client or AsyncOpenAI(api_key=api_key)
        self._model = model

    async def stream_chat(
        self,
        system_prompt: str,
        user_message: str,
        tools: list[Callable[..., Any]] | None = None,
    ) -> AsyncIterator[str]:
        """Stream the answer; when the model requests tools, run them and stream the next round.

        Every round is streamed: text deltas are yielded as they arrive, tool-call deltas are
        collected. A round without tool calls is the final answer.
        """
        tools = tools or []
        tool_map = {fn.__name__: fn for fn in tools}
        # Only send "tools" when there are some; an empty list is rejected by the API.
        extra = {"tools": [_tool_schema(fn) for fn in tools]} if tools else {}
        messages: list[dict] = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_message}]

        for _ in range(MAX_TOOL_ROUNDS + 1):
            # Step 1: one streamed round.
            stream = await self._client.chat.completions.create(model=self._model, messages=messages, stream=True, **extra)
            calls: dict[int, dict] = {}
            async for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                # Text goes straight to the user.
                if delta.content:
                    yield delta.content
                # Tool calls arrive in fragments (id, name, then pieces of the JSON arguments), keyed by index.
                for part in delta.tool_calls or []:
                    slot = calls.setdefault(part.index, {"id": "", "name": "", "arguments": ""})
                    slot["id"] = part.id or slot["id"]
                    if part.function and part.function.name:
                        slot["name"] += part.function.name
                    if part.function and part.function.arguments:
                        slot["arguments"] += part.function.arguments
            # Step 2: no tool calls means the answer is complete.
            if not calls:
                return
            # Step 3: record the model's tool request, run all requested tools concurrently, send the results back.
            requested = list(calls.values())
            messages.append({"role": "assistant", "tool_calls": [
                {"id": c["id"], "type": "function", "function": {"name": c["name"], "arguments": c["arguments"]}} for c in requested
            ]})
            results = await asyncio.gather(*(self._run_tool(tool_map, c) for c in requested))
            for call, result in zip(requested, results):
                messages.append({"role": "tool", "tool_call_id": call["id"], "content": json.dumps(result)})

    async def _run_tool(self, tool_map: dict[str, Callable[..., Any]], call: dict) -> Any:
        """Run one requested tool; an unknown name or bad JSON becomes an error result, not a crash."""
        fn = tool_map.get(call["name"])
        if fn is None:
            return {"error": f"unknown tool {call['name']}"}
        try:
            args = json.loads(call["arguments"] or "{}")
        except json.JSONDecodeError:
            return {"error": "tool arguments were not valid JSON"}
        return await fn(**args)
