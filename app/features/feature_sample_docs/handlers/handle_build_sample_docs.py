# Builds every Northwind sample PDF from its Markdown source; scanned documents are rasterized after rendering.
# ICS layer: handler
# CRD component: be.handle_build_sample_docs
# Called by: feature_sample_docs/cli.py, tests
# Calls: be.service_read_text_file, be.service_render_text_pdf, be.service_rasterize_pdf, be.service_write_file
# Step: added in step 2 (Ingest tagged chunks)

from pathlib import Path  # source and output folders

from app.features.feature_sample_docs.configs.sample_docs import SAMPLE_DOCS  # what to build
from app.features.feature_sample_docs.services.service_rasterize_pdf import service_rasterize_pdf  # removes the text layer
from app.features.feature_sample_docs.services.service_read_text_file import service_read_text_file  # loads Markdown
from app.features.feature_sample_docs.services.service_render_text_pdf import service_render_text_pdf  # Markdown -> PDF
from app.features.feature_sample_docs.services.service_write_file import service_write_file  # saves the PDF


async def handle_build_sample_docs(src_dir: Path, out_dir: Path) -> list[dict]:
    """Render all SAMPLE_DOCS from src_dir into out_dir.

    src_dir: folder with the Markdown sources (docs_src/).
    out_dir: folder the PDFs are written to (docs/), created when missing.
    Returns one {"pdf": name, "scanned": bool} entry per file written.
    """
    built = []
    for doc in SAMPLE_DOCS:
        # Step 1: load the Markdown source of this document.
        markdown = await service_read_text_file(src_dir / doc["source"])
        # Step 2: render it to a PDF with a selectable text layer.
        pdf_bytes = await service_render_text_pdf(markdown)
        # Step 3: for "scanned" documents, replace every page with its picture.
        if doc["scanned"]:
            pdf_bytes = await service_rasterize_pdf(pdf_bytes)
        # Step 4: save the result under its PDF name; ingestion reads it from there.
        await service_write_file(out_dir / doc["pdf"], pdf_bytes)
        built.append({"pdf": doc["pdf"], "scanned": doc["scanned"]})
    return built
