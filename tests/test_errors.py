# Proves the hardening: failures become error events, the connection survives them, and limits are enforced.
# ICS layer: test
# Covers: be.handle_chat_socket (error handling, length limit), be.configure_logging
# Step: added in step 6 (Hardening)

import logging  # captures the server-side log line

from app.core.dependencies import get_llm_provider
from app.features.feature_chat.handlers.handle_chat_socket import ANSWER_FAILED
from app.main import app
from tests.fakes.recording_llm_provider import RecordingLLMProvider


class FailingOnceProvider(RecordingLLMProvider):
    """Raises like a provider out of quota on the first call, then answers normally."""

    async def stream_chat(self, system_prompt, user_message, tools=None):
        self.calls.append({"user_message": user_message})
        if len(self.calls) == 1:
            raise RuntimeError("429 Too Many Requests (simulated quota error)")
        for piece in self.pieces:
            yield piece


def _login(ws, token):
    """Send the auth message and return the auth_success event."""
    ws.send_json({"type": "auth", "token": token})
    return ws.receive_json()


def _until_done_or_error(ws) -> list[dict]:
    """Read events until done or error, inclusive."""
    events = []
    while True:
        events.append(ws.receive_json())
        if events[-1]["type"] in ("done", "error"):
            return events


def test_llm_failure_becomes_an_error_event_and_the_next_question_works(indexed, client, token_for, caplog):
    # handle_chat_socket: a provider exception (quota, network) is logged with its details, the client gets
    # one generic error event, and the same connection answers the next question.
    provider = FailingOnceProvider()
    app.dependency_overrides[get_llm_provider] = lambda: provider
    with caplog.at_level(logging.ERROR), client.websocket_connect("/ws/chat") as ws:
        _login(ws, token_for("driver"))
        ws.send_json({"type": "message", "text": "What bonus can I earn?"})
        first = _until_done_or_error(ws)
        ws.send_json({"type": "message", "text": "What bonus can I earn?"})
        second = _until_done_or_error(ws)
    assert first[-1] == {"type": "error", "message": ANSWER_FAILED}
    assert "429" not in first[-1]["message"]
    assert "429 Too Many Requests" in caplog.text
    assert second[-1] == {"type": "done"}
    assert "".join(e.get("text", "") for e in second if e["type"] == "stream") == "".join(provider.pieces)


def test_too_long_message_is_refused_without_calling_the_model(indexed, client, token_for, settings):
    # handle_chat_socket: text longer than MAX_MESSAGE_CHARS -> error event, no LLM call, connection open.
    provider = RecordingLLMProvider()
    app.dependency_overrides[get_llm_provider] = lambda: provider
    with client.websocket_connect("/ws/chat") as ws:
        _login(ws, token_for("sales"))
        ws.send_json({"type": "message", "text": "x" * (settings.max_message_chars + 1)})
        assert ws.receive_json()["message"].startswith("message too long")
        ws.send_json({"type": "message", "text": "hello"})
        assert _until_done_or_error(ws)[-1]["type"] == "done"
    assert [c["user_message"] for c in provider.calls] == ["hello"]


def test_malformed_messages_keep_the_connection_open(indexed, client, token_for):
    # handle_chat_socket: non-JSON text and an unknown message type get "invalid message"; the session continues.
    with client.websocket_connect("/ws/chat") as ws:
        _login(ws, token_for("dispatcher"))
        ws.send_text("this is not json")
        assert ws.receive_json() == {"type": "error", "message": "invalid message"}
        ws.send_json({"type": "delete_everything"})
        assert ws.receive_json() == {"type": "error", "message": "invalid message"}
        ws.send_json({"type": "message", "text": "hello"})
        assert _until_done_or_error(ws)[-1]["type"] == "done"
