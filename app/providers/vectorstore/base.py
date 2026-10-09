# The interface every vector store implements; features depend on this, never on Chroma directly.
# ICS layer: provider (interface)
# Called by: feature_ingest services, feature_chat services (from step 3), core/dependencies.py
# Calls: nothing (a Protocol has no behaviour)
# Step: added in step 2 (Ingest tagged chunks); changed in step 3: query() with a metadata filter

from typing import Any, Protocol  # structural interface and the loose metadata value type

from app.providers.vectorstore.retrieved_chunk import RetrievedChunk  # what a query returns


class VectorStore(Protocol):
    """Stores text chunks with their vectors and metadata."""

    async def upsert(self, ids: list[str], texts: list[str], embeddings: list[list[float]], metadatas: list[dict[str, Any]]) -> None:
        """Insert or replace chunks by id; all four lists are parallel (same length, same order)."""
        ...

    async def count(self) -> int:
        """Number of chunks currently stored."""
        ...

    async def query(self, embedding: list[float], top_k: int, where: dict[str, Any]) -> list[RetrievedChunk]:
        """Return the top_k chunks closest to embedding among those matching where.

        where is applied by the store BEFORE ranking, so forbidden chunks never compete
        for the top_k places. Results are ordered from most to least relevant.
        """
        ...
