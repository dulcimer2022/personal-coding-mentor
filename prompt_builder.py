from classifier import QueryMode

_NO_SOLUTION = (
    "Never show a complete working implementation. "
    "Provide only a targeted hint that guides the user to discover the fix themselves."
)

_DEBUG_FORMAT = """
Issue: [what is wrong and where in the code]
Root cause: [why it happens]
Hint: [one guiding question or observation — not the fix]
Related: [LeetCode problem IDs or note titles from your history, if any]
""".strip()

_SUMMARY_FORMAT = """
Common pitfalls: [2-3 mistakes you've made repeatedly, from your notes]
Patterns: [recurring problem-solving patterns you struggle with]
Practice problems: [2-3 LeetCode IDs that directly target these weak points, e.g. 206, 141, 21]
Improvements: [one concrete next step]
""".strip()

_PRACTICE_FORMAT = """
Suggested problems: [comma-separated LeetCode IDs only, e.g. 206, 141, 21]
""".strip()


def build_debug(query: str, context: str, retrieval_miss: bool = False) -> str:
    miss_note = (
        "\nNote: No matching notes found in your knowledge base — "
        "hint based on general knowledge.\n"
        if retrieval_miss else ""
    )
    ctx_block = f"\n\nYour relevant notes:\n{context}\n" if context else ""
    return f"""{_NO_SOLUTION}
{miss_note}
You are a coding mentor. The user is debugging their code.
Analyze the issue and respond using EXACTLY this format:

{_DEBUG_FORMAT}

Be precise. Reference the user's notes when relevant.{ctx_block}
User's code/question:
{query}"""


def build_summary(query: str, context: str, retrieval_miss: bool = False) -> str:
    miss_note = (
        "\nNote: No matching notes found for this topic yet.\n"
        if retrieval_miss else ""
    )
    ctx_block = f"\n\nYour notes:\n{context}\n" if context else ""
    return f"""You are a coding mentor reviewing a learner's study notes.

Important context:
- Every note the learner wrote down represents something they struggled with, got wrong, or needed to learn. Treat ALL note content as evidence of past difficulty — not as proof they've mastered it.
- Ignore any "Status" or completion labels in the notes entirely — they are outdated and unreliable.
- If the notes are sparse or missing, say so honestly instead of fabricating insights.
{miss_note}
Extract the actual hard-won lessons from the note content itself. Quote specific lines when possible.

Respond using EXACTLY this format:

{_SUMMARY_FORMAT}
{ctx_block}
User's question:
{query}"""


def build_practice(query: str, context: str, retrieval_miss: bool = False) -> str:
    miss_note = (
        "\nNote: No matching notes found — suggesting from general knowledge.\n"
        if retrieval_miss else ""
    )
    ctx_block = f"\n\nYour relevant notes:\n{context}\n" if context else ""
    return f"""You are a coding mentor suggesting practice problems.
{miss_note}
Respond using EXACTLY this format (IDs only, no explanations):

{_PRACTICE_FORMAT}
{ctx_block}
User's question:
{query}"""


def build_qa(query: str, context: str, retrieval_miss: bool = False) -> str:
    miss_note = (
        "Note: No relevant notes found — answering from general knowledge.\n\n"
        if retrieval_miss else ""
    )
    ctx_block = f"Your relevant notes:\n{context}\n\n" if context else ""
    return f"""You are a coding mentor. Answer concisely in 2-4 sentences, grounded in the notes.
{miss_note}{ctx_block}Question: {query}"""


def build(mode: QueryMode, query: str, hits: list[dict]) -> tuple[str, bool]:
    """Build a prompt for the given mode and retrieved hits.

    Returns (prompt_str, retrieval_miss).
    """
    from retriever import format_context
    miss = len(hits) == 0
    context = format_context(hits)

    if mode == QueryMode.DEBUG:
        return build_debug(query, context, miss), miss
    if mode == QueryMode.SUMMARY:
        return build_summary(query, context, miss), miss
    if mode == QueryMode.PRACTICE:
        return build_practice(query, context, miss), miss
    return build_qa(query, context, miss), miss
