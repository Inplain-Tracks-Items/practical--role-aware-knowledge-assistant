# Lists the PDF files waiting to be ingested.
# ICS layer: service
# CRD component: be.service_list_pdfs
# Called by: feature_ingest/handlers/handle_ingest_documents.py
# Calls: the file system
# Step: added in step 2 (Ingest tagged chunks)

import asyncio  # directory listing is blocking I/O; it runs in a worker thread
from pathlib import Path  # folder and file paths


async def service_list_pdfs(docs_dir: Path) -> list[Path]:
    """Return every *.pdf directly inside docs_dir, sorted by name so runs are reproducible.

    Returns an empty list when the folder does not exist yet (sample docs not built).
    """
    if not docs_dir.exists():
        return []
    return await asyncio.to_thread(lambda: sorted(docs_dir.glob("*.pdf")))
