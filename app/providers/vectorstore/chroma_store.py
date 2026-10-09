# Chroma-backed VectorStore: one persistent collection on local disk, no server needed.
# ICS layer: provider
# CRD component: be.ChromaStore.upsert, be.ChromaStore.query
# Called by: core/dependencies.py, feature_ingest/services/service_store_chunks.py, feature_chat/services/service_retrieve_chunks.py
# Calls: chromadb (local persistent client)
# Step: added in step 2 (Ingest tagged chunks); changed in step 3: query() with the access filter in the where clause

import asyncio  # Chroma's client is synchronous; calls run in a worker thread
from typing import Any  # metadata values are str / int / bool

import chromadb  # embedded vector database

from app.providers.vectorstore.retrieved_chunk import RetrievedChunk  # typed query result


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

    def _query(self, embedding: list[float], top_k: int, where: dict[str, Any]) -> list[RetrievedChunk]:
        """Run the filtered similarity search and flatten Chroma's nested result lists."""
        # where is evaluated by Chroma before ranking: only chunks this user may read are
        # candidates, so the top_k places are never wasted on forbidden chunks.
        result = self._collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        # Chroma answers per query embedding; we sent one, so we read index [0] of each list.
        return [
            RetrievedChunk(text=text, source_file=meta["source_file"], page=meta["page"], distance=distance)
            for text, meta, distance in zip(result["documents"][0], result["metadatas"][0], result["distances"][0])
        ]

    async def query(self, embedding: list[float], top_k: int, where: dict[str, Any]) -> list[RetrievedChunk]:
        """Return up to top_k chunks matching where, most relevant first."""
        return await asyncio.to_thread(self._query, embedding, top_k, where)
