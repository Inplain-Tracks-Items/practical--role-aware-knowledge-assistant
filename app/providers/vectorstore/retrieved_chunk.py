# One search result from the vector store: the chunk text plus what is needed to cite it.
# ICS layer: provider (shared schema of the vector store interface)
# Called by: providers/vectorstore/chroma_store.py (builds it), feature_chat services (read it)
# Calls: Pydantic validation
# Step: added in step 3 (Access-aware retrieval)

from pydantic import BaseModel  # typed result instead of Chroma's nested lists


class RetrievedChunk(BaseModel):
    """A chunk returned by a similarity query.

    text: the chunk content that will be given to the LLM as context.
    source_file, page: the citation shown to the user, e.g. driver_safety_manual.pdf p.1.
    distance: cosine distance to the query (0 = identical); lower is more relevant.
    """

    text: str
    source_file: str
    page: int
    distance: float
