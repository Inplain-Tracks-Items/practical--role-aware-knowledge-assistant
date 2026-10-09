# Command-line door of the auth feature: prints a JWT for every demo user.
# Run: python -m app.features.feature_auth.cli
# ICS layer: door
# CRD component: be.auth_cli
# Called by: a developer in the terminal
# Calls: be.handle_mint_demo_tokens
# Step: added in step 1 (Authenticated WebSocket)

from app.core.config import get_settings  # reads JWT_SECRET from .env
from app.features.feature_auth.handlers.handle_mint_demo_tokens import handle_mint_demo_tokens  # does the work


def main() -> None:
    """Print each demo user's role, clearance and token; never prints the secret itself."""
    # The door only delegates and prints; it holds no token logic.
    for entry in handle_mint_demo_tokens(get_settings()):
        user = entry["user"]
        print(f"# {user.name} <{user.email}>  role={user.role}  clearance={user.clearance}")
        print(entry["token"])
        print()


# Runs only when executed as a module, not when imported by tests.
if __name__ == "__main__":
    main()
