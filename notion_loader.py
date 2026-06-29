import re
import time
from typing import Optional
from notion_client import Client
from notion_client.errors import APIResponseError

SUPPORTED_BLOCK_TYPES = {
    "paragraph", "heading_1", "heading_2", "heading_3",
    "bulleted_list_item", "numbered_list_item",
    "code", "table", "toggle", "callout",
}

# Map Notion property names → internal field names (LeetCode DB)
PROPERTY_MAP = {
    "Question":  "problem_name",
    "Category":  "topic",
    "Skill":     "difficulty",
    "Progress":  "progress",
    "Notes":     "key_insight",
    "Set Type":  "tags",
}

# Map Notion property names → internal field names (Algorithm Concepts DB)
ALGO_PROPERTY_MAP = {
    "Type":   "topic",
    "Status": "progress",
}


class NotionSyncError(Exception):
    pass


def _retry(fn, page_id, retries=3, delay=2):
    for attempt in range(retries):
        try:
            return fn()
        except APIResponseError as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise NotionSyncError(f"Notion API failed for page {page_id}: {e}")


def _rich_text_to_str(rich_text_list: list) -> str:
    return "".join(item.get("plain_text", "") for item in rich_text_list)


def _block_to_text(block: dict) -> str:
    btype = block.get("type", "")
    if btype not in SUPPORTED_BLOCK_TYPES:
        print(f"[notion_loader] Skipping unsupported block type: {btype}")
        return ""

    data = block.get(btype, {})

    if btype in ("paragraph", "heading_1", "heading_2", "heading_3",
                 "bulleted_list_item", "numbered_list_item", "toggle", "callout"):
        return _rich_text_to_str(data.get("rich_text", []))

    if btype == "code":
        code = _rich_text_to_str(data.get("rich_text", []))
        lang = data.get("language", "")
        return f"```{lang}\n{code}\n```"

    if btype == "table":
        # Table rows are child blocks — handled in _fetch_block_children
        return ""

    return ""


def _fetch_block_children(client: Client, block_id: str) -> str:
    lines = []
    try:
        response = client.blocks.children.list(block_id=block_id)
        blocks = response.get("results", [])
    except APIResponseError:
        return ""

    table_rows = []
    in_table = False

    for block in blocks:
        btype = block.get("type", "")

        if btype == "table_row":
            cells = block.get("table_row", {}).get("cells", [])
            row = " | ".join(_rich_text_to_str(cell) for cell in cells)
            table_rows.append(row)
            in_table = True
            continue

        if in_table:
            lines.append("\n".join(table_rows))
            table_rows = []
            in_table = False

        text = _block_to_text(block)
        if text:
            lines.append(text)

        # Recurse one level for toggles and child pages
        if block.get("has_children") and btype in ("toggle", "bulleted_list_item",
                                                     "numbered_list_item"):
            child_text = _fetch_block_children(client, block["id"])
            if child_text:
                lines.append(child_text)

    if table_rows:
        lines.append("\n".join(table_rows))

    return "\n".join(filter(None, lines))


def _extract_property(prop: dict) -> Optional[str]:
    ptype = prop.get("type")
    if ptype == "title":
        return _rich_text_to_str(prop.get("title", []))
    if ptype == "rich_text":
        return _rich_text_to_str(prop.get("rich_text", []))
    if ptype == "select":
        sel = prop.get("select")
        return sel.get("name") if sel else None
    if ptype == "multi_select":
        return ", ".join(opt["name"] for opt in prop.get("multi_select", []))
    if ptype == "number":
        return prop.get("number")
    if ptype == "status":
        sel = prop.get("status")
        return sel.get("name") if sel else None
    return None


def _parse_problem_id(title: str) -> Optional[int]:
    match = re.search(r"(\d+)\s*$", title.strip())
    return int(match.group(1)) if match else None


def _map_properties(raw_props: dict, prop_map: dict) -> dict:
    result = {}
    for notion_key, internal_key in prop_map.items():
        if notion_key in raw_props:
            result[internal_key] = _extract_property(raw_props[notion_key])
        else:
            result[internal_key] = None
    return result


def load_database(client: Client, database_id: str, db_type: str = "leetcode") -> list[dict]:
    """Fetch all pages from a Notion database and return as structured dicts.

    db_type: "leetcode" or "concept"
    Each dict has: page_id, last_edited_time, type, body_text, + mapped metadata fields.
    """
    pages = []
    cursor = None

    while True:
        kwargs = {"database_id": database_id}
        if cursor:
            kwargs["start_cursor"] = cursor

        def _query():
            return client.databases.query(**kwargs)

        response = _retry(_query, database_id)
        results = response.get("results", [])

        for page in results:
            page_id = page["id"]
            last_edited = page.get("last_edited_time", "")
            raw_props = page.get("properties", {})

            if db_type == "leetcode":
                meta = _map_properties(raw_props, PROPERTY_MAP)
                meta["type"] = "leetcode"
                name = meta.get("problem_name") or ""
                meta["problem_id"] = _parse_problem_id(name)
            else:
                meta = _map_properties(raw_props, ALGO_PROPERTY_MAP)
                meta["type"] = "concept"
                # For concept pages, title is in the "Name" property
                name_prop = raw_props.get("Name") or raw_props.get("Question") or {}
                meta["problem_name"] = _extract_property(name_prop)
                meta["problem_id"] = None

            missing = [k for k, v in meta.items() if v is None and k not in ("problem_id", "tags", "progress")]
            if missing:
                print(f"[notion_loader] Page {page_id} ({meta.get('problem_name', '?')}) "
                      f"missing fields: {missing}")

            def _get_body(pid=page_id):
                return _fetch_block_children(client, pid)

            body_text = _retry(_get_body, page_id)

            pages.append({
                "page_id": page_id,
                "last_edited_time": last_edited,
                "body_text": body_text,
                **meta,
            })

        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")

    return pages


def _discover_databases(client: Client, page_id: str, depth: int = 3) -> list[str]:
    """Find all inline database IDs nested within a page, up to `depth` levels deep."""
    db_ids = []
    try:
        response = client.blocks.children.list(block_id=page_id)
    except APIResponseError:
        return []

    for block in response.get("results", []):
        btype = block.get("type", "")
        if btype == "child_database":
            db_ids.append(block["id"])
        elif btype == "child_page" and depth > 1:
            db_ids.extend(_discover_databases(client, block["id"], depth=depth - 1))

    return db_ids


def _resolve_database_ids(client: Client, entry_id: str) -> list[str]:
    """Return database IDs from an entry point.

    If entry_id is already a database, returns [entry_id].
    If it is a page (inline or parent), discovers databases nested inside it.
    """
    try:
        client.databases.retrieve(database_id=entry_id)
        return [entry_id]  # already a database
    except APIResponseError:
        pass

    # It's a page — discover databases inside it
    db_ids = _discover_databases(client, entry_id, depth=3)
    if not db_ids:
        raise NotionSyncError(
            f"No databases found inside page {entry_id}. "
            "Check that the Notion integration has access to this page."
        )
    return db_ids


def load_all(notion_token: str, leetcode_db_id: Optional[str] = None, concept_db_id: Optional[str] = None) -> list[dict]:
    """Load all pages from both databases.

    Accepts either a direct database ID or a parent page ID (auto-discovers databases inside it).
    At least one of leetcode_db_id or concept_db_id must be set.
    """
    client = Client(auth=notion_token)
    pages = []

    if leetcode_db_id:
        print("[notion_loader] Resolving LeetCode database(s)...")
        lc_ids = _resolve_database_ids(client, leetcode_db_id)
        print(f"[notion_loader] Found {len(lc_ids)} LeetCode database(s).")
        for db_id in lc_ids:
            pages += load_database(client, db_id, db_type="leetcode")

    if concept_db_id:
        print("[notion_loader] Resolving Algorithm Concepts database(s)...")
        concept_ids = _resolve_database_ids(client, concept_db_id)
        print(f"[notion_loader] Found {len(concept_ids)} concept database(s).")
        for db_id in concept_ids:
            pages += load_database(client, db_id, db_type="concept")

    print(f"[notion_loader] Loaded {len(pages)} pages total.")
    return pages
