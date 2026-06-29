import re
from enum import Enum


class QueryMode(Enum):
    DEBUG = "debug"
    SUMMARY = "summary"
    PRACTICE = "practice"
    QA = "qa"


_CODE_BLOCK_RE = re.compile(r"```[\s\S]+?```")
_INDENTED_RE = re.compile(r"^( {4}|\t).+", re.MULTILINE)

_SUMMARY_KEYWORDS = {"summarize", "pitfall", "mistake", "my mistakes",
                     "patterns", "weak spots", "common errors", "review"}
_PRACTICE_KEYWORDS = {"practice", "problems", "questions", "topic",
                      "leetcode", "suggest", "drill", "exercise"}


def _has_code(text: str) -> bool:
    if _CODE_BLOCK_RE.search(text):
        return True
    indented = _INDENTED_RE.findall(text)
    return len(indented) >= 2


def classify(query: str) -> QueryMode:
    """Classify a query into DEBUG, SUMMARY, PRACTICE, or QA.

    Priority order: code detection > summary keywords > practice keywords > QA.
    """
    if _has_code(query):
        return QueryMode.DEBUG

    lower = query.lower()
    if any(kw in lower for kw in _SUMMARY_KEYWORDS):
        return QueryMode.SUMMARY

    if any(kw in lower for kw in _PRACTICE_KEYWORDS):
        return QueryMode.PRACTICE

    return QueryMode.QA
