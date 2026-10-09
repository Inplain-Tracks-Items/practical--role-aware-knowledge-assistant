# App-wide settings, read once from environment variables / .env. Every other file reads config from here.
# ICS layer: config
# Called by: core/dependencies.py, feature_auth (JWT secret), feature_chat handler, feature_ingest and feature_sample_docs CLIs
# Calls: pydantic-settings (reads the environment)
# Step: added in step 1 (Authenticated WebSocket); changed in step 2: ingestion settings (docs, embeddings, Chroma, chunking, OCR)

from functools import lru_cache  # caches get_settings() so .env is parsed once per process

from pydantic_settings import BaseSettings, SettingsConfigDict  # typed settings loaded from env


class Settings(BaseSettings):
    """All configuration of the backend.

    Every field maps to an upper-case environment variable (jwt_secret -> JWT_SECRET).
    Fields without a default are required: the app refuses to start without them,
    which is better than failing on the first request.
    """

    # Read .env from the working directory; ignore variables this class does not declare.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Secret that signs and verifies every JWT; the token minting CLI and the server must share it.
    jwt_secret: str
    # HS256 = one shared secret signs and verifies; enough for a single backend.
    jwt_algorithm: str = "HS256"
    # How long a minted demo token stays valid.
    jwt_ttl_minutes: int = 7 * 24 * 60

    # Which LLM answers: "fake" works offline with no key (later steps add "openai" and "gemini").
    llm_provider: str = "fake"

    # Step 2 — ingestion.
    # Markdown sources of the Northwind documents and the folder the PDFs are rendered into.
    docs_src_dir: str = "./docs_src"
    docs_dir: str = "./docs"
    # "sentence-transformers" (real, local model) or "hashing" (offline word hashing for tests/demos).
    embedding_provider: str = "sentence-transformers"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    # Where Chroma keeps its files and which collection holds the chunks.
    chroma_path: str = "./chroma_data"
    chroma_collection: str = "northwind_docs"
    # Chunking: words per chunk and words shared with the previous chunk (see STEP-2.md).
    chunk_size_words: int = 120
    chunk_overlap_words: int = 30
    # EasyOCR language codes for scanned pages, comma-separated.
    ocr_languages: str = "en"


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide Settings, built on the first call and reused afterwards."""
    return Settings()
