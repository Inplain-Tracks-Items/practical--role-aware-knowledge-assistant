# LLMProvider backed by the OpenAI Chat Completions API, streamed token by token.
# ICS layer: provider
# CRD component: be.OpenAIProvider.stream_chat
# Called by: core/dependencies.py (LLM_PROVIDER=openai), feature_chat/services/service_stream_answer.py
# Calls: OpenAI API (HTTPS, needs OPENAI_API_KEY)
# Step: added in step 4 (Stream answers)

from typing import Any, AsyncIterator, Callable  # types of the LLMProvider contract

from openai import AsyncOpenAI  # official async client


class OpenAIProvider:
    """Streams answers from an OpenAI chat model."""

    def __init__(self, api_key: str, model: str) -> None:
        """api_key: OPENAI_API_KEY. model: e.g. gpt-4o-mini (OPENAI_MODEL)."""
        # One client per process (built once by core/dependencies.py): it keeps the HTTP connection pool.
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def stream_chat(
        self,
        system_prompt: str,
        user_message: str,
        tools: list[Callable[..., Any]] | None = None,
    ) -> AsyncIterator[str]:
        """Stream the answer; tools are accepted for the interface and used from step 5."""
        # The system message carries the rules and the allowed passages; the user message is the question.
        stream = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_message}],
            stream=True,
        )
        # Each streamed chunk holds a small delta of the answer; empty deltas (role, finish) are skipped.
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
