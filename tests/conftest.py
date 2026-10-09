# Shared pytest fixtures: a test secret, the app under test, a token helper and an indexed test collection.
# ICS layer: test
# Called by: pytest, before every test module
# Calls: core/config.py, feature_auth service_mint_token, app/main.py, feature_sample_docs + feature_ingest handlers
# Step: added in step 1 (Authenticated WebSocket); changed in step 3: offline embedder, temp Chroma and the indexed fixture

import asyncio  # the ingestion handlers are async
import os  # set environment variables before the app reads its settings
import tempfile  # a throw-away folder for the test Chroma collection
from pathlib import Path  # repo paths

# Settings are read from the environment, so the test values must exist before anything
# imports app.core.config. A fixed secret makes tokens reproducible; "fake" keeps tests offline.
os.environ["JWT_SECRET"] = "test-secret-only-for-pytest-0123456789abcdef"
os.environ["LLM_PROVIDER"] = "fake"
# Hashing embeddings: no model download, instant, deterministic. A fresh temp folder per
# test run keeps the developer's real chroma_data/ untouched.
os.environ["EMBEDDING_PROVIDER"] = "hashing"
os.environ["CHROMA_PATH"] = tempfile.mkdtemp(prefix="northwind-test-chroma-")
os.environ["CHROMA_COLLECTION"] = "northwind_test"

import pytest  # fixtures  # noqa: E402  (imports after the env setup on purpose)
from fastapi.testclient import TestClient  # drives the app in-process, WebSockets included  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.dependencies import get_embedder, get_vectorstore  # noqa: E402
from app.core.token_claims import TokenClaims  # noqa: E402
from app.features.feature_auth.configs.demo_users import DEMO_USERS  # noqa: E402
from app.features.feature_auth.services.service_mint_token import service_mint_token  # noqa: E402
from app.features.feature_ingest.handlers.handle_ingest_documents import handle_ingest_documents  # noqa: E402
from app.features.feature_sample_docs.handlers.handle_build_sample_docs import handle_build_sample_docs  # noqa: E402
from app.main import app  # noqa: E402
from tests.fakes.fake_ocr_provider import FakeOcrProvider  # noqa: E402

DOCS_SRC = Path(__file__).resolve().parents[1] / "docs_src"


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


@pytest.fixture(scope="session")
def indexed(tmp_path_factory):
    """Build the sample PDFs and ingest them once into the app's own test collection.

    The fake OCR returns the real text of the scanned report, so the confidential incident
    review is searchable exactly as it would be after real OCR.
    Returns the ingest summary.
    """
    docs = tmp_path_factory.mktemp("docs")
    asyncio.run(handle_build_sample_docs(DOCS_SRC, docs))
    ocr = FakeOcrProvider(text=(DOCS_SRC / "incident_review_q2.md").read_text(encoding="utf-8"))
    settings = get_settings()
    return asyncio.run(handle_ingest_documents(docs, settings.chunk_size_words, settings.chunk_overlap_words, get_embedder(), get_vectorstore(), ocr))
