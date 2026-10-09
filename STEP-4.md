# Step 4 of 6 — Stream answers

## What you build in this step
Real answers. The passages retrieved in step 3, and only those, are placed into a system prompt with answering rules and citation labels, sent to a real LLM (OpenAI or Gemini) and streamed back to the client piece by piece. The provider is a configuration choice (`LLM_PROVIDER`), and the offline fake from step 1 stays the default, so the code still runs and tests without a key.

## What you learn
- Prompt construction for RAG: rules, a labelled CONTEXT section, and an explicit "nothing found" placeholder so the model does not guess.
- Citations that are always openable: the model copies `[file p.N]` labels that only exist for pages the user may read.
- Streaming from two different SDKs (OpenAI Chat Completions, Gemini `generate_content_stream`) behind one `LLMProvider` interface.
- Choosing a provider once at startup with dependency injection, and failing early with a clear message when its key is missing.
- Testing what reaches the model with a recording fake, without spending a request.

## What changed since step 3
| Component (STEP-4.crd) | Change | Files |
|---|---|---|
| `be.service_build_prompt` | added: rules + labelled allowed passages | `app/features/feature_chat/services/service_build_prompt.py` |
| `be.OpenAIProvider.stream_chat` | added: OpenAI streaming | `app/providers/llm/openai_provider.py` |
| `be.GeminiProvider.stream_chat` | added: Gemini streaming | `app/providers/llm/gemini_provider.py` |
| `ext.openai_api`, `ext.gemini_api` | added: external LLM boundaries | — |
| `be.handle_chat_socket` | changed: builds the prompt from the allowed chunks before streaming | `app/features/feature_chat/handlers/handle_chat_socket.py` |
| `be.service_stream_answer` | changed: takes the built prompt instead of a fixed one | `app/features/feature_chat/services/service_stream_answer.py` |
| `be.get_llm_provider` | changed: `openai` and `gemini`, with an API-key check | `app/core/dependencies.py` |
| everything else | unchanged | |

## Run it
```bash
pip install -r requirements.txt     # adds openai and google-genai
# in .env:
LLM_PROVIDER=gemini                 # or openai
GEMINI_API_KEY=...                  # or OPENAI_API_KEY=...
uvicorn app.main:app --reload
```
Ask **"What bonus can I earn?"** as the driver and as the leader. A real run with Gemini 2.5 Flash and the bge index:

> **driver** — sources: driver_safety_manual.pdf p.1, employee_handbook.pdf p.1
> Drivers can earn a safe driving bonus of 150 euros per quarter (driver_safety_manual.pdf p.1). To qualify, drivers must have no preventable incidents, no speeding alerts from the telematics system, and complete inspection records for every trip (driver_safety_manual.pdf p.1). …

> **leadership** — sources: leadership_compensation_plan.pdf p.1, employee_handbook.pdf p.1
> The annual leadership bonus is between 0 and 25 percent of base salary (leadership_compensation_plan.pdf p.1). It is calculated based on three company targets: on-time delivery above 96% (40% of bonus), operating margin above 7.5% (40% of bonus), and zero fatal or serious injury incidents (20% of bonus) …

Same question, same model, different answers, because each prompt only contains what its reader may see.

## Verify it
```bash
pytest                                                    # 28 passed, 2 skipped
RUN_LIVE_LLM=1 LIVE_LLM_PROVIDER=gemini GEMINI_API_KEY=... pytest tests/test_llm_live.py
```
`tests/test_answering.py` proves that every passage is labelled with its citation, that an empty retrieval produces the "nothing found" placeholder, that the driver's prompt contains the driver manual and not a word of the leadership plan, that the model's pieces arrive in order followed by `done`, and that `LLM_PROVIDER` picks the class and a missing key fails with its name. The live test (skipped by default) asks the real model and checks that the answer uses the passage and cites it.

## Diagram
Import `role-aware-knowledge-assistant.inkp` from main in Inkplain Simulator (Project → Import Project (.inkp)) and open the `STEP-4` tab to see this step's components.

## Next
Step 5 — Parallel shipment tools: the model can look up a shipment's status, route ETA and customer SLA, three calls run concurrently, and only for shipments the user may see.
