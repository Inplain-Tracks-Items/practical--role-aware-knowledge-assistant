# Extracts the text layer of every page of a PDF and flags the pages that have none (scanned pages).
# ICS layer: service
# CRD component: be.service_extract_pages
# Called by: feature_ingest/handlers/handle_ingest_documents.py
# Calls: PyMuPDF (text extraction)
# Step: added in step 2 (Ingest tagged chunks)

import asyncio  # PDF parsing is blocking; it runs in a worker thread
from pathlib import Path  # the PDF path

import pymupdf  # PyMuPDF: reads PDF pages

from app.features.feature_ingest.schemas.ingest_schemas import PageText  # one page of text

# A page with fewer characters than this is treated as scanned: real text pages have far more,
# and a scanned page can still carry a few stray characters (a page number, a stamp).
MIN_TEXT_CHARS = 20


def _extract(path: Path) -> list[PageText]:
    """Read every page; pages without a usable text layer get needs_ocr=True and empty text."""
    pages = []
    with pymupdf.open(path) as document:
        for index, page in enumerate(document):
            text = page.get_text().strip()
            needs_ocr = len(text) < MIN_TEXT_CHARS
            # Page numbers are 1-based because that is how people cite pages.
            pages.append(PageText(source_file=path.name, page=index + 1, text="" if needs_ocr else text, needs_ocr=needs_ocr))
    return pages


async def service_extract_pages(path: Path) -> list[PageText]:
    """Return one PageText per page of the PDF at path."""
    return await asyncio.to_thread(_extract, path)
