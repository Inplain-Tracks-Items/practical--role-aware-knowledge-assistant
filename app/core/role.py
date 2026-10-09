# The closed list of Northwind Logistics job roles a user can have and a document can be written for.
# ICS layer: config
# Called by: feature_auth (token claims), feature_ingest (document audience), feature_chat (retrieval filter)
# Calls: nothing
# Step: added in step 1 (Authenticated WebSocket)

from typing import Literal  # Literal turns the role names into a type Pydantic can validate against

# Every role in the company. A token with any other role is rejected at auth time,
# so the rest of the system can trust that a role is always one of these five.
Role = Literal["driver", "dispatcher", "safety", "sales", "leadership"]
