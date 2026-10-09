# Step 3 of 6 — Access-aware retrieval

## What you build in this step
Search that respects who is asking. For every question, the user's **role** and **clearance** (from the verified token of step 1) become a filter inside the Chroma query, built on the tags stored in step 2. The server now sends a `sources` event listing the pages it found, before the (still echoed) answer.

This is the heart of the case: a forbidden passage is never a search candidate, so it can never reach the model, the answer or the citations.

## What you learn
- Writing an access rule as a vector-store filter: `{"$and": [{"aud_driver": true}, {"clearance_rank": {"$lte": 1}}]}`.
- Why the filter belongs **inside** the query (pre-filtering) and not in Python afterwards (post-filtering): with post-filtering, the top-k places can all be taken by forbidden chunks and the user gets nothing even when allowed answers exist.
- Taking identity only from the verified token, never from the message, so a question cannot widen its own access.
- Testing an access rule exhaustively: every demo user × every question × every returned chunk.

## What changed since step 2
| Component (STEP-3.crd) | Change | Files |
|---|---|---|
| `be.service_retrieve_chunks` | added: filter → embed query → filtered search | `app/features/feature_chat/services/service_retrieve_chunks.py` |
| `be.util_build_access_filter` | added: role + clearance → where-filter | `app/features/feature_chat/utils/util_build_access_filter.py` |
| `be.ChromaStore.query` | added: `collection.query(..., where=...)` | `app/providers/vectorstore/chroma_store.py` |
| `be.SentenceTransformersProvider.embed_query`, `be.HashingProvider.embed_query` | added: the query side of both embedders | `app/providers/embeddings/` |
| `be.handle_chat_socket` | changed: retrieves allowed chunks per question and sends `sources` | `app/features/feature_chat/handlers/handle_chat_socket.py` |
| `be.chat_socket` | changed: injects the embedder and the vector store | `app/features/feature_chat/router.py` |
| everything else | unchanged | |

Also new: `RetrievedChunk` (`app/providers/vectorstore/retrieved_chunk.py`), `SourceRef` / `SourcesEvent` in `chat_schemas.py`, the `query()` method on the `VectorStore` interface and `RETRIEVAL_TOP_K` in settings.

The protocol after a question is now:
```
< {"type": "sources", "sources": [{"source_file": "driver_safety_manual.pdf", "page": 1}, ...]}
< {"type": "stream", "text": "Echo: "} ...
< {"type": "done"}
```

## Run it
Nothing new to install. If `chroma_data/` from step 2 is missing, build and ingest first:
```bash
python -m app.features.feature_sample_docs.cli
python -m app.features.feature_ingest.cli
uvicorn app.main:app --reload
```
Log in as the driver and as the leader (tokens from `python -m app.features.feature_auth.cli`) and ask both **"What bonus can I earn?"**. With the real bge model, the top three chunks are:

| User | Sources |
|---|---|
| driver (internal) | driver_safety_manual, driver_safety_manual, employee_handbook |
| sales (internal) | employee_handbook, customer_sla_guide, employee_handbook |
| leadership (confidential) | leadership_compensation_plan, leadership_compensation_plan, employee_handbook |

and for **"What happened in the forklift injury incident?"** only safety and leadership get `incident_review_q2` (the scanned, OCR'd report).

## Verify it
```bash
pytest          # 22 passed, 1 skipped
```
`tests/test_retrieval.py` checks every demo user against six questions and asserts that every returned chunk's document lists the user's role and is not above their clearance; that the bonus question gives the driver and the leader different documents; that the scanned report reaches safety but not sales; that the filter runs before ranking (the driver still gets three allowed chunks for a question whose best matches are all in the leadership plan); and that the socket's `sources` event lists allowed pages only. The tests run on the offline hashing embedder; the table above was produced with the real model.

## Diagram
Import `role-aware-knowledge-assistant.inkp` from main in Inkplain Simulator (Project → Import Project (.inkp)) and open the `STEP-3` tab to see this step's components.

## Next
Step 4 — Stream answers: the retrieved passages go to a real LLM (OpenAI or Gemini) behind the same provider interface, and its answer streams back with citations.
