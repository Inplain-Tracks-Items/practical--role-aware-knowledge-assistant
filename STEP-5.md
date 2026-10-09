# Step 5 of 6 — Parallel shipment tools

## What you build in this step
Live operational data. The model gets one tool, `get_shipment_overview(shipment_id)`. When a user asks about a shipment ("Where is NW-1042?"), the model calls it; the tool first checks that **this user may see this shipment**, then fetches status, route ETA and customer SLA from three (mocked) operational APIs **at the same time**. Each API takes about a second; together they take about one second, not three.

The tool is bound to the user on the server: the model can choose a shipment id, never an identity.

## What you learn
- Exposing a Python function to an LLM as a tool: its name, type hints and docstring are the tool description.
- Running independent I/O concurrently with `asyncio.gather`, and proving the speed-up with a timing test.
- Binding a tool to the authenticated user with a closure, so a prompt cannot make the tool act for someone else.
- Applying access control in a tool before any data is fetched, and answering "missing" and "forbidden" identically so the model cannot learn which shipments exist.
- Tool calling in two SDKs: the OpenAI streaming tool-call loop (fragments collected, tools run concurrently, next round streamed) and Gemini's automatic function calling in the chat API.

### Who sees which shipment
| Role | Visible shipments |
|---|---|
| driver (`drv-101`) | the ones they drive: NW-1042, NW-1103 |
| sales (`sal-401`) | the ones of customers they own: NW-1042, NW-1077 |
| dispatcher, safety, leadership | all |

## What changed since step 4
| Component (STEP-5.crd) | Change | Files |
|---|---|---|
| `be.tool_bind_shipment_overview`, `be.get_shipment_overview` | added: binds the tool to the user; the function the model calls | `app/features/feature_shipment_tool/tool_bind_shipment_overview.py` |
| `be.tool_get_shipment_overview` | added: visibility check, then three concurrent calls | `app/features/feature_shipment_tool/tool_get_shipment_overview.py` |
| `be.service_find_visible_shipment` | added: the shipment access rule | `app/features/feature_shipment_tool/services/service_find_visible_shipment.py` |
| `be.service_get_shipment_status`, `be.service_get_route_eta`, `be.service_get_customer_sla` | added: mocked APIs with 1 s latency | `app/features/feature_shipment_tool/services/` |
| `ext.operations_apis` | added: mock data boundary | `app/features/feature_shipment_tool/configs/` |
| `be.handle_chat_socket` | changed: binds the tool once per connection and passes it on | `app/features/feature_chat/handlers/handle_chat_socket.py` |
| `be.service_stream_answer` | changed: forwards the tools to the provider | `app/features/feature_chat/services/service_stream_answer.py` |
| `be.service_build_prompt` | changed: rule to call the tool for shipment ids and cite it | `app/features/feature_chat/services/service_build_prompt.py` |
| `be.OpenAIProvider.stream_chat` | changed: streamed tool-call loop | `app/providers/llm/openai_provider.py` |
| `be.GeminiProvider.stream_chat` | changed: chat API with automatic function calling | `app/providers/llm/gemini_provider.py` |
| `be.FakeProvider.stream_chat` | changed: calls the first tool for an id-like token | `app/providers/llm/fake_provider.py` |

`feature_shipment_tool` has no router: it is a tool-provider feature, and `feature_chat` imports only its public entry `tool_bind_shipment_overview` (ICS rule for tool features).

## Run it
No new packages or settings.
```bash
uvicorn app.main:app --reload
```
With `LLM_PROVIDER=fake`, ask "Where is NW-1042?" as the driver: the fake calls the tool and prints its JSON result. A real run with Gemini 2.5 Flash:

> **driver**: *Where is NW-1042 and will Rhine Foods get a credit if it is late?* (4.1 s)
> Shipment NW-1042 is in transit, currently on the A3 near Arnhem (shipment tool). It is estimated to arrive at 14:40, which is 10 minutes past its delivery window of 14:30 (shipment tool). …

> **sales** (`sal-401`): *What is the status of NW-1103?* (1.3 s)
> I cannot find shipment NW-1103 or share its status with you.

## Verify it
```bash
pytest                                                                  # 38 passed, 2 skipped
RUN_LIVE_LLM=1 LIVE_LLM_PROVIDER=gemini GEMINI_API_KEY=... pytest tests/test_llm_live.py
```
`tests/test_shipment_tool.py` proves that the three lookups finish in about 1 s (between 0.9 s and 1.6 s), that each role sees exactly its shipments, that a forbidden and a missing shipment give the same error without any data call, that the model-facing function takes only `shipment_id`, that the socket answers a shipment question through the tool (and refuses another driver's shipment), and that the OpenAI provider assembles a fragmented tool call, runs the tool with the parsed argument and streams the final round (with a stub client, no network). The live test checks that Gemini really calls the tool, quotes the driver's own shipment and does not invent data for a shipment it may not see.

One thing this step does **not** handle yet: if the LLM call fails (no quota, network error), the exception ends the WebSocket. Step 6 fixes that.

## Diagram
Import `role-aware-knowledge-assistant.inkp` from main in Inkplain Simulator (Project → Import Project (.inkp)) and open the `STEP-5` tab to see this step's components.

## Next
Step 6 — Hardening: failures become `error` events while the connection stays open, input limits, logging, a browser test client and the final README.
