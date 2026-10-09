# Builds every provider once per process and hands it to routes and CLIs through FastAPI's Depends() or direct calls.
# ICS layer: config (dependency wiring)
# CRD component: be.get_llm_provider, be.get_embedder, be.get_vectorstore, be.get_ocr_provider
# Called by: feature_chat/router.py (Depends), feature_ingest/cli.py, tests (dependency_overrides)
# Calls: core/config.py, providers/*
# Step: added in step 1 (Authenticated WebSocket); changed in step 2: embedder, vector store and OCR factories; changed in step 4: OpenAI and Gemini

from functools import lru_cache  # one instance per process: a provider is never rebuilt per request

from app.core.config import get_settings  # decides which concrete providers to build
from app.providers.embeddings.base import EmbeddingProvider  # interfaces the features depend on
from app.providers.llm.base import LLMProvider
from app.providers.ocr.base import OcrProvider
from app.providers.vectorstore.base import VectorStore
from app.providers.embeddings.hashing_provider import HashingProvider  # concrete providers, only referenced here
from app.providers.embeddings.sentence_transformers_provider import SentenceTransformersProvider
from app.providers.llm.fake_provider import FakeProvider
from app.providers.llm.gemini_provider import GeminiProvider
from app.providers.llm.openai_provider import OpenAIProvider
from app.providers.ocr.easyocr_provider import EasyOcrProvider
from app.providers.vectorstore.chroma_store import ChromaStore


@lru_cache
def get_llm_provider() -> LLMProvider:
    """Return the shared LLM provider chosen by LLM_PROVIDER.

    Features only ever see the LLMProvider interface, so switching providers is a
    config change, never a code change in feature_chat.
    Raises ValueError for an unknown provider name or a missing API key, at the first request that needs it.
    """
    settings = get_settings()
    # Offline echo: the default, so a fresh clone runs without any key.
    if settings.llm_provider == "fake":
        return FakeProvider()
    # Real providers need their key; failing here gives a clear message instead of a 401 mid-stream.
    if settings.llm_provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("LLM_PROVIDER=openai needs OPENAI_API_KEY")
        return OpenAIProvider(api_key=settings.openai_api_key, model=settings.openai_model)
    if settings.llm_provider == "gemini":
        if not settings.gemini_api_key:
            raise ValueError("LLM_PROVIDER=gemini needs GEMINI_API_KEY")
        return GeminiProvider(api_key=settings.gemini_api_key, model=settings.gemini_model)
    raise ValueError(f"unknown LLM_PROVIDER '{settings.llm_provider}'")


@lru_cache
def get_embedder() -> EmbeddingProvider:
    """Return the shared embedding provider chosen by EMBEDDING_PROVIDER.

    The same instance embeds documents at ingestion and queries at chat time; both sides
    must use the same model, or the vectors would not be comparable.
    """
    settings = get_settings()
    # "hashing" needs no download: handy for tests and a first run.
    if settings.embedding_provider == "hashing":
        return HashingProvider()
    if settings.embedding_provider == "sentence-transformers":
        return SentenceTransformersProvider(settings.embedding_model)
    raise ValueError(f"unknown EMBEDDING_PROVIDER '{settings.embedding_provider}'")


@lru_cache
def get_vectorstore() -> VectorStore:
    """Return the shared Chroma collection handle, opened once instead of per request."""
    settings = get_settings()
    return ChromaStore(path=settings.chroma_path, collection_name=settings.chroma_collection)


@lru_cache
def get_ocr_provider() -> OcrProvider:
    """Return the shared OCR reader; only ingestion needs it, so the chat server never builds it."""
    settings = get_settings()
    # "en,de" in the env becomes ["en", "de"] for EasyOCR.
    return EasyOcrProvider([code.strip() for code in settings.ocr_languages.split(",")])
