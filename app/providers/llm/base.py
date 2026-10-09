# The interface every LLM provider implements; features depend on this, never on a concrete SDK.
# ICS layer: provider (interface)
# Called by: feature_chat services (type hints), core/dependencies.py
# Calls: nothing (a Protocol has no behaviour)
# Step: added in step 1 (Authenticated WebSocket)

from typing import Any, AsyncIterator, Callable, Protocol  # typing tools to describe the contract


class LLMProvider(Protocol):
    """Anything that can stream a chat answer token by token.

    A Protocol is structural: FakeProvider (and later OpenAIProvider, GeminiProvider)
    match it by having the same method, without inheriting from it.
    """

    def stream_chat(
        self,
        system_prompt: str,
        user_message: str,
        tools: list[Callable[..., Any]] | None = None,
    ) -> AsyncIterator[str]:
        """Stream the answer to user_message.

        system_prompt: the instructions (and later the retrieved context) for the model.
        user_message: the question exactly as the user typed it.
        tools: async Python callables the model may call while answering (used from step 5).
        Yields text pieces in order; joined, they form the full answer.
        """
        ...
