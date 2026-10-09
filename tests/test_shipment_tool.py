# Proves the shipment tool: three lookups run concurrently, visibility follows the user's role, the user is bound
# by the server, and both the fake and the OpenAI provider actually call it.
# ICS layer: test
# Covers: be.tool_get_shipment_overview, be.tool_bind_shipment_overview, be.service_find_visible_shipment,
#         be.FakeProvider.stream_chat, be.OpenAIProvider.stream_chat, be.handle_chat_socket
# Step: added in step 5 (Parallel shipment tools)

import asyncio  # the tool is async
import inspect  # checks what the model can pass to the bound tool
import json  # tool-call arguments in the OpenAI stub
import time  # wall-clock timing of the parallel lookups
from types import SimpleNamespace  # minimal stand-ins for OpenAI stream chunks

import pytest  # parametrize

from app.features.feature_auth.configs.demo_users import DEMO_USERS
from app.features.feature_shipment_tool.tool_bind_shipment_overview import tool_bind_shipment_overview
from app.features.feature_shipment_tool.tool_get_shipment_overview import NOT_VISIBLE, tool_get_shipment_overview
from app.providers.llm.openai_provider import OpenAIProvider


def _user(role: str):
    """The demo user with this role."""
    return next(u for u in DEMO_USERS if u.role == role)


def test_three_lookups_run_concurrently_not_one_after_another():
    # tool_get_shipment_overview: status, ETA and SLA each take ~1 s; gathered they take ~1 s, not ~3 s.
    start = time.perf_counter()
    result = asyncio.run(tool_get_shipment_overview("NW-1042", _user("dispatcher")))
    elapsed = time.perf_counter() - start
    assert 0.9 <= elapsed < 1.6, elapsed
    assert result["status"]["status"] == "in_transit"
    assert result["eta"]["flag"] == "on_time" and result["eta"]["minutes_late"] == 10
    assert result["sla"] == {"tier": "Priority", "window_hours": 2, "credit_percent_if_missed": 10}


@pytest.mark.parametrize("role, visible", [
    ("driver", {"NW-1042", "NW-1103"}),                       # drives these two
    ("sales", {"NW-1042", "NW-1077"}),                        # owns these customers
    ("dispatcher", {"NW-1042", "NW-1077", "NW-1103", "NW-1150"}),
    ("safety", {"NW-1042", "NW-1077", "NW-1103", "NW-1150"}),
    ("leadership", {"NW-1042", "NW-1077", "NW-1103", "NW-1150"}),
])
def test_each_role_sees_exactly_its_shipments(monkeypatch, role, visible):
    # service_find_visible_shipment via the tool: the visibility rule per role. Latency is set to 0 to keep this fast.
    monkeypatch.setattr("app.features.feature_shipment_tool.services.service_get_shipment_status.MOCK_LATENCY_SECONDS", 0)
    monkeypatch.setattr("app.features.feature_shipment_tool.services.service_get_route_eta.MOCK_LATENCY_SECONDS", 0)
    monkeypatch.setattr("app.features.feature_shipment_tool.services.service_get_customer_sla.MOCK_LATENCY_SECONDS", 0)
    seen = {sid for sid in ["NW-1042", "NW-1077", "NW-1103", "NW-1150"]
            if "error" not in asyncio.run(tool_get_shipment_overview(sid, _user(role)))}
    assert seen == visible


def test_forbidden_and_missing_shipments_look_the_same():
    # tool_get_shipment_overview: "not yours" and "does not exist" give the same error, and no data call is made.
    start = time.perf_counter()
    forbidden = asyncio.run(tool_get_shipment_overview("NW-1077", _user("driver")))
    missing = asyncio.run(tool_get_shipment_overview("NW-9999", _user("driver")))
    assert forbidden == missing == {"error": NOT_VISIBLE}
    assert time.perf_counter() - start < 0.5


def test_bound_tool_takes_only_a_shipment_id():
    # tool_bind_shipment_overview: the model-facing function has one parameter; the user cannot be passed in.
    tool = tool_bind_shipment_overview(_user("driver"))
    assert tool.__name__ == "get_shipment_overview"
    assert list(inspect.signature(tool).parameters) == ["shipment_id"]
    assert asyncio.run(tool("NW-1077")) == {"error": NOT_VISIBLE}


def test_socket_answers_a_shipment_question_through_the_tool(indexed, client, token_for):
    # handle_chat_socket + FakeProvider: "NW-1042" in the question makes the fake call the bound tool;
    # the driver gets their shipment, and NW-1077 (another driver's) is refused.
    with client.websocket_connect("/ws/chat") as ws:
        ws.send_json({"type": "auth", "token": token_for("driver")})
        ws.receive_json()
        answers = []
        for question in ["Where is NW-1042?", "Where is NW-1077?"]:
            ws.send_json({"type": "message", "text": question})
            text = ""
            while (event := ws.receive_json())["type"] != "done":
                text += event.get("text", "")
            answers.append(text)
    assert "in_transit" in answers[0] and "Rhine Foods" in answers[0]
    assert NOT_VISIBLE in answers[1] and "Antwerp Steelworks" not in answers[1]


class _StubCompletions:
    """Replays scripted OpenAI stream rounds and records every request."""

    def __init__(self, rounds):
        self.rounds = rounds
        self.requests = []

    async def create(self, **kwargs):
        self.requests.append(kwargs)
        chunks = self.rounds[len(self.requests) - 1]

        async def gen():
            for chunk in chunks:
                yield chunk

        return gen()


def _chunk(content=None, tool_calls=None):
    """One stream chunk with a delta."""
    return SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=content, tool_calls=tool_calls))])


def _tool_part(index, id=None, name=None, arguments=None):
    """One fragment of a streamed tool call."""
    return SimpleNamespace(index=index, id=id, function=SimpleNamespace(name=name, arguments=arguments))


def test_openai_provider_runs_the_requested_tool_and_streams_the_final_answer():
    # OpenAIProvider.stream_chat: round 1 streams a tool call in fragments; the provider runs the tool with the
    # parsed argument, sends the result back as a "tool" message, and streams round 2's text to the user.
    args = json.dumps({"shipment_id": "NW-1042"})
    completions = _StubCompletions([
        [_chunk(tool_calls=[_tool_part(0, id="call_1", name="get_shipment_overview", arguments=args[:10])]),
         _chunk(tool_calls=[_tool_part(0, arguments=args[10:])])],
        [_chunk(content="NW-1042 is "), _chunk(content="in transit (shipment tool).")],
    ])
    provider = OpenAIProvider(api_key="unused", model="test-model", client=SimpleNamespace(chat=SimpleNamespace(completions=completions)))
    calls = []

    async def get_shipment_overview(shipment_id: str) -> dict:
        """Test tool."""
        calls.append(shipment_id)
        return {"status": "in_transit"}

    async def collect():
        return [p async for p in provider.stream_chat("system", "Where is NW-1042?", tools=[get_shipment_overview])]

    assert asyncio.run(collect()) == ["NW-1042 is ", "in transit (shipment tool)."]
    assert calls == ["NW-1042"]
    tool_message = completions.requests[1]["messages"][-1]
    assert tool_message == {"role": "tool", "tool_call_id": "call_1", "content": json.dumps({"status": "in_transit"})}
    assert completions.requests[0]["tools"][0]["function"]["parameters"]["required"] == ["shipment_id"]
