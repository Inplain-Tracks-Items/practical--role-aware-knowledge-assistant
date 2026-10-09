# Pydantic models that travel through the ingestion pipeline: who may read a document, a page of text, a chunk to store.
# ICS layer: config (schemas)
# Called by: feature_ingest configs, services and handler
# Calls: Pydantic validation
# Step: added in step 2 (Ingest tagged chunks)

from typing import Any  # metadata values are str / int / bool

from pydantic import BaseModel, Field  # validated data models

from app.core.clearance import Clearance  # allowed sensitivity levels
from app.core.role import Role  # allowed audience roles


class DocumentAccess(BaseModel):
    """Who may read one document.

    audience: the roles the document is written for; at least one, unknown roles are rejected.
    clearance: how sensitive it is; a reader needs at least this clearance.
    """

    audience: list[Role] = Field(min_length=1)
    clearance: Clearance


class PageText(BaseModel):
    """The text of one PDF page.

    page: 1-based page number, shown to users as the citation.
    needs_ocr: True when the page has no text layer (a scanned page), so OCR must read it.
    """

    source_file: str
    page: int
    text: str
    needs_ocr: bool


class ChunkRecord(BaseModel):
    """One chunk ready for the vector store.

    id: stable "<file>:p<page>:c<index>", so re-ingesting replaces instead of duplicating.
    metadata: the access tags and citation fields stored next to the vector.
    """

    id: str
    text: str
    metadata: dict[str, Any]
