# Which Northwind PDFs to build from which Markdown source, and which one is rendered as a scanned (image-only) PDF.
# ICS layer: config
# Called by: feature_sample_docs/handlers/handle_build_sample_docs.py
# Calls: nothing
# Step: added in step 2 (Ingest tagged chunks)

# One entry per document. "scanned": True turns the PDF into page images with no text layer,
# like a signed paper report run through an office scanner, so ingestion has to OCR it.
SAMPLE_DOCS: list[dict] = [
    {"source": "employee_handbook.md", "pdf": "employee_handbook.pdf", "scanned": False},
    {"source": "driver_safety_manual.md", "pdf": "driver_safety_manual.pdf", "scanned": False},
    {"source": "dispatch_playbook.md", "pdf": "dispatch_playbook.pdf", "scanned": False},
    {"source": "customer_sla_guide.md", "pdf": "customer_sla_guide.pdf", "scanned": False},
    {"source": "leadership_compensation_plan.md", "pdf": "leadership_compensation_plan.pdf", "scanned": False},
    {"source": "incident_review_q2.md", "pdf": "incident_review_q2.pdf", "scanned": True},
]
