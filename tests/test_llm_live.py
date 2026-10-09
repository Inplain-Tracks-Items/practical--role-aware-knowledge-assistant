# Calls the real configured LLM once with an allowed passage. Costs a request, so it only runs with RUN_LIVE_LLM=1.
# ICS layer: test
# Covers: be.OpenAIProvider.stream_chat or be.GeminiProvider.stream_chat, be.service_build_prompt
# Step: added in step 4 (Stream answers)

import asyncio  # the provider streams asynchronously
import os  # RUN_LIVE_LLM switch and provider settings

import pytest  # skip marker

from app.features.feature_chat.services.service_build_prompt import service_build_prompt
from app.providers.vectorstore.retrieved_chunk import RetrievedChunk

PASSAGE = RetrievedChunk(
    text="Drivers earn a safe driving bonus of 150 euros per quarter when they have no preventable incidents.",
    source_file="driver_safety_manual.pdf", page=1, distance=0.3,
)


@pytest.mark.skipif(os.environ.get("RUN_LIVE_LLM") != "1", reason="set RUN_LIVE_LLM=1 plus LIVE_LLM_PROVIDER and its API key")
def test_real_llm_streams_a_cited_answer_from_the_context():
    # The real model answers from the passage (150 euros) and cites it, streaming more than one piece.
    from app.providers.llm.gemini_provider import GeminiProvider
    from app.providers.llm.openai_provider import OpenAIProvider

    if os.environ.get("LIVE_LLM_PROVIDER", "gemini") == "openai":
        llm = OpenAIProvider(os.environ["OPENAI_API_KEY"], os.environ.get("OPENAI_MODEL", "gpt-4o-mini"))
    else:
        llm = GeminiProvider(os.environ["GEMINI_API_KEY"], os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"))

    async def collect() -> list[str]:
        return [piece async for piece in llm.stream_chat(service_build_prompt([PASSAGE]), "What bonus can I earn?")]

    pieces = asyncio.run(collect())
    answer = "".join(pieces)
    assert "150" in answer
    assert "driver_safety_manual.pdf" in answer
