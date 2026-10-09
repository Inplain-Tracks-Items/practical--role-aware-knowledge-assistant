# Reads one UTF-8 text file without blocking the event loop.
# ICS layer: service
# CRD component: be.service_read_text_file
# Called by: feature_sample_docs/handlers/handle_build_sample_docs.py
# Calls: the file system
# Step: added in step 2 (Ingest tagged chunks)

import asyncio  # file reads are blocking I/O; they run in a worker thread
from pathlib import Path  # file path type


async def service_read_text_file(path: Path) -> str:
    """Return the content of path. Raises FileNotFoundError when the source is missing."""
    return await asyncio.to_thread(path.read_text, encoding="utf-8")
