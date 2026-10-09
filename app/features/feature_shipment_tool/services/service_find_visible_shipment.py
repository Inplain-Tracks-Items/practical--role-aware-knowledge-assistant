# Looks up a shipment only if the user may see it: the access rule of the shipment tool, applied in the lookup itself.
# ICS layer: service
# CRD component: be.service_find_visible_shipment
# Called by: feature_shipment_tool/tool_get_shipment_overview.py
# Calls: the shipment register (mock data in configs/shipments.py)
# Step: added in step 5 (Parallel shipment tools)

from app.core.token_claims import TokenClaims  # the verified user
from app.features.feature_shipment_tool.configs.shipments import SHIPMENTS  # mock planner database

# Roles that supervise operations see every shipment.
ALL_SHIPMENTS_ROLES = {"dispatcher", "safety", "leadership"}


async def service_find_visible_shipment(shipment_id: str, user: TokenClaims) -> dict | None:
    """Return the shipment record, or None when it does not exist OR the user may not see it.

    Rule: dispatcher, safety and leadership see all shipments; a driver sees the shipments
    they drive; sales sees the shipments of the customers they own.
    Returning the same None for "missing" and "forbidden" means the answer never reveals
    that a shipment the user may not see exists.
    """
    # Normalise "nw-1042 " to "NW-1042", the form ids are stored in.
    shipment = SHIPMENTS.get(shipment_id.strip().upper())
    if shipment is None:
        return None
    if user.role in ALL_SHIPMENTS_ROLES:
        return shipment
    # Drivers: only their own trips. Sales: only their own accounts. Nobody else.
    if user.role == "driver" and shipment["driver_id"] == user.sub:
        return shipment
    if user.role == "sales" and shipment["account_owner_id"] == user.sub:
        return shipment
    return None
