# Mints a token for every demo user so a learner can log in as each role.
# ICS layer: handler
# CRD component: be.handle_mint_demo_tokens
# Called by: feature_auth/cli.py
# Calls: be.service_mint_token
# Step: added in step 1 (Authenticated WebSocket)

from app.core.config import Settings  # passed through to the signing service
from app.features.feature_auth.configs.demo_users import DEMO_USERS  # who gets a token
from app.features.feature_auth.services.service_mint_token import service_mint_token  # signs one token


def handle_mint_demo_tokens(settings: Settings) -> list[dict]:
    """Return one {"user": TokenClaims, "token": str} entry per demo user, in DEMO_USERS order."""
    # One signing call per user; the handler only loops and pairs, the signing rule lives in the service.
    return [{"user": user, "token": service_mint_token(user, settings)} for user in DEMO_USERS]
