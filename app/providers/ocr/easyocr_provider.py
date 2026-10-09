# OCR with EasyOCR: reads the text of scanned PDF pages locally on the CPU.
# ICS layer: provider
# CRD component: be.EasyOcrProvider.read_text
# Called by: core/dependencies.py, feature_ingest/services/service_ocr_page.py
# Calls: easyocr (downloads its detection and recognition models on first use)
# Step: added in step 2 (Ingest tagged chunks)

import asyncio  # OCR is slow and blocking; it runs in a worker thread


class EasyOcrProvider:
    """EasyOCR reader, built once per process because loading its models takes seconds."""

    def __init__(self, languages: list[str]) -> None:
        """languages: EasyOCR language codes, e.g. ["en"]."""
        # Imported here so that importing this module (for example in tests) does not load torch.
        import easyocr

        # gpu=False: works on any laptop; a GPU only makes it faster.
        self._reader = easyocr.Reader(languages, gpu=False)

    async def read_text(self, png_bytes: bytes) -> str:
        """Return the page text; paragraph=True merges detected lines into paragraphs."""
        # detail=0 returns plain strings instead of (box, text, confidence) tuples.
        paragraphs = await asyncio.to_thread(self._reader.readtext, png_bytes, detail=0, paragraph=True)
        return "\n".join(paragraphs)
