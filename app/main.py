# Entry point of the backend: builds the FastAPI app and plugs in each feature's router. No logic here.
# Run: uvicorn app.main:app --reload
# ICS layer: door
# Called by: uvicorn, tests (TestClient)
# Calls: feature_chat/router.py
# Step: added in step 1 (Authenticated WebSocket)

from fastapi import FastAPI  # the ASGI application

from app.features.feature_chat.router import router as chat_router  # /ws/chat

# The title shows up in the auto-generated docs at /docs.
app = FastAPI(title="Northwind Role-Aware Knowledge Assistant")

# Each feature brings its own routes; main.py only assembles them.
app.include_router(chat_router)
