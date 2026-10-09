# Writes bytes to a file, creating its folder first, without blocking the event loop.
# ICS layer: service
# CRD component: be.service_write_file
# Called by: feature_sample_docs/handlers/handle_build_sample_docs.py
# Calls: the file system
# Step: added in step 2 (Ingest tagged chunks)

import asyncio  # file writes are blocking I/O; they run in a worker thread
from pathlib import Path  # file path type


def _write(path: Path, data: bytes) -> None:
    """Create the parent folder if needed, then replace the file's content."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


async def service_write_file(path: Path, data: bytes) -> None:
    """Write data to path (overwriting it)."""
    await asyncio.to_thread(_write, path, data)
