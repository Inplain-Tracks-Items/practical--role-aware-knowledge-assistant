# Thin door of the chat feature: declares the /ws/chat WebSocket, injects its dependencies, delegates once.
# ICS layer: door
# CRD component: be.chat_socket
# Called by: app/main.py (include_router), the client over ws://<host>/ws/chat
# Calls: be.handle_chat_socket
# Step: added in step 1 (Authenticated WebSocket)

from fastapi import APIRouter, Depends, WebSocket  # routing and dependency injection

from app.core.config import get_settings  # settings singleton, injected so tests can override it
from app.core.dependencies import get_llm_provider  # LLM singleton, injected so tests can swap in a fake
from app.features.feature_chat.handlers.handle_chat_socket import handle_chat_socket  # the whole flow

# One router per feature; main.py includes it.
router = APIRouter()


@router.websocket("/ws/chat")
async def chat_socket(websocket: WebSocket, settings=Depends(get_settings), llm=Depends(get_llm_provider)) -> None:
    """WebSocket door: FastAPI resolves the dependencies, the handler does everything else."""
    await handle_chat_socket(websocket, settings, llm)
