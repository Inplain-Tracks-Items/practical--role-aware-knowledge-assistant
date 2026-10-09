# LLMProvider backed by Google Gemini (google-genai SDK), streamed piece by piece.
# ICS layer: provider
# CRD component: be.GeminiProvider.stream_chat
# Called by: core/dependencies.py (LLM_PROVIDER=gemini), feature_chat/services/service_stream_answer.py
# Calls: Gemini API (HTTPS, needs GEMINI_API_KEY)
# Step: added in step 4 (Stream answers)

from typing import Any, AsyncIterator, Callable  # types of the LLMProvider contract

from google import genai  # official Gemini SDK
from google.genai import types  # request configuration types


class GeminiProvider:
    """Streams answers from a Gemini model."""

    def __init__(self, api_key: str, model: str) -> None:
        """api_key: GEMINI_API_KEY. model: e.g. gemini-2.5-flash (GEMINI_MODEL)."""
        # One client per process (built once by core/dependencies.py).
        self._client = genai.Client(api_key=api_key)
        self._model = model

    async def stream_chat(
        self,
        system_prompt: str,
        user_message: str,
        tools: list[Callable[..., Any]] | None = None,
    ) -> AsyncIterator[str]:
        """Stream the answer; tools are accepted for the interface and used from step 5."""
        # Gemini takes the rules and passages as system_instruction, separate from the question.
        stream = await self._client.aio.models.generate_content_stream(
            model=self._model,
            contents=user_message,
            config=types.GenerateContentConfig(system_instruction=system_prompt),
        )
        # Some streamed parts carry no text (metadata only); they are skipped.
        async for chunk in stream:
            if chunk.text:
                yield chunk.text
