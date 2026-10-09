# The shipment overview: visibility check first, then status, ETA and SLA fetched concurrently.
# ICS layer: tool
# CRD component: be.tool_get_shipment_overview
# Called by: feature_shipment_tool/tool_bind_shipment_overview.py (the closure the LLM calls)
# Calls: be.service_find_visible_shipment, be.service_get_shipment_status, be.service_get_route_eta, be.service_get_customer_sla
# Step: added in step 5 (Parallel shipment tools)

import asyncio  # asyncio.gather runs the three lookups at the same time

from app.core.token_claims import TokenClaims  # the verified user the tool is bound to
from app.features.feature_shipment_tool.services.service_find_visible_shipment import service_find_visible_shipment  # access rule
from app.features.feature_shipment_tool.services.service_get_customer_sla import service_get_customer_sla  # contracts API
from app.features.feature_shipment_tool.services.service_get_route_eta import service_get_route_eta  # route planner API
from app.features.feature_shipment_tool.services.service_get_shipment_status import service_get_shipment_status  # telematics API

# One message for "does not exist" and "not yours", so the model cannot learn which one it was.
NOT_VISIBLE = "shipment not found or not visible to this user"


async def tool_get_shipment_overview(shipment_id: str, user: TokenClaims) -> dict:
    """Return the overview of one shipment for user, or {"error": NOT_VISIBLE}.

    shipment_id: e.g. "NW-1042", as the model extracted it from the question.
    user: the connection's verified identity (bound by tool_bind_shipment_overview, never chosen by the model).
    """
    # Step 1: access check BEFORE any data call, so nothing about a forbidden shipment is fetched.
    shipment = await service_find_visible_shipment(shipment_id, user)
    if shipment is None:
        return {"error": NOT_VISIBLE}
    sid = shipment_id.strip().upper()
    # Step 2: three independent API calls run concurrently: total time ~= the slowest call
    # (about 1 s), not the sum (about 3 s). gather returns results in argument order.
    status, eta, sla = await asyncio.gather(
        service_get_shipment_status(sid),
        service_get_route_eta(sid),
        service_get_customer_sla(sid),
    )
    # Step 3: one flat answer the model can read and quote.
    return {"shipment_id": sid, "customer": shipment["customer"], "route": shipment["route"], "status": status, "eta": eta, "sla": sla}
