# Builds the metadata stored next to every chunk: citation fields plus the access tags retrieval filters on.
# ICS layer: util (pure)
# CRD component: be.util_build_chunk_metadata
# Called by: feature_ingest/handlers/handle_ingest_documents.py
# Calls: nothing (pure function)
# Step: added in step 2 (Ingest tagged chunks)

from typing import Any, get_args  # get_args lists the values of the Role Literal

from app.core.clearance_ranks import CLEARANCE_RANKS  # clearance name -> comparable number
from app.core.role import Role  # every role gets its own flag
from app.features.feature_ingest.schemas.ingest_schemas import DocumentAccess  # the document's access entry


def util_build_chunk_metadata(source_file: str, page: int, chunk_index: int, access: DocumentAccess) -> dict[str, Any]:
    """Return the metadata dict of one chunk.

    source_file, page, chunk_index: where the chunk comes from (used for citations and the chunk id).
    access: the document's audience and clearance from ACCESS_MAP.
    Example for a driver-safety chunk: {"aud_driver": True, "aud_sales": False, ..., "clearance_rank": 1}.
    """
    metadata: dict[str, Any] = {
        "source_file": source_file,
        "page": page,
        "chunk_index": chunk_index,
        # The name is kept for humans reading the store; the rank is what queries compare.
        "clearance": access.clearance,
        "clearance_rank": CLEARANCE_RANKS[access.clearance],
    }
    # One boolean per role instead of a list: every vector store can filter on
    # {"aud_driver": True}, while list-membership filters differ between stores.
    for role in get_args(Role):
        metadata[f"aud_{role}"] = role in access.audience
    return metadata
