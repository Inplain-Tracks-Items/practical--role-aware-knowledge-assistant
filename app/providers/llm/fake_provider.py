# An offline LLM provider that echoes the question, so the whole system runs and is testable without an API key.
# ICS layer: provider
# CRD component: be.FakeProvider.stream_chat
# Called by: core/dependencies.py (LLM_PROVIDER=fake), feature_chat/services/service_stream_answer.py
# Calls: nothing external; the first tool it is given, when the question contains an id
# Step: added in step 1 (Authenticated WebSocket); changed in step 5: calls the first tool for an id-like token

import json  # tool results are shown as JSON
import re  # finds id-like tokens such as NW-1042
from typing import Any, AsyncIterator, Callable  # types of the LLMProvider contract

# "Two or more capital letters, a dash, digits": the shape of a record id in the question.
ID_PATTERN = re.compile(r"\b[A-Z]{2,}-\d+\b")


class FakeProvider:
    """Deterministic stand-in for a real model: same interface, predictable output."""

    async def stream_chat(
        self,
        system_prompt: str,
        user_message: str,
        tools: list[Callable[..., Any]] | None = None,
    ) -> AsyncIterator[str]:
        """Stream "Echo: <question>", or the result of the first tool when the question names an id.

        This imitates the one decision a real model makes here (call the tool or not) with a
        fixed rule, so the tool path can be demonstrated and tested offline.
        """
        match = ID_PATTERN.search(user_message)
        if tools and match:
            # Call the tool the way a real provider would: with the argument extracted from the question.
            result = await tools[0](match.group())
            reply = f"{tools[0].__name__}({match.group()}) returned: {json.dumps(result)}"
        else:
            reply = f"Echo: {user_message}"
        # Split the reply into words so the client sees several "stream" events, as with a real model.
        for word in reply.split():
            yield word + " "
