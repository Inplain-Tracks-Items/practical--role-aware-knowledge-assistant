# Test double for LLMProvider: remembers exactly what it was sent and streams a fixed answer.
# ICS layer: test
# Called by: tests that check what reaches the model and how the answer streams
# Step: added in step 4 (Stream answers)

from typing import Any, AsyncIterator, Callable  # LLMProvider contract types


class RecordingLLMProvider:
    """Records every call; streams `pieces` in order."""

    def __init__(self, pieces: list[str] | None = None) -> None:
        self.pieces = pieces or ["Drivers earn ", "150 euros per quarter ", "(driver_safety_manual.pdf p.1)."]
        self.calls: list[dict] = []

    async def stream_chat(self, system_prompt: str, user_message: str, tools: list[Callable[..., Any]] | None = None) -> AsyncIterator[str]:
        """Store the arguments, then yield the fixed pieces."""
        self.calls.append({"system_prompt": system_prompt, "user_message": user_message, "tools": tools or []})
        for piece in self.pieces:
            yield piece
