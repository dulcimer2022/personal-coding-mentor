from typing import Optional, Union
from langchain.text_splitter import RecursiveCharacterTextSplitter

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", " ", ""],
)

# Fields carried through as ChromaDB metadata (must be str/int/float/bool)
METADATA_FIELDS = [
    "page_id", "last_edited_time", "problem_name", "problem_id",
    "topic", "difficulty", "progress", "key_insight", "tags", "type",
]


def _sanitize(value) -> Optional[Union[str, int, float, bool]]:
    if value is None:
        return None
    if isinstance(value, (int, float, bool)):
        return value
    return str(value)[:1000]  # ChromaDB metadata values have a size limit


def chunk_pages(pages: list[dict]) -> list[dict]:
    """Split pages into chunks with metadata. Returns list of {text, metadata} dicts."""
    chunks = []

    for page in pages:
        # Combine inline Notes/key_insight with body text for richer context
        key_insight = page.get("key_insight") or ""
        body = page.get("body_text") or ""
        full_text = f"{key_insight}\n\n{body}".strip() if key_insight else body

        if not full_text.strip():
            print(f"[chunker] Page {page['page_id']} ({page.get('problem_name', '?')}) "
                  f"has no text content — skipping.")
            continue

        meta = {field: _sanitize(page.get(field)) for field in METADATA_FIELDS}

        splits = _splitter.split_text(full_text)
        for i, chunk_text in enumerate(splits):
            chunks.append({
                "text": chunk_text,
                "metadata": {**meta, "chunk_index": i},
            })

    print(f"[chunker] Produced {len(chunks)} chunks from {len(pages)} pages.")
    return chunks
