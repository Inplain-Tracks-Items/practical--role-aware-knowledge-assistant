# Entry point of the backend: builds the FastAPI app and plugs in each feature's router. No logic here.
# Run: uvicorn app.main:app --reload
# ICS layer: door
# Called by: uvicorn, tests (TestClient)
# Calls: core/configure_logging.py, feature_chat/router.py
# Step: added in step 1 (Authenticated WebSocket); changed in step 6: configures logging at startup

from fastapi import FastAPI  # the ASGI application

from app.core.config import get_settings  # LOG_LEVEL
from app.core.configure_logging import configure_logging  # one-time logging setup
from app.features.feature_chat.router import router as chat_router  # /ws/chat

# Logging is configured once, before the first request, so every module's logger writes the same format.
configure_logging(get_settings().log_level)

# The title shows up in the auto-generated docs at /docs.
app = FastAPI(title="Northwind Role-Aware Knowledge Assistant")

# Each feature brings its own routes; main.py only assembles them.
app.include_router(chat_router)
