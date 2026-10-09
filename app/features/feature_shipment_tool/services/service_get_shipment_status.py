# Fetches a shipment's live status from the (mocked) telematics API.
# ICS layer: service
# CRD component: be.service_get_shipment_status
# Called by: feature_shipment_tool/tool_get_shipment_overview.py (concurrently with the ETA and SLA services)
# Calls: mock telematics API (configs/tracking_data.py, with simulated latency)
# Step: added in step 5 (Parallel shipment tools)

import asyncio  # asyncio.sleep simulates network latency without blocking the event loop

from app.features.feature_shipment_tool.configs.tracking_data import MOCK_LATENCY_SECONDS, TRACKING_DATA  # mock API


async def service_get_shipment_status(shipment_id: str) -> dict:
    """Return {"status", "last_position"} for an id the caller has already checked for visibility."""
    # A real telematics API call would await an HTTP response here; sleeping keeps the timing realistic.
    await asyncio.sleep(MOCK_LATENCY_SECONDS)
    data = TRACKING_DATA[shipment_id]
    return {"status": data["status"], "last_position": data["last_position"]}
