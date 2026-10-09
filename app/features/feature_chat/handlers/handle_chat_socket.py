# Runs one /ws/chat connection end to end: accept -> auth handshake -> message loop -> streamed answer.
# ICS layer: handler
# CRD component: be.handle_chat_socket
# Called by: feature_chat/router.py (the /ws/chat door)
# Calls: be.verify_jwt, be.service_retrieve_chunks, be.service_stream_answer
# Step: added in step 1 (Authenticated WebSocket); changed in step 3: retrieves allowed chunks and sends their sources

from fastapi import WebSocket, WebSocketDisconnect  # the socket and the "client went away" signal

from app.core.auth_error import AuthError  # raised by verify_jwt for any untrusted token
from app.core.config import Settings  # carries the JWT secret for verification
from app.core.verify_jwt import verify_jwt  # turns the token into trusted claims
from app.features.feature_chat.schemas.chat_schemas import (  # every message shape of the protocol
    AuthFailedEvent,
    AuthSuccessEvent,
    ClientMessage,
    DoneEvent,
    ErrorEvent,
    SourceRef,
    SourcesEvent,
    StreamEvent,
)
from app.features.feature_chat.services.service_retrieve_chunks import service_retrieve_chunks  # access-filtered search
from app.features.feature_chat.services.service_stream_answer import service_stream_answer  # talks to the LLM
from app.providers.embeddings.base import EmbeddingProvider  # interfaces of the injected providers
from app.providers.llm.base import LLMProvider
from app.providers.vectorstore.base import VectorStore


async def handle_chat_socket(
    websocket: WebSocket,
    settings: Settings,
    llm: LLMProvider,
    embedder: EmbeddingProvider,
    store: VectorStore,
) -> None:
    """Serve one chat connection until the client disconnects.

    websocket: the accepted-to-be connection from the door.
    settings: JWT settings for the handshake and retrieval_top_k.
    llm: the shared LLM provider, injected by the door.
    embedder, store: the shared embedding provider and vector store, injected by the door.
    Returns when the client disconnects or the handshake fails (the socket is then closed).
    """
    # Step 1: accept the connection; nothing is answered until the client proves who it is.
    await websocket.accept()

    # Step 2: auth handshake. The first message must be {"type": "auth", "token": ...}.
    try:
        first = ClientMessage(**await websocket.receive_json())
    except WebSocketDisconnect:
        # The client left before authenticating; there is nobody to answer.
        return
    except Exception:
        # Not JSON, or not a known message shape: refuse and close.
        await websocket.send_json(AuthFailedEvent(message="first message must be an auth message").model_dump())
        await websocket.close()
        return
    if first.type != "auth" or not first.token:
        # A question before logging in is refused the same way as a bad token.
        await websocket.send_json(AuthFailedEvent(message="first message must be an auth message").model_dump())
        await websocket.close()
        return
    try:
        # The claims returned here are this connection's identity from now on.
        user = verify_jwt(first.token, settings)
    except AuthError as exc:
        await websocket.send_json(AuthFailedEvent(message=str(exc)).model_dump())
        await websocket.close()
        return
    # Tell the client who it is logged in as, so it can show it (and so tests can assert it).
    await websocket.send_json(
        AuthSuccessEvent(user_id=user.sub, name=user.name, role=user.role, clearance=user.clearance).model_dump()
    )

    # Step 3: message loop, one question at a time, until the client disconnects.
    try:
        while True:
            try:
                message = ClientMessage(**await websocket.receive_json())
            except WebSocketDisconnect:
                # Re-raise so the outer handler ends the loop cleanly.
                raise
            except Exception:
                # A malformed message is reported but does not end the connection.
                await websocket.send_json(ErrorEvent(message="invalid message").model_dump())
                continue
            # Only questions are answered; a second auth message or an empty text is ignored.
            if message.type != "message" or not message.text:
                continue
            # Step 4: retrieve the chunks this user may read that best match the question.
            # The user's role and clearance come from the verified token (step 2), not from the message.
            chunks = await service_retrieve_chunks(message.text, user, embedder, store, settings.retrieval_top_k)
            # Tell the client which pages were found (deduplicated, in relevance order).
            pages = list(dict.fromkeys((c.source_file, c.page) for c in chunks))
            await websocket.send_json(SourcesEvent(sources=[SourceRef(source_file=f, page=p) for f, p in pages]).model_dump())
            # Step 5: stream the answer piece by piece, then mark the end with "done".
            async for piece in service_stream_answer(message.text, llm):
                await websocket.send_json(StreamEvent(text=piece).model_dump())
            await websocket.send_json(DoneEvent().model_dump())
    except WebSocketDisconnect:
        # Normal end of a conversation: the client closed the socket.
        return
