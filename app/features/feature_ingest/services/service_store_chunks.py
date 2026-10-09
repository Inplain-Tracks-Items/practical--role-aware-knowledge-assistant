# Writes chunks, their vectors and their access metadata into the vector store.
# ICS layer: service
# CRD component: be.service_store_chunks
# Called by: feature_ingest/handlers/handle_ingest_documents.py
# Calls: be.ChromaStore.upsert (through the VectorStore interface)
# Step: added in step 2 (Ingest tagged chunks)

from app.features.feature_ingest.schemas.ingest_schemas import ChunkRecord  # chunk + metadata
from app.providers.vectorstore.base import VectorStore  # interface only


async def service_store_chunks(records: list[ChunkRecord], embeddings: list[list[float]], store: VectorStore) -> int:
    """Upsert records with their embeddings and return how many were written.

    records and embeddings are parallel lists (embeddings[i] belongs to records[i]).
    Raises ValueError when the lengths differ, which would attach vectors to the wrong text.
    """
    if len(records) != len(embeddings):
        raise ValueError("every record needs exactly one embedding")
    if not records:
        return 0
    # The store receives four parallel lists: ids, texts, vectors, metadata.
    await store.upsert(
        ids=[r.id for r in records],
        texts=[r.text for r in records],
        embeddings=embeddings,
        metadatas=[r.metadata for r in records],
    )
    return len(records)
