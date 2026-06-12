"""
Embedding Service — Vector representation of text.

Wraps sentence-transformers model for document and query embedding.
"""

from __future__ import annotations

from src.core.logger import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """
    Embedding service using sentence-transformers.

    Lazy-loads the model on first use to avoid GPU allocation at import time.
    """

    def __init__(self, model_name: str | None = None):
        """
        Initialize the embedding service.

        Args:
            model_name: HuggingFace model name. Defaults to settings.EMBEDDING_MODEL.
        """
        # TODO: Implement in Sprint 1, Day 3
        raise NotImplementedError("EmbeddingService will be implemented in Day 3")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Encode a list of document texts into vectors."""
        raise NotImplementedError

    def embed_query(self, text: str) -> list[float]:
        """Encode a single query text into a vector."""
        raise NotImplementedError
