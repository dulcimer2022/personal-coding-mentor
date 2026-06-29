from vector_store import similarity_search


def retrieve(query: str, k: int = 3) -> list[dict]:
    """Return relevant chunks for a query.

    Returns list of {text, metadata, score} above the similarity threshold.
    Empty list = retrieval miss; caller handles fallback per mode.
    """
    return similarity_search(query, k=k)


def format_context(hits: list[dict]) -> str:
    """Format retrieved chunks into a prompt-ready context block."""
    if not hits:
        return ""

    parts = []
    for i, hit in enumerate(hits, 1):
        meta = hit["metadata"]
        source = meta.get("problem_name") or meta.get("topic") or "Note"
        insight = meta.get("key_insight") or ""
        header = f"[{i}] {source}"
        if meta.get("difficulty"):
            header += f" ({meta['difficulty']})"
        body = hit["text"]
        if insight and insight not in body:
            body = f"{insight}\n{body}"
        parts.append(f"{header}\n{body}")

    return "\n\n---\n\n".join(parts)
