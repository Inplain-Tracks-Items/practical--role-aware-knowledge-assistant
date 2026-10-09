# Command-line door of the ingest feature: loads docs/*.pdf into the Chroma collection.
# Run: python -m app.features.feature_ingest.cli
# ICS layer: door
# CRD component: be.ingest_cli
# Called by: a developer in the terminal (after building the sample docs, before starting the server)
# Calls: be.handle_ingest_documents
# Step: added in step 2 (Ingest tagged chunks)

import asyncio  # runs the async handler from a plain script
from pathlib import Path  # docs_dir as a path

from app.core.config import get_settings  # folder and chunking settings
from app.core.dependencies import get_embedder, get_ocr_provider, get_vectorstore  # the shared providers
from app.features.feature_ingest.handlers.handle_ingest_documents import handle_ingest_documents  # the pipeline


def main() -> None:
    """Run the pipeline once and print a summary."""
    settings = get_settings()
    # The door wires the providers and delegates; all pipeline logic is in the handler.
    summary = asyncio.run(handle_ingest_documents(
        docs_dir=Path(settings.docs_dir),
        chunk_size_words=settings.chunk_size_words,
        chunk_overlap_words=settings.chunk_overlap_words,
        embedder=get_embedder(),
        store=get_vectorstore(),
        ocr=get_ocr_provider(),
    ))
    print(f"ingested {len(summary['ingested'])} PDFs, {summary['chunks']} chunks, {summary['ocr_pages']} page(s) read with OCR")
    # Unclassified PDFs are reported loudly: they are not searchable until added to ACCESS_MAP.
    for name in summary["skipped"]:
        print(f"skipped {name}: not in ACCESS_MAP")


# Runs only when executed as a module, not when imported by tests.
if __name__ == "__main__":
    main()
