# Turns chunk texts into vectors with the injected embedding provider.
# ICS layer: service
# CRD component: be.service_embed_texts
# Called by: feature_ingest/handlers/handle_ingest_documents.py
# Calls: be.SentenceTransformersProvider.embed_documents (through the EmbeddingProvider interface)
# Step: added in step 2 (Ingest tagged chunks)

from app.providers.embeddings.base import EmbeddingProvider  # interface only


async def service_embed_texts(texts: list[str], embedder: EmbeddingProvider) -> list[list[float]]:
    """Return one vector per text, same order.

    texts: all chunk texts of the run, embedded in one batch (much faster than one by one).
    embedder: the shared provider; must be the same model the chat side uses for queries.
    """
    # An empty batch would make some models raise; nothing to embed means no vectors.
    if not texts:
        return []
    return await embedder.embed_documents(texts)
