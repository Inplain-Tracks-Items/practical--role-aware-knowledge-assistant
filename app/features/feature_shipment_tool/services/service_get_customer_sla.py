# Fetches the service level a shipment was sold with from the (mocked) contracts API.
# ICS layer: service
# CRD component: be.service_get_customer_sla
# Called by: feature_shipment_tool/tool_get_shipment_overview.py (concurrently with the status and ETA services)
# Calls: mock contracts API (configs/tracking_data.py, with simulated latency)
# Step: added in step 5 (Parallel shipment tools)

import asyncio  # asyncio.sleep simulates network latency

from app.features.feature_shipment_tool.configs.tracking_data import MOCK_LATENCY_SECONDS, SLA_TIERS, TRACKING_DATA  # mock API


async def service_get_customer_sla(shipment_id: str) -> dict:
    """Return {"tier", "window_hours", "credit_percent_if_missed"} for the shipment's contract."""
    await asyncio.sleep(MOCK_LATENCY_SECONDS)
    tier = TRACKING_DATA[shipment_id]["tier"]
    # The tier's terms come from the customer SLA guide (step 2 documents).
    return {"tier": tier, "window_hours": SLA_TIERS[tier]["window_hours"], "credit_percent_if_missed": SLA_TIERS[tier]["credit_percent"]}
