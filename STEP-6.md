# Step 6 of 6 — Hardening

## What you build in this step
The production edges. Until step 5, a failing LLM call (quota exhausted, network down) raised through the handler and **killed the WebSocket**; that really happened while building step 5, on Gemini's free-tier limit of 5 requests per minute. Now every question is answered inside one guarded unit: any failure is logged on the server with its details and reaches the user as a single `error` event, and the next question on the same connection works. Questions over a size limit are refused before they cost an embedding or a model call, the server writes a consistent log, and a browser test client lets you try every role.

## What you learn
- Isolating per-message work so one failure cannot end a long-lived connection.
- Separating what the user sees (a generic message) from what the operator sees (the stack trace in the log): provider errors can contain internals.
- Cheap input limits at the edge (`MAX_MESSAGE_CHARS`) before expensive work.
- One logging setup at startup (`LOG_LEVEL`), and logging refused logins without ever logging the token.
- Testing failure paths with a fake that fails once and then recovers.

## What changed since step 5
| Component (STEP-6.crd) | Change | Files |
|---|---|---|
| `be.handle_chat_socket` | changed: length check, each question answered through `_answer` inside try/except, failures logged and sent as `error`, refused logins logged | `app/features/feature_chat/handlers/handle_chat_socket.py` |
| `be.handle_chat_socket._answer` | added: the per-question steps (retrieve, sources, prompt, stream, done) moved into one function that raises on failure | same file |
| `fe.handleConnect`, `fe.handleServerEvent`, `fe.handleSend` | added: browser test client | `test_client.html` |
| everything else | unchanged | |

Also new: `app/core/configure_logging.py` (called once from `app/main.py`), and `MAX_MESSAGE_CHARS`, `LOG_LEVEL` in settings and `.env.example`.

Error events the client can now receive, all with the connection left open:
```
{"type": "error", "message": "invalid message"}                              # not JSON / unknown type
{"type": "error", "message": "message too long (max 2000 characters)"}
{"type": "error", "message": "the answer could not be generated; please try again"}
```

## Run it
```bash
python -m app.features.feature_auth.cli    # tokens for the five demo users
uvicorn app.main:app --reload
```
Open `test_client.html` in a browser, paste a token, connect, and try:
- "What bonus can I earn?" as the driver, then as the leader;
- "What happened in the forklift incident?" as sales, then as safety;
- "Where is NW-1077?" as the driver (refused), then as the dispatcher.

## Verify it
```bash
pytest                      # 41 passed, 3 skipped (OCR and live LLM tests are opt-in)
```
`tests/test_errors.py` proves that a provider exception (a simulated 429) becomes one generic `error` event while its details go to the log, and that the next question on the same connection streams normally; that a too-long message is refused without calling the model; and that non-JSON text and unknown message types get `invalid message` without closing the session.

## Diagram
Import `role-aware-knowledge-assistant.inkp` from main in Inkplain Simulator (Project → Import Project (.inkp)) and open the `STEP-6` tab to see this step's components.

## Next
This is the final version; main has the same code.
