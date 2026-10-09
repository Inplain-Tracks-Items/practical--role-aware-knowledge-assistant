# Runs the ingestion pipeline: PDF -> page text (OCR for scanned pages) -> chunks -> access tags -> vectors -> Chroma.
# ICS layer: handler
# CRD component: be.handle_ingest_documents
# Called by: feature_ingest/cli.py, tests
# Calls: be.service_list_pdfs, be.service_extract_pages, be.service_ocr_page, be.service_chunk_text,
#        be.util_build_chunk_metadata, be.service_embed_texts, be.service_store_chunks
# Step: added in step 2 (Ingest tagged chunks)

from pathlib import Path  # the docs folder

from app.features.feature_ingest.configs.access_map import ACCESS_MAP  # who may read which PDF
from app.features.feature_ingest.schemas.ingest_schemas import ChunkRecord  # what gets stored
from app.features.feature_ingest.services.service_chunk_text import service_chunk_text  # page -> chunks
from app.features.feature_ingest.services.service_embed_texts import service_embed_texts  # chunks -> vectors
from app.features.feature_ingest.services.service_extract_pages import service_extract_pages  # PDF -> pages
from app.features.feature_ingest.services.service_list_pdfs import service_list_pdfs  # what to ingest
from app.features.feature_ingest.services.service_ocr_page import service_ocr_page  # scanned page -> text
from app.features.feature_ingest.services.service_store_chunks import service_store_chunks  # -> vector store
from app.features.feature_ingest.utils.util_build_chunk_metadata import util_build_chunk_metadata  # access tags
from app.providers.embeddings.base import EmbeddingProvider  # injected interfaces
from app.providers.ocr.base import OcrProvider
from app.providers.vectorstore.base import VectorStore


async def handle_ingest_documents(
    docs_dir: Path,
    chunk_size_words: int,
    chunk_overlap_words: int,
    embedder: EmbeddingProvider,
    store: VectorStore,
    ocr: OcrProvider,
) -> dict:
    """Ingest every classified PDF in docs_dir into the vector store.

    docs_dir: folder with the PDFs (built by feature_sample_docs).
    chunk_size_words, chunk_overlap_words: chunking parameters from settings.
    embedder, store, ocr: the shared providers (fakes in tests).
    Returns {"ingested": [file names], "skipped": [file names], "ocr_pages": int, "chunks": int}.
    """
    records: list[ChunkRecord] = []
    ingested, skipped, ocr_pages = [], [], 0

    # Step 1: find the PDFs.
    for pdf in await service_list_pdfs(docs_dir):
        # Step 2: look up who may read this document; unclassified files are skipped (fail closed).
        access = ACCESS_MAP.get(pdf.name)
        if access is None:
            skipped.append(pdf.name)
            continue
        # Step 3: page texts; scanned pages come back empty with needs_ocr=True.
        for page in await service_extract_pages(pdf):
            text = page.text
            # Step 4: OCR only the pages that need it; text pages are never sent through OCR.
            if page.needs_ocr:
                text = await service_ocr_page(pdf, page.page, ocr)
                ocr_pages += 1
            # Step 5: chunk the page and tag every chunk with the document's access.
            for index, chunk in enumerate(service_chunk_text(text, chunk_size_words, chunk_overlap_words)):
                records.append(ChunkRecord(
                    id=f"{pdf.name}:p{page.page}:c{index}",
                    text=chunk,
                    metadata=util_build_chunk_metadata(pdf.name, page.page, index, access),
                ))
        ingested.append(pdf.name)

    # Step 6: embed all chunks in one batch, then store them with their tags.
    embeddings = await service_embed_texts([r.text for r in records], embedder)
    stored = await service_store_chunks(records, embeddings, store)
    return {"ingested": ingested, "skipped": skipped, "ocr_pages": ocr_pages, "chunks": stored}
