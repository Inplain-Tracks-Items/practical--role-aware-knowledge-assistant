# Reads the text of one scanned PDF page: renders the page to an image, then hands it to the OCR provider.
# ICS layer: service
# CRD component: be.service_ocr_page
# Called by: feature_ingest/handlers/handle_ingest_documents.py (only for pages with needs_ocr=True)
# Calls: PyMuPDF (page rendering), be.EasyOcrProvider.read_text (through the OcrProvider interface)
# Step: added in step 2 (Ingest tagged chunks)

import asyncio  # rendering is blocking; it runs in a worker thread
from pathlib import Path  # the PDF path

import pymupdf  # PyMuPDF: renders a page to PNG

from app.providers.ocr.base import OcrProvider  # interface only; EasyOCR is injected

# Higher than the 150 dpi scan itself is pointless; 200 gives OCR crisp letters.
OCR_DPI = 200


def _render_page_png(path: Path, page_number: int) -> bytes:
    """Return the PNG bytes of the 1-based page_number of the PDF at path."""
    with pymupdf.open(path) as document:
        return document[page_number - 1].get_pixmap(dpi=OCR_DPI).tobytes("png")


async def service_ocr_page(path: Path, page_number: int, ocr: OcrProvider) -> str:
    """Return the OCR text of one page.

    path: the scanned PDF.
    page_number: 1-based page to read.
    ocr: the shared OCR provider from core/dependencies.py (a fake in tests).
    """
    # Step 1: pixels of the page.
    png = await asyncio.to_thread(_render_page_png, path, page_number)
    # Step 2: text from the pixels.
    return await ocr.read_text(png)
