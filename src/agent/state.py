"""
Agent State — TypedDict for LangGraph state machine.

Defines the shared state passed between nodes in the agent graph.
"""

from __future__ import annotations

from typing import TypedDict


class AgentState(TypedDict, total=False):
    """State shared across LangGraph nodes."""

    # Input
    query: str
    session_id: str

    # Router
    intent: str  # "INTERNAL_DOC" | "GENERAL_CHAT"

    # RAG
    context: list  # list[Document]
    reformulated_query: str

    # Output
    answer: str
    sources: list[dict]  # [{"source": str, "page": int}]

    # Memory
    history: list[dict]  # [{"role": "user"|"assistant", "content": str}]
