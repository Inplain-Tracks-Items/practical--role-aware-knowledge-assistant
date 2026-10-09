# Mock shipment register: who drives each shipment and which salesperson owns its customer.
# ICS layer: config (mock data standing in for the planner database)
# Called by: feature_shipment_tool/services/service_find_visible_shipment.py
# Calls: nothing
# Step: added in step 5 (Parallel shipment tools)

# driver_id and account_owner_id are user ids (the "sub" claim of the JWT); they are what
# the visibility rule compares against. drv-101 and sal-401 are demo users; the others are colleagues.
SHIPMENTS: dict[str, dict] = {
    "NW-1042": {"customer": "Rhine Foods", "route": "Rotterdam -> Cologne", "driver_id": "drv-101", "account_owner_id": "sal-401"},
    "NW-1077": {"customer": "Antwerp Steelworks", "route": "Antwerp -> Duisburg", "driver_id": "drv-102", "account_owner_id": "sal-401"},
    "NW-1103": {"customer": "Duisburg Retail", "route": "Duisburg -> Rotterdam", "driver_id": "drv-101", "account_owner_id": "sal-402"},
    "NW-1150": {"customer": "Benelux Pharma", "route": "Rotterdam -> Antwerp", "driver_id": "drv-103", "account_owner_id": "sal-402"},
}
