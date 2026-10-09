# Splits a page of text into overlapping word windows: the chunks that get embedded and retrieved.
# ICS layer: service (pure computation)
# CRD component: be.service_chunk_text
# Called by: feature_ingest/handlers/handle_ingest_documents.py
# Calls: nothing
# Step: added in step 2 (Ingest tagged chunks)


def service_chunk_text(text: str, size_words: int, overlap_words: int) -> list[str]:
    """Return chunks of at most size_words words, each sharing overlap_words with the previous one.

    text: the text of one page (chunks never cross pages, so every chunk has one page to cite).
    size_words: e.g. 120, roughly one paragraph: big enough to hold a whole rule, small enough to stay on one topic.
    overlap_words: e.g. 30, so a sentence cut at a chunk border still appears whole in one of the two chunks.
    Raises ValueError when overlap_words >= size_words (the window would never move forward).
    """
    if overlap_words >= size_words:
        raise ValueError("overlap_words must be smaller than size_words")
    words = text.split()
    # A short page is a single chunk; an empty page yields none.
    if len(words) <= size_words:
        return [" ".join(words)] if words else []
    chunks = []
    # Each window starts (size - overlap) words after the previous one.
    step = size_words - overlap_words
    for start in range(0, len(words), step):
        chunks.append(" ".join(words[start:start + size_words]))
        # Stop once a window reaches the end; otherwise the tail would repeat as tiny chunks.
        if start + size_words >= len(words):
            break
    return chunks
