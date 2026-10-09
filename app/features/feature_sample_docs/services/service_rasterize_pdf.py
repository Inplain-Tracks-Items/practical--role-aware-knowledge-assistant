# Turns a PDF into a "scanned" PDF: every page becomes a grey-scale image, and the text layer is gone.
# ICS layer: service
# CRD component: be.service_rasterize_pdf
# Called by: feature_sample_docs/handlers/handle_build_sample_docs.py
# Calls: PyMuPDF (page rendering and image insertion)
# Step: added in step 2 (Ingest tagged chunks)

import asyncio  # rasterizing is CPU work; it runs in a worker thread

import pymupdf  # PyMuPDF: renders pages to pixels and builds the image-only PDF

# 150 dpi is a typical office-scanner resolution: readable for OCR, small files.
SCAN_DPI = 150


def _rasterize(pdf_bytes: bytes) -> bytes:
    """Render each page of pdf_bytes to an image and place it on a page of a new PDF."""
    source = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    scanned = pymupdf.open()
    for page in source:
        # Grey-scale pixels of the whole page, like a scanner produces.
        pixmap = page.get_pixmap(dpi=SCAN_DPI, colorspace=pymupdf.csGRAY)
        # Same page size as the original, but its only content is the picture.
        target = scanned.new_page(width=page.rect.width, height=page.rect.height)
        target.insert_image(target.rect, pixmap=pixmap)
    return scanned.tobytes()


async def service_rasterize_pdf(pdf_bytes: bytes) -> bytes:
    """Return an image-only copy of pdf_bytes; text extraction on it returns nothing, so OCR is needed."""
    return await asyncio.to_thread(_rasterize, pdf_bytes)
