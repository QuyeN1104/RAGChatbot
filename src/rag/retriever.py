"""
Retriever — Semantic search and answer generation.

Two-stage retrieval: semantic search → (optional) re-ranking → LLM generation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.core.logger import get_logger

if TYPE_CHECKING:
    from langchain_core.documents import Document

    from src.core.llm_client import LLMProvider
    from src.rag.vector_store import VectorStoreManager

logger = get_logger(__name__)


def retrieve_context(
    query: str,
    store: VectorStoreManager,
    top_k: int = 5,
) -> list[Document]:
    """
    Retrieve relevant documents for a query via semantic search.

    Args:
        query: User question.
        store: Vector store manager instance.
        top_k: Number of documents to retrieve.

    Returns:
        List of relevant Document objects.
    """
    # TODO: Implement in Sprint 1, Day 4
    raise NotImplementedError("Retriever will be implemented in Day 4")


def generate_answer(
    query: str,
    context: list[Document],
    llm: LLMProvider,
) -> str:
    """
    Generate an answer using retrieved context and LLM.

    Assembles a RAG prompt with context documents and sends to LLM.

    Args:
        query: User question.
        context: Retrieved documents as context.
        llm: LLM provider instance.

    Returns:
        Generated answer string.
    """
    # TODO: Implement in Sprint 1, Day 4
    raise NotImplementedError("Answer generation will be implemented in Day 4")
