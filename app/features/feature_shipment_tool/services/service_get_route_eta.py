# Fetches a shipment's ETA from the (mocked) route planner and flags delays the way the dispatch playbook does.
# ICS layer: service
# CRD component: be.service_get_route_eta
# Called by: feature_shipment_tool/tool_get_shipment_overview.py (concurrently with the status and SLA services)
# Calls: mock route-planning API (configs/tracking_data.py, with simulated latency)
# Step: added in step 5 (Parallel shipment tools)

import asyncio  # asyncio.sleep simulates network latency
from datetime import datetime  # "HH:MM" -> minutes

from app.features.feature_shipment_tool.configs.tracking_data import MOCK_LATENCY_SECONDS, TRACKING_DATA  # mock API


def _minutes(hhmm: str) -> int:
    """Minutes since midnight of an "HH:MM" time."""
    t = datetime.strptime(hhmm, "%H:%M")
    return t.hour * 60 + t.minute


async def service_get_route_eta(shipment_id: str) -> dict:
    """Return {"eta", "window_end", "minutes_late", "flag"}.

    flag follows the dispatch playbook: "red" when more than 90 minutes behind the window,
    "amber" when more than 30, else "on_time".
    """
    await asyncio.sleep(MOCK_LATENCY_SECONDS)
    data = TRACKING_DATA[shipment_id]
    # Negative lateness means early; it is reported as 0 so the flag logic stays simple.
    late = max(0, _minutes(data["eta"]) - _minutes(data["window_end"]))
    flag = "red" if late > 90 else "amber" if late > 30 else "on_time"
    return {"eta": data["eta"], "window_end": data["window_end"], "minutes_late": late, "flag": flag}
