# A tiny offline embedder: hashes words into a fixed-size vector. No model download; used by tests and quick demos.
# ICS layer: provider
# CRD component: be.HashingProvider.embed_documents
# Called by: core/dependencies.py (EMBEDDING_PROVIDER=hashing), tests
# Calls: nothing external
# Step: added in step 2 (Ingest tagged chunks)

import hashlib  # stable hash of a word -> the same vector slot on every run and machine
import math  # vector length for normalisation
import re  # splits text into lowercase words

# Words too common to say anything about a passage; leaving them out makes similarity
# depend on the meaningful words ("bonus", "forklift"), like a real model would.
STOPWORDS = {"the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "is", "are", "be", "with", "by", "at", "it", "this", "that", "as", "from", "what", "how", "my", "i", "do", "does", "who", "per"}


class HashingProvider:
    """Bag-of-words vectors: two texts are close when they share words.

    Not semantic (it does not know "pay" and "salary" are related) but deterministic
    and instant, which is exactly what tests of the access rules need.
    """

    def __init__(self, dimensions: int = 512) -> None:
        """dimensions: vector size; larger means fewer words share a slot."""
        self._dimensions = dimensions

    def _embed(self, text: str) -> list[float]:
        """Count each non-stopword in its hashed slot, then scale the vector to length 1."""
        vector = [0.0] * self._dimensions
        # Lowercase words only, so "Bonus" and "bonus" land in the same slot.
        for word in re.findall(r"[a-z0-9]+", text.lower()):
            if word in STOPWORDS:
                continue
            # md5 is used as a stable spreader here, not for security.
            slot = int(hashlib.md5(word.encode()).hexdigest(), 16) % self._dimensions
            vector[slot] += 1.0
        # Normalise so cosine distance compares word mix, not text length.
        length = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / length for v in vector]

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """One hashed vector per passage; pure CPU and fast, so no thread is needed."""
        return [self._embed(text) for text in texts]

    async def embed_query(self, text: str) -> list[float]:
        """Queries are hashed exactly like passages."""
        return self._embed(text)
