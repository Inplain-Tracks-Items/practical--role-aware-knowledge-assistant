# Proves real OCR reads the scanned sample PDF. Slow (loads EasyOCR models), so it only runs with RUN_OCR=1.
# ICS layer: test
# Covers: be.service_ocr_page, be.EasyOcrProvider.read_text
# Step: added in step 2 (Ingest tagged chunks)

import asyncio  # the services are async
import os  # RUN_OCR switch
from pathlib import Path  # repo paths

import pytest  # skip marker

from app.features.feature_ingest.services.service_ocr_page import service_ocr_page
from app.features.feature_sample_docs.handlers.handle_build_sample_docs import handle_build_sample_docs

DOCS_SRC = Path(__file__).resolve().parents[1] / "docs_src"


@pytest.mark.skipif(os.environ.get("RUN_OCR") != "1", reason="set RUN_OCR=1 to run real OCR (downloads models on first run)")
def test_easyocr_reads_the_scanned_incident_review(tmp_path):
    # EasyOcrProvider: page 1 of the image-only incident review comes back as readable text.
    from app.providers.ocr.easyocr_provider import EasyOcrProvider

    asyncio.run(handle_build_sample_docs(DOCS_SRC, tmp_path))
    text = asyncio.run(service_ocr_page(tmp_path / "incident_review_q2.pdf", 1, EasyOcrProvider(["en"])))
    assert "forklift" in text.lower()
    assert "duisburg" in text.lower()
