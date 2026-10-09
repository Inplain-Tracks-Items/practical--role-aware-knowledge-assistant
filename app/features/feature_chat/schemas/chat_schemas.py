# Pydantic models of the /ws/chat wire protocol: every message the client sends and the server returns.
# ICS layer: config (schemas)
# Called by: feature_chat/handlers/handle_chat_socket.py
# Calls: Pydantic validation
# Step: added in step 1 (Authenticated WebSocket); changed in step 3: SourcesEvent

from typing import Literal  # pins each message to its "type" value

from pydantic import BaseModel  # parses and validates JSON messages


class ClientMessage(BaseModel):
    """Anything the client sends.

    {"type": "auth", "token": "<jwt>"} must come first; afterwards
    {"type": "message", "text": "<question>"} for every question.
    """

    type: Literal["auth", "message"]
    token: str | None = None
    text: str | None = None


class AuthSuccessEvent(BaseModel):
    """Server -> client after a valid token: who the server thinks you are."""

    type: Literal["auth_success"] = "auth_success"
    user_id: str
    name: str
    role: str
    clearance: str


class AuthFailedEvent(BaseModel):
    """Server -> client when the handshake fails; the server closes the socket right after."""

    type: Literal["auth_failed"] = "auth_failed"
    message: str


class SourceRef(BaseModel):
    """One document page the answer may draw on: the citation shown to the user."""

    source_file: str
    page: int


class SourcesEvent(BaseModel):
    """Server -> client before the answer: the pages retrieved for this user and question.

    Only pages the user may read can appear here, because retrieval filters by access.
    """

    type: Literal["sources"] = "sources"
    sources: list[SourceRef]


class StreamEvent(BaseModel):
    """Server -> client: one piece of the answer, in order."""

    type: Literal["stream"] = "stream"
    text: str


class DoneEvent(BaseModel):
    """Server -> client: the answer to the last question is complete."""

    type: Literal["done"] = "done"


class ErrorEvent(BaseModel):
    """Server -> client: this message could not be handled; the connection stays open."""

    type: Literal["error"] = "error"
    message: str
