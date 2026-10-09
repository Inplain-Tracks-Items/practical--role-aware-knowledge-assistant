# Step 2 of 6 — Ingest tagged chunks

## What you build in this step
The ingestion pipeline. Northwind's six documents (written for this course, in `docs_src/`) are rendered into PDFs, and the incident review is rendered as a **scanned**, image-only PDF. The pipeline reads every page (with OCR when a page has no text layer), cuts it into overlapping chunks, tags every chunk with **who may read it** and stores it with its embedding in a local Chroma collection.

The tags come now, before any search exists, because access control that is added after the data is indexed always leaves holes. Every chunk is born with its audience and clearance.

## What you learn
- Extracting PDF text with PyMuPDF and detecting scanned pages (no text layer) to send them through OCR (EasyOCR).
- A chunking strategy you can defend: 120-word windows with a 30-word overlap, never crossing a page (see below).
- Encoding an access model as vector-store metadata: one boolean per role (`aud_driver`, `aud_sales`, …) plus a numeric `clearance_rank`, so that step 3 can filter inside the query.
- Failing closed: a PDF that is missing from `ACCESS_MAP` is skipped, never stored as "public".
- Keeping blocking libraries (PyMuPDF, EasyOCR, sentence-transformers, Chroma) off the event loop with `asyncio.to_thread`, and keeping each one behind a provider interface.

### Why these chunks
- **Per page**: every chunk has exactly one page to cite.
- **120 words**: about one paragraph of these documents, large enough to hold a whole rule ("after 4.5 hours of driving a break of 45 minutes…"), small enough to stay on one topic, so its vector is not diluted.
- **30-word overlap**: a sentence cut at a chunk border still appears whole in one of the two neighbours.

### The access model
| Document | Audience | Clearance |
|---|---|---|
| `employee_handbook.pdf` | all five roles | public |
| `driver_safety_manual.pdf` | driver, dispatcher, safety | internal |
| `dispatch_playbook.pdf` | dispatcher, safety, leadership | internal |
| `customer_sla_guide.pdf` | sales, dispatcher, leadership | internal |
| `leadership_compensation_plan.pdf` | leadership | confidential |
| `incident_review_q2.pdf` (scanned) | safety, leadership | confidential |

A user may read a chunk when **their role is in its audience and their clearance rank is at least the chunk's** (public 0, internal 1, confidential 2). Step 3 turns this sentence into a query filter.

## What changed since step 1
| Component (STEP-2.crd) | Change | Files |
|---|---|---|
| `be.sample_docs_cli`, `be.handle_build_sample_docs` | added: builds `docs/*.pdf` from `docs_src/*.md` | `app/features/feature_sample_docs/cli.py`, `handlers/handle_build_sample_docs.py` |
| `be.service_read_text_file`, `be.service_render_text_pdf`, `be.service_rasterize_pdf`, `be.service_write_file` | added: read, render, "scan", write | `app/features/feature_sample_docs/services/` |
| `be.ingest_cli`, `be.handle_ingest_documents` | added: the pipeline and its door | `app/features/feature_ingest/cli.py`, `handlers/handle_ingest_documents.py` |
| `be.service_list_pdfs`, `be.service_extract_pages`, `be.service_ocr_page`, `be.service_chunk_text`, `be.service_embed_texts`, `be.service_store_chunks` | added: one job each | `app/features/feature_ingest/services/` |
| `be.util_build_chunk_metadata` | added: audience flags + clearance rank | `app/features/feature_ingest/utils/util_build_chunk_metadata.py` |
| `be.SentenceTransformersProvider.embed_documents`, `be.HashingProvider.embed_documents` | added: real and offline embedders | `app/providers/embeddings/` |
| `be.ChromaStore.upsert` | added: persistent Chroma collection | `app/providers/vectorstore/chroma_store.py` |
| `be.EasyOcrProvider.read_text` | added: OCR | `app/providers/ocr/easyocr_provider.py` |
| `be.get_embedder`, `be.get_vectorstore`, `be.get_ocr_provider` | added: provider factories | `app/core/dependencies.py` |
| all step 1 components | unchanged | |

Also new: `app/features/feature_ingest/configs/access_map.py` (the table above), `schemas/ingest_schemas.py`, new settings in `app/core/config.py` and `.env.example`.

## Run it
```bash
pip install -r requirements.txt                 # adds chromadb, sentence-transformers, pymupdf, easyocr
cp .env.example .env                            # or add the new step 2 variables to your .env
python -m app.features.feature_sample_docs.cli  # builds docs/*.pdf, one of them scanned
python -m app.features.feature_ingest.cli       # first run downloads the bge and EasyOCR models
```
Expected output of the last command:
```
ingested 6 PDFs, 19 chunks, 1 page(s) read with OCR
```
No model download wanted yet? Set `EMBEDDING_PROVIDER=hashing` in `.env`. OCR still needs EasyOCR for the scanned page. Switching providers later means deleting `chroma_data/` and ingesting again, because the vector sizes differ.

## Verify it
```bash
pytest                                  # 12 passed, 1 skipped
RUN_OCR=1 pytest tests/test_ocr_real.py # real EasyOCR on the scanned PDF (slow)
```
The tests prove that the chunks overlap and cover each page, that every chunk carries one flag per role and a clearance rank, that the incident review has no text layer and is read through OCR, that its chunks are stored as confidential and visible to safety and leadership only, and that an unclassified PDF is never stored.

## Diagram
Import `role-aware-knowledge-assistant.inkp` from main in Inkplain Simulator (Project → Import Project (.inkp)) and open the `STEP-2` tab to see this step's components.

## Next
Step 3 — Access-aware retrieval: the user's role and clearance become a filter inside the Chroma query, so forbidden passages are never even candidates.
