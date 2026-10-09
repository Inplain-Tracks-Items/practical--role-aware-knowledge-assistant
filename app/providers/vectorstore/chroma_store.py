# Chroma-backed VectorStore: one persistent collection on local disk, no server needed.
# ICS layer: provider
# CRD component: be.ChromaStore.upsert
# Called by: core/dependencies.py, feature_ingest/services/service_store_chunks.py
# Calls: chromadb (local persistent client)
# Step: added in step 2 (Ingest tagged chunks)

import asyncio  # Chroma's client is synchronous; calls run in a worker thread
from typing import Any  # metadata values are str / int / bool

import chromadb  # embedded vector database


class ChromaStore:
    """A single Chroma collection opened once per process."""

    def __init__(self, path: str, collection_name: str) -> None:
        """Open (or create) the collection.

        path: folder where Chroma keeps its files, e.g. ./chroma_data.
        collection_name: one collection holds every Northwind chunk.
        """
        # PersistentClient keeps data on disk, so ingestion runs once and the server reuses it.
        self._client = chromadb.PersistentClient(path=path)
        # Cosine distance matches the normalised vectors both embedding providers produce.
        self._collection = self._client.get_or_create_collection(name=collection_name, metadata={"hnsw:space": "cosine"})

    async def upsert(self, ids: list[str], texts: list[str], embeddings: list[list[float]], metadatas: list[dict[str, Any]]) -> None:
        """Insert or replace chunks; re-running ingestion with the same ids overwrites instead of duplicating."""
        await asyncio.to_thread(self._collection.upsert, ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)

    async def count(self) -> int:
        """Number of stored chunks (used by the ingest summary and tests)."""
        return await asyncio.to_thread(self._collection.count)
