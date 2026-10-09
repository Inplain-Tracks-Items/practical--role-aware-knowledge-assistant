# Streams the LLM's answer to one question; the only chat code that talks to the LLM provider.
# ICS layer: service
# CRD component: be.service_stream_answer
# Called by: feature_chat/handlers/handle_chat_socket.py
# Calls: be.FakeProvider.stream_chat (through the LLMProvider interface)
# Step: added in step 1 (Authenticated WebSocket)

from typing import AsyncIterator  # the answer is an async stream of text pieces

from app.providers.llm.base import LLMProvider  # interface only; the concrete provider is injected

# Step 1 has no documents yet, so the instructions are fixed. Step 4 replaces this
# with a prompt built from the passages the user is allowed to see.
SYSTEM_PROMPT = "You are the Northwind Logistics assistant. Answer briefly and politely."


async def service_stream_answer(user_message: str, llm: LLMProvider) -> AsyncIterator[str]:
    """Yield the answer to user_message piece by piece.

    user_message: the question text from the client.
    llm: the shared provider from core/dependencies.py (FakeProvider unless configured otherwise).
    """
    # Pass each piece through as soon as the provider produces it: the handler forwards
    # it to the socket immediately, which is what makes the answer appear to "type".
    async for piece in llm.stream_chat(SYSTEM_PROMPT, user_message):
        yield piece
