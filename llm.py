import os
from dotenv import load_dotenv
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage
from classifier import QueryMode

load_dotenv()

_MAX_TOKENS = {
    QueryMode.DEBUG:    500,
    QueryMode.SUMMARY:  600,
    QueryMode.PRACTICE: 100,
    QueryMode.QA:       400,
}


def _get_client(mode: QueryMode) -> ChatOpenAI:
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        max_tokens=_MAX_TOKENS[mode],
        api_key=os.getenv("OPENAI_API_KEY"),
    )


def generate(prompt: str, mode: QueryMode, history: Optional[list] = None) -> str:
    """Send prompt to gpt-4o-mini and return the response text.

    history: list of {role: 'user'|'assistant', content: str} for followup context.
    """
    client = _get_client(mode)

    messages = []
    for turn in (history or []):
        if turn["role"] == "user":
            messages.append(HumanMessage(content=turn["content"]))
        else:
            messages.append(AIMessage(content=turn["content"]))
    messages.append(HumanMessage(content=prompt))

    response = client.invoke(messages)
    return response.content.strip()
