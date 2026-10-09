# LLMProvider backed by Google Gemini (google-genai SDK), streamed piece by piece, with automatic function calling.
# ICS layer: provider
# CRD component: be.GeminiProvider.stream_chat
# Called by: core/dependencies.py (LLM_PROVIDER=gemini), feature_chat/services/service_stream_answer.py
# Calls: Gemini API (HTTPS, needs GEMINI_API_KEY); the tool functions it is given
# Step: added in step 4 (Stream answers); changed in step 5: tools through the chat API's automatic function calling

from typing import Any, AsyncIterator, Callable  # types of the LLMProvider contract

from google import genai  # official Gemini SDK
from google.genai import types  # request configuration types


class GeminiProvider:
    """Streams answers from a Gemini model; the SDK runs the tools the model asks for."""

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
        """Stream the answer. Plain Python functions in tools are described to the model from their
        name, type hints and docstring; when the model calls one, the SDK awaits it and continues."""
        # The chat API (not models.generate_content_stream) is where the SDK supports automatic
        # function calling while streaming. A fresh chat per question: no history between questions.
        chat = self._client.aio.chats.create(
            model=self._model,
            config=types.GenerateContentConfig(system_instruction=system_prompt, tools=tools or []),
        )
        stream = await chat.send_message_stream(user_message)
        # Parts that carry a function call or metadata have no text; they are skipped.
        async for chunk in stream:
            if chunk.text:
                yield chunk.text
