#!/usr/bin/env python3
import sys
import warnings
warnings.filterwarnings("ignore")

from dotenv import load_dotenv
load_dotenv()

_FOLLOWUP_KEYWORDS = {"why", "how", "can you", "what about", "explain", "example",
                      "provide", "give", "show", "more", "elaborate", "clarify"}

def _is_followup(query: str, last_response: str) -> bool:
    """True if this looks like a followup to the previous answer."""
    if not last_response:
        return False
    q = query.lower().strip()
    # Short queries (under 6 words) that start with a followup keyword
    words = q.split()
    if len(words) <= 6 and any(q.startswith(kw) for kw in _FOLLOWUP_KEYWORDS):
        return True
    return False


def _run_query(query: str, history=None) -> str:
    from vector_store import is_empty
    from classifier import classify
    from retriever import retrieve
    from prompt_builder import build
    from llm import generate

    if is_empty():
        print("No notes loaded. Run: python mentor.py sync")
        sys.exit(1)

    mode = classify(query)
    print(f"[{mode.value}]")

    hits = retrieve(query)
    prompt, miss = build(mode, query, hits)
    response = generate(prompt, mode, history=history)
    print(response)
    return response


def _run_sync() -> None:
    from sync import sync_notion
    sync_notion()


def _collect_debug() -> str:
    """Collect multi-line code for debug mode."""
    print("Paste your code. Type END on a new line when done:")
    lines = []
    while True:
        try:
            line = input("> ")
        except (EOFError, KeyboardInterrupt):
            break
        if line.strip() == "END":
            break
        lines.append(line)
    code = "\n".join(lines)
    try:
        context = input("What's the issue? (press Enter to skip): ").strip()
    except (EOFError, KeyboardInterrupt):
        context = ""
    question = context if context else "Why is my code wrong?"
    return f"{question}\n```\n{code}\n```"


def _repl() -> None:
    from vector_store import is_empty
    if is_empty():
        print("No notes loaded. Run: python mentor.py sync")
        sys.exit(1)

    print("Mentor ready. Commands: 'debug' to paste code, 'sync' to reload notes, 'quit' to exit.\n")

    history: list[dict] = []
    last_response = ""

    while True:
        try:
            query = input("you: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not query:
            continue
        if query.lower() in ("quit", "exit", "q"):
            break
        if query.lower() == "sync":
            _run_sync()
            print()
            history = []
            last_response = ""
            continue
        if query.lower() == "debug":
            query = _collect_debug()

        if _is_followup(query, last_response):
            ctx_history = history[-4:]  # last 2 turns
        else:
            ctx_history = []
            history = []

        response = _run_query(query, history=ctx_history)
        history.append({"role": "user", "content": query})
        history.append({"role": "assistant", "content": response})
        last_response = response
        print()


def main():
    args = sys.argv[1:]

    if not args:
        _repl()
    elif args[0] == "sync":
        _run_sync()
    else:
        query = " ".join(args)
        _run_query(query)


if __name__ == "__main__":
    main()
