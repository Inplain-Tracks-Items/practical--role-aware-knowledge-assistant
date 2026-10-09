# Turns a user's role and clearance into the vector-store filter that decides which chunks they may see.
# ICS layer: util (pure)
# CRD component: be.util_build_access_filter
# Called by: feature_chat/services/service_retrieve_chunks.py
# Calls: nothing (pure function)
# Step: added in step 3 (Access-aware retrieval)

from typing import Any  # filter values are bools and dicts

from app.core.clearance_ranks import CLEARANCE_RANKS  # clearance name -> number stored on every chunk
from app.core.token_claims import TokenClaims  # the verified user


def util_build_access_filter(user: TokenClaims) -> dict[str, Any]:
    """Return the Chroma where-filter for user.

    The rule from step 2, written as a query:
    "the user's role is in the chunk's audience" AND "the chunk's clearance rank <= the user's".
    Example for the driver (internal = 1):
        {"$and": [{"aud_driver": True}, {"clearance_rank": {"$lte": 1}}]}
    Both values come from the verified token, never from the user's message, so a question
    cannot widen its own access.
    """
    return {
        "$and": [
            # Role check: the chunk was written for this role (flag set at ingestion).
            {f"aud_{user.role}": True},
            # Clearance check: the chunk is not more sensitive than the user may read.
            {"clearance_rank": {"$lte": CLEARANCE_RANKS[user.clearance]}},
        ]
    }
