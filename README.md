# Role-Aware Knowledge Assistant

A chat backend for **Northwind Logistics** (a fictional freight carrier) that answers questions from internal documents, and only from the documents the person asking is allowed to read. It turns PDFs (one of them scanned) into searchable chunks tagged with their audience and clearance, enforces those tags **inside** the vector search, streams the LLM's answer over a WebSocket with citations, and lets the model look up live shipment data through tools that run in parallel and are bound to the authenticated user.

An Inkplain practical case: a real project built step by step.

## What the final version does
- **Auth**: a client opens `ws://localhost:8000/ws/chat` and sends a JWT first. Its `role` (driver, dispatcher, safety, sales, leadership) and `clearance` (public, internal, confidential) are the user's identity for everything that follows.
- **Ingestion**: `docs_src/*.md` → PDFs (the incident review as an image-only scan) → page text (EasyOCR for scanned pages) → 120-word chunks with 30-word overlap → `aud_<role>` flags and `clearance_rank` per chunk → bge embeddings → Chroma.
- **Retrieval**: `{"$and": [{"aud_<role>": true}, {"clearance_rank": {"$lte": <rank>}}]}` is part of the Chroma query, so forbidden passages are never candidates.
- **Answering**: the allowed passages, labelled `[file p.N]`, go to OpenAI or Gemini (or an offline fake) behind one `LLMProvider` interface; the answer streams back with citations.
- **Tools**: `get_shipment_overview(shipment_id)` checks visibility (drivers their trips, sales their accounts, operations roles all), then fetches status, ETA and SLA concurrently with `asyncio.gather` (~1 s instead of ~3 s).
- **Hardening**: failures become `error` events and the connection stays open; message size limit; logging; a browser test client.

## The steps
| Step | Branch | What it adds |
|---|---|---|
| 1 | `step-01-authenticated-websocket` | FastAPI skeleton, `/ws/chat` with a JWT handshake (role + clearance), demo token CLI, fake streaming LLM |
| 2 | `step-02-ingest-tagged-chunks` | Sample PDFs (one scanned), extraction + OCR, chunking, audience/clearance tags, embeddings, Chroma |
| 3 | `step-03-access-aware-retrieval` | The access filter inside the vector query; `sources` event |
| 4 | `step-04-stream-answers` | Prompt with labelled allowed passages; OpenAI and Gemini streaming providers |
| 5 | `step-05-parallel-shipment-tools` | User-bound shipment tool; visibility rule; three concurrent lookups; tool calling in both SDKs |
| 6 | `step-06-hardening` | Errors as events without closing the socket, input limit, logging, browser test client |

`main` is the same code as step 6.

## How to follow the steps
```bash
git clone https://github.com/Inplain-Tracks-Items/practical--role-aware-knowledge-assistant.git
cd practical--role-aware-knowledge-assistant
git checkout step-01-authenticated-websocket
# read STEP-1.md: what the step teaches, what changed, how to run and verify it
pytest
git checkout step-02-ingest-tagged-chunks   # and so on
```
Every step branch runs and passes its tests on its own.

## Run the final version
Requires Python 3.12+ and about 2 GB of disk for the embedding and OCR models (downloaded on first use).
```bash
python -m venv .venv
source .venv/bin/activate                         # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                              # set JWT_SECRET; optionally LLM_PROVIDER + its key
python -m app.features.feature_sample_docs.cli    # builds docs/*.pdf
python -m app.features.feature_ingest.cli         # fills chroma_data/
python -m app.features.feature_auth.cli           # prints a token per demo user
uvicorn app.main:app --reload                     # ws://localhost:8000/ws/chat
```
Then open `test_client.html` in a browser, paste a token and ask, for example, "What bonus can I earn?" as the driver and as the leader, or "Where is NW-1042?".

Tests: `pytest` (offline: hashing embeddings, fake OCR and fake LLM). Opt-in: `RUN_OCR=1 pytest tests/test_ocr_real.py`, `RUN_LIVE_LLM=1 LIVE_LLM_PROVIDER=gemini GEMINI_API_KEY=... pytest tests/test_llm_live.py`.

## Stack and configuration
Python, FastAPI + uvicorn (WebSocket), PyJWT, pydantic-settings, Chroma (local, persistent), sentence-transformers (`BAAI/bge-small-en-v1.5`), PyMuPDF, EasyOCR, OpenAI and Google Gen AI SDKs, pytest. Every variable is listed and explained in `.env.example`; only `JWT_SECRET` is required, and the default `LLM_PROVIDER=fake` runs without any API key.

The code follows the Inkplain Codebase Structure (ICS): thin doors (`router.py`, `cli.py`, `main.py`), handlers that orchestrate, single-job services, providers behind interfaces injected once, one export per file, and teaching comments in every file.

## Diagrams
Every step branch has a `STEP-N.crd` file at its root: the Component Relation Diagram of the whole system on that branch (components, contracts, call relations, and what the step added or changed). `FINAL.crd` here on main describes the final version. A `role-aware-knowledge-assistant.inkp` Inkplain Simulator project with one tab per step (`STEP-1` … `STEP-6`) is added to main from these files; import it with Simulator → Project → Import Project (.inkp).
