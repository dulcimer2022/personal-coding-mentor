import os
from typing import Optional
from dotenv import load_dotenv
from notion_loader import load_all, NotionSyncError
from chunker import chunk_pages
from vector_store import get_last_edited, delete_page, ingest_chunks

load_dotenv()


def sync_notion(
    notion_token: Optional[str] = None,
    leetcode_db_id: Optional[str] = None,
    concept_db_id: Optional[str] = None,
) -> None:
    """Incrementally sync Notion databases to ChromaDB.

    - Pages with a newer last_edited_time are deleted and re-ingested.
    - New pages are ingested.
    - Unchanged pages are skipped.
    """
    token = notion_token or os.getenv("NOTION_TOKEN")
    lc_db = leetcode_db_id or os.getenv("NOTION_LEETCODE_DB_ID") or None
    concept_db = concept_db_id or os.getenv("NOTION_CONCEPT_DB_ID") or None

    if not token:
        raise ValueError("NOTION_TOKEN not set in .env")
    if not lc_db and not concept_db:
        raise ValueError("Set at least one of NOTION_LEETCODE_DB_ID or NOTION_CONCEPT_DB_ID in .env")

    print("[sync] Fetching pages from Notion...")
    pages = load_all(token, lc_db, concept_db)

    new_count = updated_count = skipped_count = 0

    for page in pages:
        page_id = page["page_id"]
        stored_time = get_last_edited(page_id)

        if stored_time is None:
            # New page
            chunks = chunk_pages([page])
            if chunks:
                ingest_chunks(chunks)
                new_count += 1
            else:
                skipped_count += 1

        elif page["last_edited_time"] > stored_time:
            # Updated page — delete old chunks then re-ingest
            delete_page(page_id)
            chunks = chunk_pages([page])
            try:
                if chunks:
                    ingest_chunks(chunks)
            except Exception as e:
                print(f"[sync] WARNING: re-ingestion failed for {page_id}: {e}. "
                      f"Re-run sync to restore.")
            updated_count += 1

        else:
            skipped_count += 1

    print(f"[sync] Done. New: {new_count}, Updated: {updated_count}, "
          f"Skipped (unchanged): {skipped_count}")
