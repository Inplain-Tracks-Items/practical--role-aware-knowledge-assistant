# The interface every embedding provider implements: text in, vector out.
# ICS layer: provider (interface)
# Called by: feature_ingest services (documents), feature_chat services (queries, from step 3), core/dependencies.py
# Calls: nothing (a Protocol has no behaviour)
# Step: added in step 2 (Ingest tagged chunks)

from typing import Protocol  # structural interface: implementations match by shape, not inheritance


class EmbeddingProvider(Protocol):
    """Turns text into vectors whose distance reflects meaning.

    Documents and queries have separate methods because some models (bge) embed
    a search query with an instruction prefix and a passage without one.
    """

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per text, in the same order. Used at ingestion."""
        ...

    async def embed_query(self, text: str) -> list[float]:
        """Return the vector of a search query. Used at retrieval."""
        ...
