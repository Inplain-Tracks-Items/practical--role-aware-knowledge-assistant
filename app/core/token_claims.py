# The verified identity of a caller: the JWT claims the rest of the system is allowed to trust.
# ICS layer: config (shared schema)
# Called by: core/verify_jwt.py (builds it), feature_auth (mints it), feature_chat (reads role and clearance)
# Calls: Pydantic validation
# Step: added in step 1 (Authenticated WebSocket)

from pydantic import BaseModel  # validates the decoded token payload field by field

from app.core.clearance import Clearance  # allowed clearance names
from app.core.role import Role  # allowed role names


class TokenClaims(BaseModel):
    """Claims carried by every Northwind JWT.

    sub: stable user id, e.g. "drv-101"; tools later use it to find the user's own shipments.
    email: shown back to the client after login.
    name: display name.
    role: one of Role; decides which documents (audience) the user may read.
    clearance: one of Clearance; decides how sensitive those documents may be.
    A token with an unknown role or clearance fails validation here, so it never reaches retrieval.
    """

    sub: str
    email: str
    name: str
    role: Role
    clearance: Clearance
