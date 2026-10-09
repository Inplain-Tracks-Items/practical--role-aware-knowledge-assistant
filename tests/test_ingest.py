# Proves the ingestion pipeline: sample PDFs (one scanned), chunking, access tags, and what lands in Chroma.
# ICS layer: test
# Covers: be.handle_build_sample_docs, be.handle_ingest_documents, be.service_extract_pages, be.service_ocr_page,
#         be.service_chunk_text, be.util_build_chunk_metadata, be.ChromaStore.upsert, be.HashingProvider.embed_documents
# Step: added in step 2 (Ingest tagged chunks)

import asyncio  # the pipeline is async; tests drive it with asyncio.run
from pathlib import Path  # repo and temp folders

import chromadb  # read the stored metadata back directly
import pytest  # fixtures and raises

from app.features.feature_ingest.configs.access_map import ACCESS_MAP
from app.features.feature_ingest.handlers.handle_ingest_documents import handle_ingest_documents
from app.features.feature_ingest.services.service_chunk_text import service_chunk_text
from app.features.feature_ingest.services.service_extract_pages import service_extract_pages
from app.features.feature_ingest.utils.util_build_chunk_metadata import util_build_chunk_metadata
from app.features.feature_sample_docs.handlers.handle_build_sample_docs import handle_build_sample_docs
from app.providers.embeddings.hashing_provider import HashingProvider
from app.providers.vectorstore.chroma_store import ChromaStore
from tests.fakes.fake_ocr_provider import FakeOcrProvider

# docs_src/ lives at the repo root, one level above tests/.
DOCS_SRC = Path(__file__).resolve().parents[1] / "docs_src"


@pytest.fixture
def sample_pdfs(tmp_path) -> Path:
    """Build the six sample PDFs into a temp folder and return it."""
    out = tmp_path / "docs"
    asyncio.run(handle_build_sample_docs(DOCS_SRC, out))
    return out


def test_chunks_overlap_and_cover_the_whole_text():
    # service_chunk_text: 300 words, size 120, overlap 30 -> windows start at 0, 90, 180;
    # neighbours share 30 words and the last chunk ends with the last word.
    words = [f"w{i}" for i in range(300)]
    chunks = service_chunk_text(" ".join(words), 120, 30)
    assert [c.split()[0] for c in chunks] == ["w0", "w90", "w180"]
    assert chunks[0].split()[-30:] == chunks[1].split()[:30]
    assert chunks[-1].split()[-1] == "w299"


def test_chunker_rejects_an_overlap_that_never_advances():
    # service_chunk_text: overlap >= size would loop forever, so it is refused.
    with pytest.raises(ValueError):
        service_chunk_text("a b c", 10, 10)


def test_metadata_carries_one_flag_per_role_and_a_clearance_rank():
    # util_build_chunk_metadata: the driver manual is for driver/dispatcher/safety at "internal" (rank 1).
    meta = util_build_chunk_metadata("driver_safety_manual.pdf", 2, 0, ACCESS_MAP["driver_safety_manual.pdf"])
    assert meta["aud_driver"] is True and meta["aud_safety"] is True
    assert meta["aud_sales"] is False and meta["aud_leadership"] is False
    assert meta["clearance_rank"] == 1 and meta["page"] == 2


def test_sample_docs_have_one_scanned_pdf_without_text(sample_pdfs):
    # handle_build_sample_docs + service_extract_pages: text PDFs have a text layer; the scanned one has none.
    handbook = asyncio.run(service_extract_pages(sample_pdfs / "employee_handbook.pdf"))
    scanned = asyncio.run(service_extract_pages(sample_pdfs / "incident_review_q2.pdf"))
    assert not any(p.needs_ocr for p in handbook) and "Northwind" in handbook[0].text
    assert all(p.needs_ocr for p in scanned)


def test_ingest_stores_every_chunk_with_its_access_tags(sample_pdfs, tmp_path):
    # handle_ingest_documents: all six PDFs are ingested, the scanned one through OCR, and every
    # stored chunk carries the audience flags and clearance rank of its document.
    ocr = FakeOcrProvider()
    store = ChromaStore(path=str(tmp_path / "chroma"), collection_name="test_docs")
    summary = asyncio.run(handle_ingest_documents(sample_pdfs, 120, 30, HashingProvider(), store, ocr))

    assert sorted(summary["ingested"]) == sorted(ACCESS_MAP)
    assert summary["ocr_pages"] == ocr.calls >= 1
    assert summary["chunks"] == asyncio.run(store.count()) > 6

    # Read the scanned report's chunks straight from Chroma: OCR text, confidential, safety + leadership only.
    collection = chromadb.PersistentClient(path=str(tmp_path / "chroma")).get_collection("test_docs")
    rows = collection.get(where={"source_file": "incident_review_q2.pdf"})
    assert rows["documents"] and all("forklift" in d for d in rows["documents"])
    for meta in rows["metadatas"]:
        assert meta["clearance_rank"] == 2
        assert meta["aud_safety"] and meta["aud_leadership"]
        assert not meta["aud_driver"] and not meta["aud_sales"] and not meta["aud_dispatcher"]


def test_unclassified_pdf_is_skipped_not_made_public(sample_pdfs, tmp_path):
    # handle_ingest_documents: a PDF missing from ACCESS_MAP is never stored (fail closed).
    (sample_pdfs / "secret_merger_plan.pdf").write_bytes((sample_pdfs / "employee_handbook.pdf").read_bytes())
    store = ChromaStore(path=str(tmp_path / "chroma"), collection_name="test_docs")
    summary = asyncio.run(handle_ingest_documents(sample_pdfs, 120, 30, HashingProvider(), store, FakeOcrProvider()))
    assert summary["skipped"] == ["secret_merger_plan.pdf"]
    collection = chromadb.PersistentClient(path=str(tmp_path / "chroma")).get_collection("test_docs")
    assert collection.get(where={"source_file": "secret_merger_plan.pdf"})["ids"] == []
