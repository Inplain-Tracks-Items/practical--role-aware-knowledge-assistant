# The five Northwind demo users, one per role, used to mint test tokens.
# ICS layer: config
# Called by: feature_auth/handlers/handle_mint_demo_tokens.py
# Calls: nothing
# Step: added in step 1 (Authenticated WebSocket)

from app.core.token_claims import TokenClaims  # each demo user is a ready-made, validated claim set

# One user per role, with the clearance that role normally has. The pairs matter later:
# the driver (internal) and the leader (confidential) ask the same question in step 3
# and must get different passages back.
DEMO_USERS: list[TokenClaims] = [
    TokenClaims(sub="drv-101", email="dana.driver@northwind.example", name="Dana Okafor", role="driver", clearance="internal"),
    TokenClaims(sub="dsp-201", email="sam.dispatch@northwind.example", name="Sam Lindqvist", role="dispatcher", clearance="internal"),
    TokenClaims(sub="saf-301", email="rio.safety@northwind.example", name="Rio Tanaka", role="safety", clearance="confidential"),
    TokenClaims(sub="sal-401", email="ana.sales@northwind.example", name="Ana Moreau", role="sales", clearance="internal"),
    TokenClaims(sub="led-501", email="lee.lead@northwind.example", name="Lee Haddad", role="leadership", clearance="confidential"),
]
