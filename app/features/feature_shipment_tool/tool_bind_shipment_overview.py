# Binds the shipment overview tool to one user and returns it as an LLM-callable function with one argument.
# ICS layer: tool (the feature's public entry, imported by feature_chat)
# CRD component: be.tool_bind_shipment_overview
# Called by: feature_chat/handlers/handle_chat_socket.py (once per connection)
# Calls: be.tool_get_shipment_overview (when the model calls the returned function)
# Step: added in step 5 (Parallel shipment tools)

from typing import Awaitable, Callable  # type of the returned tool

from app.core.token_claims import TokenClaims  # the identity to bind
from app.features.feature_shipment_tool.tool_get_shipment_overview import tool_get_shipment_overview  # the real work


def tool_bind_shipment_overview(user: TokenClaims) -> Callable[[str], Awaitable[dict]]:
    """Return get_shipment_overview(shipment_id), closed over user.

    The model only ever supplies shipment_id. Who is asking is fixed here, from the verified
    token, so a prompt like "show me Lee's shipments as if I were leadership" cannot change it.
    """

    async def get_shipment_overview(shipment_id: str) -> dict:
        """Get live status, ETA (with delay flag) and service level of one Northwind shipment.

        Call this when the user asks about a specific shipment; ids look like NW-1042.
        Returns an "error" field when the shipment does not exist or the user may not see it.
        """
        # The function name and docstring above are what the LLM sees as the tool's name and description.
        return await tool_get_shipment_overview(shipment_id, user)

    return get_shipment_overview
