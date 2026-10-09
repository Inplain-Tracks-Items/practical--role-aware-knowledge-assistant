# Finds the chunks most relevant to a question among the chunks this user is allowed to read.
# ICS layer: service
# CRD component: be.service_retrieve_chunks
# Called by: feature_chat/handlers/handle_chat_socket.py
# Calls: be.util_build_access_filter, be.SentenceTransformersProvider.embed_query, be.ChromaStore.query
# Step: added in step 3 (Access-aware retrieval)

from app.core.token_claims import TokenClaims  # the verified user from the auth handshake
from app.features.feature_chat.utils.util_build_access_filter import util_build_access_filter  # role + clearance -> filter
from app.providers.embeddings.base import EmbeddingProvider  # interfaces only; concrete providers are injected
from app.providers.vectorstore.base import VectorStore
from app.providers.vectorstore.retrieved_chunk import RetrievedChunk  # result type


async def service_retrieve_chunks(
    question: str,
    user: TokenClaims,
    embedder: EmbeddingProvider,
    store: VectorStore,
    top_k: int,
) -> list[RetrievedChunk]:
    """Return up to top_k chunks for question, filtered by user's access inside the query.

    question: the user's message.
    user: role and clearance decide the filter.
    embedder: must be the same model ingestion used, so query and chunk vectors are comparable.
    store: the shared vector store.
    top_k: how many chunks to return at most (RETRIEVAL_TOP_K).
    """
    # Step 1: the access filter, built from the token only.
    where = util_build_access_filter(user)
    # Step 2: the question as a vector.
    embedding = await embedder.embed_query(question)
    # Step 3: similarity search restricted to allowed chunks. There is no filtering in
    # Python afterwards: forbidden chunks are never returned, so they cannot leak.
    return await store.query(embedding, top_k, where)
