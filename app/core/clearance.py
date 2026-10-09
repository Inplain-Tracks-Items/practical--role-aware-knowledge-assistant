# The closed list of clearance levels: how sensitive a document is, and how sensitive a user may read.
# ICS layer: config
# Called by: feature_auth (token claims), feature_ingest (document clearance), core/clearance_ranks.py
# Calls: nothing
# Step: added in step 1 (Authenticated WebSocket)

from typing import Literal  # Literal turns the level names into a type Pydantic can validate against

# Ordered from least to most sensitive; the order itself lives in clearance_ranks.py.
Clearance = Literal["public", "internal", "confidential"]
