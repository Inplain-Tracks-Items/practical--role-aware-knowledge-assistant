# Builds the system prompt for one question: the assistant's rules plus the passages this user may read.
# ICS layer: service (pure computation)
# CRD component: be.service_build_prompt
# Called by: feature_chat/handlers/handle_chat_socket.py
# Calls: nothing
# Step: added in step 4 (Stream answers)

from app.providers.vectorstore.retrieved_chunk import RetrievedChunk  # the allowed passages from step 3

# The rules travel with every request. They keep the model inside the retrieved context,
# make it cite, and stop it from guessing about documents the user cannot see.
SYSTEM_RULES = """You are the internal assistant of Northwind Logistics, a freight carrier.
Answer the user's question using ONLY the passages in CONTEXT.
- Cite every fact with its source in parentheses, exactly as labelled, e.g. (driver_safety_manual.pdf p.1).
- If CONTEXT does not contain the answer, say that you cannot find it in the documents available to this user.
  Do not guess, and do not speculate about other documents that might exist.
- For greetings or small talk, reply briefly without citing anything.
- Keep answers short: a few sentences or a short list."""

# Shown instead of passages when retrieval found nothing the user may read.
NO_CONTEXT = "(no passages from documents available to this user matched the question)"


def service_build_prompt(chunks: list[RetrievedChunk]) -> str:
    """Return SYSTEM_RULES followed by a CONTEXT section.

    chunks: the allowed passages, most relevant first. Each is labelled with the citation the
    model must use, so the citation in the answer always points at a page the user may open.
    """
    # Label every passage with file and page; the label is what the model copies into its citation.
    context = "\n\n".join(f"[{c.source_file} p.{c.page}]\n{c.text}" for c in chunks) if chunks else NO_CONTEXT
    return f"{SYSTEM_RULES}\n\nCONTEXT:\n{context}"
