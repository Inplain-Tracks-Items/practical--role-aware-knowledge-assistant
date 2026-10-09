# Mock live data per shipment: telematics status, route timing and the contracted service tier.
# ICS layer: config (mock data standing in for three operational APIs)
# Called by: the three feature_shipment_tool services
# Calls: nothing
# Step: added in step 5 (Parallel shipment tools)

# Times are "HH:MM" on today's date; the ETA service compares eta with window_end.
TRACKING_DATA: dict[str, dict] = {
    "NW-1042": {"status": "in_transit", "last_position": "A3 near Arnhem", "eta": "14:40", "window_end": "14:30", "tier": "Priority"},
    "NW-1077": {"status": "delayed", "last_position": "A40 near Venlo", "eta": "17:50", "window_end": "16:00", "tier": "Critical"},
    "NW-1103": {"status": "loading", "last_position": "Duisburg depot dock 4", "eta": "18:10", "window_end": "20:00", "tier": "Standard"},
    "NW-1150": {"status": "delivered", "last_position": "Antwerp, customer site", "eta": "09:55", "window_end": "10:00", "tier": "Critical"},
}

# Service tiers from customer_sla_guide.pdf: delivery window length and the credit for a missed window.
SLA_TIERS: dict[str, dict] = {
    "Standard": {"window_hours": 4, "credit_percent": 5},
    "Priority": {"window_hours": 2, "credit_percent": 10},
    "Critical": {"window_hours": 1, "credit_percent": 20},
}

# Simulated network latency of each operational API, in seconds. Three sequential calls
# would take 3 x this; the tool runs them concurrently, so it takes about 1 x this.
MOCK_LATENCY_SECONDS = 1.0
