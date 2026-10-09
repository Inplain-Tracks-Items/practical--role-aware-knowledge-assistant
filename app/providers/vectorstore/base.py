# The interface every vector store implements; features depend on this, never on Chroma directly.
# ICS layer: provider (interface)
# Called by: feature_ingest services, core/dependencies.py
# Calls: nothing (a Protocol has no behaviour)
# Step: added in step 2 (Ingest tagged chunks)

from typing import Any, Protocol  # structural interface and the loose metadata value type


class VectorStore(Protocol):
    """Stores text chunks with their vectors and metadata."""

    async def upsert(self, ids: list[str], texts: list[str], embeddings: list[list[float]], metadatas: list[dict[str, Any]]) -> None:
        """Insert or replace chunks by id; all four lists are parallel (same length, same order)."""
        ...

    async def count(self) -> int:
        """Number of chunks currently stored."""
        ...
