# Shared pytest fixtures: a test secret, the app under test and a helper that mints tokens.
# ICS layer: test
# Called by: pytest, before every test module
# Calls: core/config.py, feature_auth service_mint_token, app/main.py
# Step: added in step 1 (Authenticated WebSocket)

import os  # set environment variables before the app reads its settings

# Settings are read from the environment, so the test values must exist before anything
# imports app.core.config. A fixed secret makes tokens reproducible; "fake" keeps tests offline.
os.environ["JWT_SECRET"] = "test-secret-only-for-pytest-0123456789abcdef"
os.environ["LLM_PROVIDER"] = "fake"

import pytest  # fixtures  # noqa: E402  (imports after the env setup on purpose)
from fastapi.testclient import TestClient  # drives the app in-process, WebSockets included  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.token_claims import TokenClaims  # noqa: E402
from app.features.feature_auth.configs.demo_users import DEMO_USERS  # noqa: E402
from app.features.feature_auth.services.service_mint_token import service_mint_token  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def settings():
    """The Settings the app uses in tests (built from the env set above)."""
    get_settings.cache_clear()
    return get_settings()


@pytest.fixture
def client():
    """A TestClient for the app; dependency overrides set by a test are removed afterwards."""
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def token_for(settings):
    """Return a function that mints a token for a demo user by role, e.g. token_for("driver")."""

    def _mint(role: str, ttl_seconds: int | None = None) -> str:
        user: TokenClaims = next(u for u in DEMO_USERS if u.role == role)
        return service_mint_token(user, settings, ttl_seconds=ttl_seconds)

    return _mint
