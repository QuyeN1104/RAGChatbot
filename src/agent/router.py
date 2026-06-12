"""
Intent Router — Classify and dispatch user queries.

Routes to RAG pipeline (document questions) or direct LLM (general chat).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from src.core.logger import get_logger

if TYPE_CHECKING:
    from src.core.llm_client import LLMProvider

logger = get_logger(__name__)


def classify_intent(
    query: str,
    llm: LLMProvider,
) -> Literal["INTERNAL_DOC", "GENERAL_CHAT"]:
    """
    Classify user query intent.

    Args:
        query: User's question.
        llm: LLM provider for classification.

    Returns:
        "INTERNAL_DOC" for document-related questions,
        "GENERAL_CHAT" for general conversation.
    """
    # TODO: Implement in Sprint 1, Day 5
    raise NotImplementedError("Intent classification will be implemented in Day 5")


def execute_route(
    intent: str,
    query: str,
    rag_chain,
    llm: LLMProvider,
) -> str:
    """
    Dispatch query to the appropriate handler based on intent.

    Args:
        intent: Classified intent ("INTERNAL_DOC" or "GENERAL_CHAT").
        query: User's question.
        rag_chain: RAG pipeline callable.
        llm: LLM provider for direct responses.

    Returns:
        Generated answer string.
    """
    # TODO: Implement in Sprint 1, Day 5
    raise NotImplementedError("Route execution will be implemented in Day 5")
