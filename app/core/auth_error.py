# The single error type for "this token cannot be trusted", whatever the low-level reason.
# ICS layer: config (shared error type)
# Called by: core/verify_jwt.py (raises it), feature_chat/handlers/handle_chat_socket.py (catches it)
# Calls: nothing
# Step: added in step 1 (Authenticated WebSocket)


class AuthError(Exception):
    """Raised for an expired, badly signed, malformed or incomplete token.

    The message is safe to send to the client: it says what is wrong, never the secret or the payload.
    """
