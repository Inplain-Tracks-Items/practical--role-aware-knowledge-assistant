# Verifies a JWT and returns its trusted claims; the only place in the system that decides whether a token is valid.
# ICS layer: service (shared, lives in core/ because more than one feature needs it)
# CRD component: be.verify_jwt
# Called by: feature_chat/handlers/handle_chat_socket.py (auth handshake)
# Calls: PyJWT (signature + expiry check), TokenClaims (claim validation)
# Step: added in step 1 (Authenticated WebSocket)

import jwt  # PyJWT: checks the signature and the exp claim
from pydantic import ValidationError  # raised when a claim is missing or has an unknown value

from app.core.auth_error import AuthError  # the one error callers need to handle
from app.core.config import Settings  # carries the secret and algorithm
from app.core.token_claims import TokenClaims  # the shape a valid token must have


def verify_jwt(token: str, settings: Settings) -> TokenClaims:
    """Check token and return its claims.

    token: the raw JWT string the client sent in its auth message.
    settings: provides jwt_secret and jwt_algorithm; passed in so tests can use their own secret.
    Returns the validated TokenClaims.
    Raises AuthError("token expired" | "invalid token" | "token claims are incomplete or unknown").
    """
    # Step 1: verify signature and expiry. algorithms=[...] pins the algorithm so a token
    # cannot pick a weaker one (for example "none") for itself.
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError:
        # Expired tokens get their own message so the client knows to fetch a new one.
        raise AuthError("token expired")
    except jwt.InvalidTokenError:
        # Wrong secret, tampered payload, garbage string: all the same to the caller.
        raise AuthError("invalid token")

    # Step 2: check the claims. A correctly signed token can still carry an unknown role;
    # TokenClaims rejects it so retrieval never sees a role it has no rule for.
    try:
        return TokenClaims(**payload)
    except ValidationError:
        raise AuthError("token claims are incomplete or unknown")
