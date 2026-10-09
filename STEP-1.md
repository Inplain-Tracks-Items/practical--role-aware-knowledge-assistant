# Step 1 of 6 — Authenticated WebSocket

## What you build in this step
The skeleton of the Northwind assistant: a FastAPI app with one WebSocket, `/ws/chat`, that refuses to talk to anyone without a valid JWT. The token carries the two facts every later step relies on, the user's **role** and **clearance**. Answers come from a fake LLM that echoes the question, so the whole loop (login, ask, stream, done) runs without any API key.

It comes first because everything after it (which documents you may read, which shipments you may look up) is decided from the identity established here.

## What you learn
- The ICS layout for FastAPI: a door (`router.py`) with no logic, a handler that orchestrates, services that do one job, providers behind an interface.
- Authenticating a WebSocket with a first "auth" message, and why the algorithm is pinned in `jwt.decode`.
- Validating claims with Pydantic `Literal` types, so an unknown role is rejected at the door instead of leaking through retrieval later.
- Dependency injection with `Depends()` and `lru_cache`, and swapping a dependency in tests.
- A streaming protocol: `stream` events followed by `done`.

## What changed since step 0
| Component (STEP-1.crd) | Change | Files |
|---|---|---|
| `be.chat_socket` | added: WebSocket door | `app/features/feature_chat/router.py` |
| `be.handle_chat_socket` | added: accept, auth handshake, message loop | `app/features/feature_chat/handlers/handle_chat_socket.py` |
| `be.verify_jwt` | added: signature, expiry and claim checks | `app/core/verify_jwt.py` |
| `be.service_stream_answer` | added: streams the LLM answer | `app/features/feature_chat/services/service_stream_answer.py` |
| `be.FakeProvider.stream_chat` | added: offline echo LLM | `app/providers/llm/fake_provider.py` |
| `be.get_llm_provider` | added: picks the LLM from `LLM_PROVIDER` | `app/core/dependencies.py` |
| `be.auth_cli`, `be.handle_mint_demo_tokens`, `be.service_mint_token` | added: prints a token per demo user | `app/features/feature_auth/` |
| `ext.pyjwt` | added: JWT library boundary | — |

The access model lives in `app/core/`: `role.py` (driver, dispatcher, safety, sales, leadership), `clearance.py` (public, internal, confidential) and `clearance_ranks.py` (0, 1, 2).

## Run it
```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                 # then set JWT_SECRET to a long random string
python -m app.features.feature_auth.cli   # prints one token per demo user
uvicorn app.main:app --reload        # serves ws://localhost:8000/ws/chat
```

Talk to it from any WebSocket client, for example with the `websockets` package that `uvicorn[standard]` installs:
```bash
python -m websockets ws://localhost:8000/ws/chat
> {"type": "auth", "token": "<paste a token>"}
< {"type": "auth_success", "user_id": "drv-101", "name": "Dana Okafor", "role": "driver", "clearance": "internal"}
> {"type": "message", "text": "hello"}
< {"type": "stream", "text": "Echo: "}
< {"type": "stream", "text": "hello "}
< {"type": "done"}
```

## Verify it
```bash
pytest
```
Six tests pass: a valid token logs in and gets a streamed echo; an expired token, a token signed with another secret, a token with an unknown role and a question sent before auth are all refused; every token the CLI prints verifies back to its user.

## Diagram
Import `role-aware-knowledge-assistant.inkp` from main in Inkplain Simulator (Project → Import Project (.inkp)) and open the `STEP-1` tab to see this step's components. `STEP-1.crd` in this branch is the same system as data.

## Next
Step 2 — Ingest tagged chunks: turn Northwind's PDFs (one of them scanned) into chunks in Chroma, each tagged with who may read it.
