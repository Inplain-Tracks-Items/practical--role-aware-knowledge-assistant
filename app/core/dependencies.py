# Builds every provider once per process and hands it to routes through FastAPI's Depends().
# ICS layer: config (dependency wiring)
# CRD component: be.get_llm_provider
# Called by: feature_chat/router.py (Depends), tests (dependency_overrides)
# Calls: core/config.py, providers/llm/*
# Step: added in step 1 (Authenticated WebSocket)

from functools import lru_cache  # one instance per process: a provider is never rebuilt per request

from app.core.config import get_settings  # decides which concrete provider to build
from app.providers.llm.base import LLMProvider  # the interface features depend on
from app.providers.llm.fake_provider import FakeProvider  # offline provider, no API key needed


@lru_cache
def get_llm_provider() -> LLMProvider:
    """Return the shared LLM provider chosen by LLM_PROVIDER.

    Features only ever see the LLMProvider interface, so switching providers is a
    config change, never a code change in feature_chat.
    Raises ValueError for an unknown provider name, at the first request that needs it.
    """
    settings = get_settings()
    # Step 1 only ships the fake provider; real providers are added in step 4.
    if settings.llm_provider == "fake":
        return FakeProvider()
    raise ValueError(f"unknown LLM_PROVIDER '{settings.llm_provider}'")
