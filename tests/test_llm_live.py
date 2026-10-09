# Calls the real LLM: once with an allowed passage, once with the shipment tool. Costs requests, so it only runs with RUN_LIVE_LLM=1.
# ICS layer: test
# Covers: be.OpenAIProvider.stream_chat or be.GeminiProvider.stream_chat, be.service_build_prompt, be.tool_bind_shipment_overview
# Step: added in step 4 (Stream answers); changed in step 5: live tool-calling test

import asyncio  # the provider streams asynchronously
import os  # RUN_LIVE_LLM switch and provider settings

import pytest  # skip marker

from app.features.feature_chat.services.service_build_prompt import service_build_prompt
from app.providers.vectorstore.retrieved_chunk import RetrievedChunk

PASSAGE = RetrievedChunk(
    text="Drivers earn a safe driving bonus of 150 euros per quarter when they have no preventable incidents.",
    source_file="driver_safety_manual.pdf", page=1, distance=0.3,
)


LIVE = pytest.mark.skipif(os.environ.get("RUN_LIVE_LLM") != "1", reason="set RUN_LIVE_LLM=1 plus LIVE_LLM_PROVIDER and its API key")


def _live_llm():
    """Build the provider named by LIVE_LLM_PROVIDER (default gemini) from its env key."""
    from app.providers.llm.gemini_provider import GeminiProvider
    from app.providers.llm.openai_provider import OpenAIProvider

    if os.environ.get("LIVE_LLM_PROVIDER", "gemini") == "openai":
        return OpenAIProvider(os.environ["OPENAI_API_KEY"], os.environ.get("OPENAI_MODEL", "gpt-4o-mini"))
    return GeminiProvider(os.environ["GEMINI_API_KEY"], os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"))


@LIVE
def test_real_llm_streams_a_cited_answer_from_the_context():
    # The real model answers from the passage (150 euros) and cites it.
    llm = _live_llm()

    async def collect() -> list[str]:
        return [piece async for piece in llm.stream_chat(service_build_prompt([PASSAGE]), "What bonus can I earn?")]

    pieces = asyncio.run(collect())
    answer = "".join(pieces)
    assert "150" in answer
    assert "driver_safety_manual.pdf" in answer


@LIVE
def test_real_llm_calls_the_bound_shipment_tool():
    # The real model decides to call get_shipment_overview for NW-1042 and answers from its result;
    # for another driver's shipment it gets the "not visible" error and must not invent a status.
    from app.features.feature_auth.configs.demo_users import DEMO_USERS
    from app.features.feature_shipment_tool.tool_bind_shipment_overview import tool_bind_shipment_overview

    llm = _live_llm()
    driver = next(u for u in DEMO_USERS if u.role == "driver")
    calls = []
    real_tool = tool_bind_shipment_overview(driver)

    async def get_shipment_overview(shipment_id: str) -> dict:
        """Get live status, ETA (with delay flag) and service level of one Northwind shipment.

        Call this when the user asks about a specific shipment; ids look like NW-1042.
        Returns an "error" field when the shipment does not exist or the user may not see it.
        """
        # Same contract as the real bound tool, plus a record of the call.
        calls.append(shipment_id)
        return await real_tool(shipment_id)

    async def ask(question: str) -> str:
        return "".join([p async for p in llm.stream_chat(service_build_prompt([]), question, tools=[get_shipment_overview])])

    own = asyncio.run(ask("Where is shipment NW-1042 right now and is it late?"))
    other = asyncio.run(ask("Where is shipment NW-1077 right now?"))
    assert "NW-1042" in calls and "NW-1077" in calls
    assert "Arnhem" in own
    assert "Venlo" not in other
