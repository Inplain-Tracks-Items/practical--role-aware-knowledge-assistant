# Proves the auth handshake of /ws/chat: only a valid, unexpired token with known claims gets an answer.
# ICS layer: test
# Covers: be.chat_socket, be.handle_chat_socket, be.verify_jwt, be.service_mint_token, be.service_stream_answer
# Step: added in step 1 (Authenticated WebSocket)

import jwt  # to forge tokens the server must reject

from app.core.verify_jwt import verify_jwt
from app.features.feature_auth.handlers.handle_mint_demo_tokens import handle_mint_demo_tokens


def _collect_answer(ws) -> str:
    """Read stream events until "done" and return the joined answer text."""
    text = ""
    while True:
        event = ws.receive_json()
        if event["type"] == "done":
            return text
        assert event["type"] == "stream", event
        text += event["text"]


def test_valid_token_logs_in_and_gets_a_streamed_answer(client, token_for):
    # handle_chat_socket: a valid driver token -> auth_success with the token's claims,
    # then a question -> several stream events followed by done.
    with client.websocket_connect("/ws/chat") as ws:
        ws.send_json({"type": "auth", "token": token_for("driver")})
        hello = ws.receive_json()
        assert hello == {"type": "auth_success", "user_id": "drv-101", "name": "Dana Okafor", "role": "driver", "clearance": "internal"}
        ws.send_json({"type": "message", "text": "hello there"})
        assert _collect_answer(ws).strip() == "Echo: hello there"


def test_expired_token_is_rejected(client, token_for):
    # verify_jwt: a token whose exp is in the past -> auth_failed "token expired".
    with client.websocket_connect("/ws/chat") as ws:
        ws.send_json({"type": "auth", "token": token_for("driver", ttl_seconds=-10)})
        assert ws.receive_json() == {"type": "auth_failed", "message": "token expired"}


def test_token_signed_with_another_secret_is_rejected(client):
    # verify_jwt: a forged signature -> auth_failed "invalid token".
    forged = jwt.encode({"sub": "x", "email": "x@x", "name": "X", "role": "leadership", "clearance": "confidential"}, "wrong-secret-wrong-secret-wrong-secret-xyz", algorithm="HS256")
    with client.websocket_connect("/ws/chat") as ws:
        ws.send_json({"type": "auth", "token": forged})
        assert ws.receive_json() == {"type": "auth_failed", "message": "invalid token"}


def test_unknown_role_is_rejected(settings):
    # TokenClaims: a correctly signed token with a role outside Role is not trusted.
    token = jwt.encode({"sub": "x", "email": "x@x", "name": "X", "role": "ceo", "clearance": "confidential"}, settings.jwt_secret, algorithm="HS256")
    try:
        verify_jwt(token, settings)
        raise AssertionError("verify_jwt accepted an unknown role")
    except Exception as exc:
        assert str(exc) == "token claims are incomplete or unknown"


def test_question_before_auth_is_refused(client):
    # handle_chat_socket: the first message must be auth; anything else -> auth_failed.
    with client.websocket_connect("/ws/chat") as ws:
        ws.send_json({"type": "message", "text": "what is the bonus plan?"})
        assert ws.receive_json()["type"] == "auth_failed"


def test_cli_mints_a_valid_token_for_every_demo_user(settings):
    # handle_mint_demo_tokens + service_mint_token: every minted token verifies back to its user.
    for entry in handle_mint_demo_tokens(settings):
        assert verify_jwt(entry["token"], settings) == entry["user"]
