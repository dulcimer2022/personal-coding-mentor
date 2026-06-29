import os
from dotenv import load_dotenv
from typing import Optional
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
COLLECTION_NAME = "coding_mentor"
SIMILARITY_THRESHOLD = 0.35

_embeddings = None
_store = None


def _get_embeddings() -> HuggingFaceEmbeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    return _embeddings


def get_store() -> Chroma:
    global _store
    if _store is None:
        _store = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=_get_embeddings(),
            persist_directory=PERSIST_DIR,
            collection_metadata={"hnsw:space": "cosine"},
        )
    return _store


def ingest_chunks(chunks: list[dict]) -> None:
    """Add chunks to ChromaDB. Each chunk: {text, metadata}."""
    if not chunks:
        return
    store = get_store()
    texts = [c["text"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]
    ids = [f"{m['page_id']}_chunk_{m['chunk_index']}" for m in metadatas]
    store.add_texts(texts=texts, metadatas=metadatas, ids=ids)
    print(f"[vector_store] Ingested {len(chunks)} chunks.")


def delete_page(page_id: str) -> None:
    """Delete all chunks for a given page_id before re-ingesting."""
    store = get_store()
    store.delete(where={"page_id": page_id})


def get_last_edited(page_id: str) -> Optional[str]:
    """Return stored last_edited_time for a page, or None if not found."""
    store = get_store()
    results = store.get(where={"page_id": page_id}, limit=1)
    if results and results.get("metadatas"):
        return results["metadatas"][0].get("last_edited_time")
    return None


def is_empty() -> bool:
    store = get_store()
    return store._collection.count() == 0


def similarity_search(query: str, k: int = 3) -> list[dict]:
    """Return top-k chunks above the similarity threshold.

    Returns list of {text, metadata, score} dicts.
    Empty list if all scores are below SIMILARITY_THRESHOLD (retrieval miss).
    """
    store = get_store()
    results = store.similarity_search_with_relevance_scores(query, k=k)

    hits = []
    for doc, score in results:
        if score >= SIMILARITY_THRESHOLD:
            hits.append({
                "text": doc.page_content,
                "metadata": doc.metadata,
                "score": score,
            })

    if not hits:
        print(f"[vector_store] Retrieval miss — all scores below {SIMILARITY_THRESHOLD}.")
    return hits
