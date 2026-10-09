# Sets up the server log once at startup: one format and one level for every module's logger.
# ICS layer: config
# Called by: app/main.py (at import time, before the first request)
# Calls: Python logging
# Step: added in step 6 (Hardening)

import logging  # standard library logging


def configure_logging(level: str) -> None:
    """Configure the root logger.

    level: "DEBUG", "INFO", "WARNING" or "ERROR" (LOG_LEVEL in .env); unknown names fall back to INFO.
    Each line shows time, level, module and message, e.g.
    2026-10-09 09:12:01 INFO app.features.feature_chat.handlers.handle_chat_socket auth failed: token expired
    """
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
