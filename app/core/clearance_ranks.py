# Maps each clearance level to a number so "may this user read this document" becomes rank <= rank.
# ICS layer: config
# Called by: feature_ingest (stores the rank on every chunk), feature_chat (filters by rank in the query)
# Calls: nothing
# Step: added in step 1 (Authenticated WebSocket)

from app.core.clearance import Clearance  # the level names this table must cover

# A user with clearance "internal" (rank 1) may read "public" (0) and "internal" (1)
# chunks but not "confidential" (2). Storing ranks as integers lets the vector store
# compare them with $lte inside the query instead of in Python afterwards.
CLEARANCE_RANKS: dict[Clearance, int] = {
    "public": 0,
    "internal": 1,
    "confidential": 2,
}
