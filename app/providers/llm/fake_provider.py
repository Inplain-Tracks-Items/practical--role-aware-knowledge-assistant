# An offline LLM provider that echoes the question, so the whole system runs and is testable without an API key.
# ICS layer: provider
# CRD component: be.FakeProvider.stream_chat
# Called by: core/dependencies.py (LLM_PROVIDER=fake), feature_chat/services/service_stream_answer.py
# Calls: nothing external
# Step: added in step 1 (Authenticated WebSocket)

from typing import Any, AsyncIterator, Callable  # types of the LLMProvider contract


class FakeProvider:
    """Deterministic stand-in for a real model: same interface, predictable output."""

    async def stream_chat(
        self,
        system_prompt: str,
        user_message: str,
        tools: list[Callable[..., Any]] | None = None,
    ) -> AsyncIterator[str]:
        """Stream "Echo: <question>" one word at a time.

        system_prompt and tools are accepted to honour the LLMProvider contract but are not used yet.
        Yields each word followed by a space, the way a real model streams small text pieces.
        """
        # Split the reply into words so the client sees several "stream" events, as with a real model.
        for word in f"Echo: {user_message}".split():
            yield word + " "
