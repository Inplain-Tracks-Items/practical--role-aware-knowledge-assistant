# Proves access-aware retrieval: every user only ever gets chunks their role and clearance allow, and the filter runs inside the query.
# ICS layer: test
# Covers: be.util_build_access_filter, be.service_retrieve_chunks, be.ChromaStore.query, be.handle_chat_socket (sources event)
# Step: added in step 3 (Access-aware retrieval)

import asyncio  # the retrieval service is async

import pytest  # parametrize

from app.core.clearance_ranks import CLEARANCE_RANKS
from app.core.dependencies import get_embedder, get_vectorstore
from app.features.feature_auth.configs.demo_users import DEMO_USERS
from app.features.feature_chat.services.service_retrieve_chunks import service_retrieve_chunks
from app.features.feature_chat.utils.util_build_access_filter import util_build_access_filter
from app.features.feature_ingest.configs.access_map import ACCESS_MAP

# Questions that touch every document, including the confidential ones.
QUESTIONS = [
    "What bonus can I earn?",
    "What happened in the forklift serious injury incident at Duisburg?",
    "How long may a driver drive before a break?",
    "What service credit does a customer get for a missed Critical delivery window?",
    "What is the base salary of a director?",
    "How many days of annual leave do I get?",
]


def _user(role: str):
    """The demo user with this role."""
    return next(u for u in DEMO_USERS if u.role == role)


def _retrieve(role: str, question: str, top_k: int = 4):
    """Run the real retrieval service against the indexed test collection."""
    return asyncio.run(service_retrieve_chunks(question, _user(role), get_embedder(), get_vectorstore(), top_k))


def test_filter_puts_role_and_clearance_into_the_query():
    # util_build_access_filter: the driver (internal) may read aud_driver chunks up to rank 1.
    assert util_build_access_filter(_user("driver")) == {"$and": [{"aud_driver": True}, {"clearance_rank": {"$lte": 1}}]}


@pytest.mark.parametrize("user", DEMO_USERS, ids=lambda u: u.role)
def test_no_user_ever_receives_a_chunk_they_may_not_read(indexed, user):
    # service_retrieve_chunks: for every user and every question, each returned chunk's document
    # lists the user's role in its audience and is not more sensitive than the user's clearance.
    for question in QUESTIONS:
        for chunk in _retrieve(user.role, question):
            access = ACCESS_MAP[chunk.source_file]
            assert user.role in access.audience, (user.role, question, chunk.source_file)
            assert CLEARANCE_RANKS[access.clearance] <= CLEARANCE_RANKS[user.clearance], (user.role, question, chunk.source_file)


def test_same_bonus_question_gives_driver_and_leader_different_documents(indexed):
    # The leak naive RAG has: "bonus" matches the leadership plan best. The driver gets the
    # safe-driving bonus instead; the leader does get the compensation plan.
    driver_files = {c.source_file for c in _retrieve("driver", "What bonus can I earn?")}
    leader_files = {c.source_file for c in _retrieve("leadership", "What bonus can I earn?")}
    assert "driver_safety_manual.pdf" in driver_files
    assert "leadership_compensation_plan.pdf" not in driver_files
    assert "leadership_compensation_plan.pdf" in leader_files


def test_scanned_confidential_report_reaches_safety_but_not_sales(indexed):
    # The OCR'd incident review (safety + leadership, confidential) is found by safety and never by sales.
    question = "What happened in the forklift serious injury incident at Duisburg?"
    assert "incident_review_q2.pdf" in {c.source_file for c in _retrieve("safety", question)}
    assert "incident_review_q2.pdf" not in {c.source_file for c in _retrieve("sales", question)}


def test_filter_runs_before_ranking_so_allowed_answers_still_fill_top_k(indexed):
    # Pre-filtering vs post-filtering: the best matches for this question are all in the leadership
    # plan. Filtering afterwards would leave the driver with nothing; filtering in the query
    # still returns top_k allowed chunks.
    chunks = _retrieve("driver", "leadership bonus base salary long-term incentive company car", top_k=3)
    assert len(chunks) == 3
    assert all(c.source_file != "leadership_compensation_plan.pdf" for c in chunks)


def test_socket_sends_only_allowed_sources_before_the_answer(indexed, client, token_for):
    # handle_chat_socket: after a question the first event is "sources", listing allowed pages only.
    with client.websocket_connect("/ws/chat") as ws:
        ws.send_json({"type": "auth", "token": token_for("sales")})
        ws.receive_json()
        ws.send_json({"type": "message", "text": "What bonus can I earn?"})
        event = ws.receive_json()
        assert event["type"] == "sources" and event["sources"]
        for source in event["sources"]:
            assert "sales" in ACCESS_MAP[source["source_file"]].audience
