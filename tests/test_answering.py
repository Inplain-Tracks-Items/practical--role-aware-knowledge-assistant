# Proves answering: the prompt holds only allowed passages with citation labels, the answer streams in order, and the LLM is chosen by config.
# ICS layer: test
# Covers: be.service_build_prompt, be.service_stream_answer, be.handle_chat_socket, be.get_llm_provider
# Step: added in step 4 (Stream answers)

import pytest  # monkeypatch, raises

from app.core.config import get_settings
from app.core.dependencies import get_llm_provider
from app.features.feature_chat.services.service_build_prompt import NO_CONTEXT, service_build_prompt
from app.main import app
from app.providers.llm.gemini_provider import GeminiProvider
from app.providers.llm.openai_provider import OpenAIProvider
from app.providers.vectorstore.retrieved_chunk import RetrievedChunk
from tests.fakes.recording_llm_provider import RecordingLLMProvider


def test_prompt_labels_every_passage_with_its_citation():
    # service_build_prompt: each passage is preceded by "[file p.N]", the label the model must cite.
    prompt = service_build_prompt([RetrievedChunk(text="Break after 4.5 hours.", source_file="driver_safety_manual.pdf", page=1, distance=0.2)])
    assert "[driver_safety_manual.pdf p.1]\nBreak after 4.5 hours." in prompt
    assert "ONLY the passages in CONTEXT" in prompt


def test_prompt_says_so_when_nothing_allowed_matched():
    # service_build_prompt: no allowed passages -> an explicit placeholder, so the model says it cannot find it.
    assert service_build_prompt([]).endswith(NO_CONTEXT)


def test_model_receives_only_allowed_passages_and_the_answer_streams(indexed, client, token_for):
    # handle_chat_socket -> service_build_prompt -> service_stream_answer: the driver's bonus question
    # reaches the model with driver-safety context and without a word of the leadership plan, and the
    # model's pieces arrive in order as stream events followed by done.
    recorder = RecordingLLMProvider()
    app.dependency_overrides[get_llm_provider] = lambda: recorder
    with client.websocket_connect("/ws/chat") as ws:
        ws.send_json({"type": "auth", "token": token_for("driver")})
        ws.receive_json()
        ws.send_json({"type": "message", "text": "What bonus can I earn?"})
        assert ws.receive_json()["type"] == "sources"
        pieces = []
        while (event := ws.receive_json())["type"] == "stream":
            pieces.append(event["text"])
        assert event["type"] == "done"
    assert pieces == recorder.pieces
    prompt = recorder.calls[0]["system_prompt"]
    assert "[driver_safety_manual.pdf" in prompt
    assert "leadership_compensation_plan" not in prompt and "112,000" not in prompt
    assert recorder.calls[0]["user_message"] == "What bonus can I earn?"


@pytest.fixture
def fresh_provider_cache():
    """Rebuild settings and the LLM provider from the patched env, and restore them afterwards."""
    get_settings.cache_clear()
    get_llm_provider.cache_clear()
    yield
    get_settings.cache_clear()
    get_llm_provider.cache_clear()


@pytest.mark.parametrize("name, key_var, cls", [("openai", "OPENAI_API_KEY", OpenAIProvider), ("gemini", "GEMINI_API_KEY", GeminiProvider)])
def test_llm_provider_is_chosen_by_config(monkeypatch, fresh_provider_cache, name, key_var, cls):
    # get_llm_provider: LLM_PROVIDER picks the class; building it makes no network call.
    monkeypatch.setenv("LLM_PROVIDER", name)
    monkeypatch.setenv(key_var, "test-key")
    assert isinstance(get_llm_provider(), cls)


def test_real_provider_without_key_fails_with_a_clear_message(monkeypatch, fresh_provider_cache):
    # get_llm_provider: a missing key is reported by name instead of failing later inside a stream.
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        get_llm_provider()
