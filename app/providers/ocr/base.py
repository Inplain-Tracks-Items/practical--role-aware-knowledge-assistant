# The interface every OCR provider implements: page image in, text out.
# ICS layer: provider (interface)
# Called by: feature_ingest/services/service_ocr_page.py, core/dependencies.py
# Calls: nothing (a Protocol has no behaviour)
# Step: added in step 2 (Ingest tagged chunks)

from typing import Protocol  # structural interface


class OcrProvider(Protocol):
    """Reads printed text from an image."""

    async def read_text(self, png_bytes: bytes) -> str:
        """Return the text found in a PNG image, paragraphs separated by newlines."""
        ...
