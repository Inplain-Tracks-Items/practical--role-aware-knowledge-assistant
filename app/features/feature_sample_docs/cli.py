# Command-line door of the sample-docs feature: renders docs_src/*.md into docs/*.pdf.
# Run: python -m app.features.feature_sample_docs.cli
# ICS layer: door
# CRD component: be.sample_docs_cli
# Called by: a developer in the terminal (once, before ingestion)
# Calls: be.handle_build_sample_docs
# Step: added in step 2 (Ingest tagged chunks)

import asyncio  # runs the async handler from a plain script
from pathlib import Path  # turns the configured folder names into paths

from app.core.config import get_settings  # docs_src_dir and docs_dir
from app.features.feature_sample_docs.handlers.handle_build_sample_docs import handle_build_sample_docs  # does the work


def main() -> None:
    """Build the PDFs and print one line per file."""
    settings = get_settings()
    # The door only delegates and prints the outcome.
    built = asyncio.run(handle_build_sample_docs(Path(settings.docs_src_dir), Path(settings.docs_dir)))
    for entry in built:
        print(f"built {entry['pdf']}{'  (scanned, image-only)' if entry['scanned'] else ''}")


# Runs only when executed as a module, not when imported by tests.
if __name__ == "__main__":
    main()
