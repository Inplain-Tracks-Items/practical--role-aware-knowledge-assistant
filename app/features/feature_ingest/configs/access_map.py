# Who may read which Northwind document: the single source of truth for document access.
# ICS layer: config
# Called by: feature_ingest/handlers/handle_ingest_documents.py
# Calls: nothing
# Step: added in step 2 (Ingest tagged chunks)

from app.features.feature_ingest.schemas.ingest_schemas import DocumentAccess  # validated access entry

# Keyed by PDF file name. A PDF that is not listed here is NOT ingested at all
# (fail closed): forgetting to classify a document must never make it readable by everyone.
ACCESS_MAP: dict[str, DocumentAccess] = {
    # Everyone works under the handbook, and nothing in it is sensitive.
    "employee_handbook.pdf": DocumentAccess(audience=["driver", "dispatcher", "safety", "sales", "leadership"], clearance="public"),
    # Drivers follow it; dispatch plans with it; safety enforces it.
    "driver_safety_manual.pdf": DocumentAccess(audience=["driver", "dispatcher", "safety"], clearance="internal"),
    # How dispatch runs the day; leadership and safety review it weekly.
    "dispatch_playbook.pdf": DocumentAccess(audience=["dispatcher", "safety", "leadership"], clearance="internal"),
    # What we sell and the penalties; dispatch needs the windows, leadership approves discounts.
    "customer_sla_guide.pdf": DocumentAccess(audience=["sales", "dispatcher", "leadership"], clearance="internal"),
    # Pay of the leadership team: leadership only, confidential.
    "leadership_compensation_plan.pdf": DocumentAccess(audience=["leadership"], clearance="confidential"),
    # Scanned incident report with injury details: safety and leadership, confidential.
    "incident_review_q2.pdf": DocumentAccess(audience=["safety", "leadership"], clearance="confidential"),
}
