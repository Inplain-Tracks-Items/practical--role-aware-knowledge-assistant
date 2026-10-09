# App-wide settings, read once from environment variables / .env. Every other file reads config from here.
# ICS layer: config
# Called by: core/dependencies.py, feature_auth (JWT secret), feature_chat handler, feature_ingest and feature_sample_docs CLIs
# Calls: pydantic-settings (reads the environment)
# Step: added in step 1 (Authenticated WebSocket); changed in step 2: ingestion settings (docs, embeddings, Chroma, chunking, OCR); changed in step 3: retrieval_top_k; changed in step 4: OpenAI and Gemini settings;
#       changed in step 6: max_message_chars, log_level

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

    # Which LLM answers: "fake" (offline echo, no key), "openai" or "gemini".
    llm_provider: str = "fake"
    # Step 4 — only the key of the selected provider is needed.
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

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

    # Step 3 — retrieval.
    # How many allowed chunks are retrieved per question; 4 paragraphs is enough context
    # for these documents without drowning the model in loosely related text.
    retrieval_top_k: int = 4

    # Step 6 — hardening.
    # Longest question accepted; longer messages get an error event instead of an answer.
    max_message_chars: int = 2000
    # Python logging level for the server log: DEBUG, INFO, WARNING, ERROR.
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide Settings, built on the first call and reused afterwards."""
    return Settings()
