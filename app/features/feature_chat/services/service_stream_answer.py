# Streams the LLM's answer to one question; the only chat code that talks to the LLM provider.
# ICS layer: service
# CRD component: be.service_stream_answer
# Called by: feature_chat/handlers/handle_chat_socket.py
# Calls: the injected LLMProvider (be.FakeProvider.stream_chat, be.OpenAIProvider.stream_chat or be.GeminiProvider.stream_chat)
# Step: added in step 1 (Authenticated WebSocket); changed in step 4: takes the prompt built from the allowed passages;
#       changed in step 5: passes the user-bound tools to the model

from typing import Any, AsyncIterator, Callable  # the answer is an async stream; tools are async callables

from app.providers.llm.base import LLMProvider  # interface only; the concrete provider is injected


async def service_stream_answer(
    system_prompt: str,
    user_message: str,
    llm: LLMProvider,
    tools: list[Callable[..., Any]] | None = None,
) -> AsyncIterator[str]:
    """Yield the answer to user_message piece by piece.

    system_prompt: rules + allowed passages, from service_build_prompt.
    user_message: the question text from the client.
    llm: the shared provider from core/dependencies.py (chosen by LLM_PROVIDER).
    tools: functions the model may call, already bound to the user (see tool_bind_shipment_overview).
    """
    # Pass each piece through as soon as the provider produces it: the handler forwards
    # it to the socket immediately, which is what makes the answer appear to "type".
    async for piece in llm.stream_chat(system_prompt, user_message, tools=tools):
        yield piece
