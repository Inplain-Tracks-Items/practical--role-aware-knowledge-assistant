# Signs one JWT for one user: the counterpart of core/verify_jwt.py.
# ICS layer: service
# CRD component: be.service_mint_token
# Called by: feature_auth/handlers/handle_mint_demo_tokens.py, tests
# Calls: PyJWT (signing)
# Step: added in step 1 (Authenticated WebSocket)

import time  # iat / exp are Unix timestamps in seconds

import jwt  # PyJWT: signs the payload with the shared secret

from app.core.config import Settings  # secret, algorithm and token lifetime
from app.core.token_claims import TokenClaims  # the claims to put in the token


def service_mint_token(claims: TokenClaims, settings: Settings, ttl_seconds: int | None = None) -> str:
    """Return a signed JWT for claims.

    claims: who the token is for (sub, email, name, role, clearance).
    settings: jwt_secret, jwt_algorithm and the default lifetime jwt_ttl_minutes.
    ttl_seconds: overrides the lifetime; tests pass a negative value to mint an already-expired token.
    """
    # iat = issued now; exp = when verify_jwt starts rejecting the token.
    now = int(time.time())
    lifetime = ttl_seconds if ttl_seconds is not None else settings.jwt_ttl_minutes * 60
    # The payload is the claims plus the two time fields PyJWT checks automatically.
    payload = {**claims.model_dump(), "iat": now, "exp": now + lifetime}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
