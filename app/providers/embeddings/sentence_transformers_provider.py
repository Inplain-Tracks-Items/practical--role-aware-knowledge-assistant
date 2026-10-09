# Embeds text locally with a sentence-transformers model (default BAAI/bge-small-en-v1.5): free, CPU, no API key.
# ICS layer: provider
# CRD component: be.SentenceTransformersProvider.embed_documents
# Called by: core/dependencies.py (EMBEDDING_PROVIDER=sentence-transformers), ingest and chat services
# Calls: sentence-transformers (model download on first use, then local inference)
# Step: added in step 2 (Ingest tagged chunks)

import asyncio  # model inference is CPU-bound and blocking, so it runs in a worker thread

# bge models search better when the query (never the passage) carries this instruction.
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


class SentenceTransformersProvider:
    """Local embedding model, loaded once per process by core/dependencies.py."""

    def __init__(self, model_name: str) -> None:
        """Load the model.

        model_name: a Hugging Face model id; downloaded once (~130 MB for bge-small) and cached.
        """
        # Imported here, not at the top of the file: loading torch takes seconds, and tests
        # that use the hashing provider should never pay for it.
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model_name)

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed passages as they are; vectors are normalised so cosine distance works directly."""
        # to_thread keeps the event loop free while the CPU does the matrix work.
        vectors = await asyncio.to_thread(self._model.encode, texts, normalize_embeddings=True)
        # Chroma expects plain Python lists, not numpy arrays.
        return [vector.tolist() for vector in vectors]

    async def embed_query(self, text: str) -> list[float]:
        """Embed a search query with the bge instruction prefix."""
        vector = await asyncio.to_thread(self._model.encode, QUERY_PREFIX + text, normalize_embeddings=True)
        return vector.tolist()
