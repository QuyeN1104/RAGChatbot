"""
Custom Exception Hierarchy — Centralized error handling.

All custom exceptions inherit from RAGException for easy catching.
"""


class RAGException(Exception):
    """Base exception for the RAG system."""

    def __init__(self, message: str = "An error occurred in the RAG system"):
        self.message = message
        super().__init__(self.message)


# --- Layer 1: Core ---

class LLMConnectionError(RAGException):
    """Raised when LLM provider is unreachable or misconfigured."""

    def __init__(self, message: str = "Failed to connect to LLM provider"):
        super().__init__(message)


class ConfigurationError(RAGException):
    """Raised when environment configuration is invalid."""

    def __init__(self, message: str = "Invalid configuration"):
        super().__init__(message)


# --- Layer 2: RAG Pipeline ---

class DocumentError(RAGException):
    """Raised when document loading or processing fails."""

    def __init__(self, message: str = "Document processing error"):
        super().__init__(message)


class EmbeddingError(RAGException):
    """Raised when embedding generation fails."""

    def __init__(self, message: str = "Embedding generation error"):
        super().__init__(message)


class VectorStoreError(RAGException):
    """Raised when vector store operations fail."""

    def __init__(self, message: str = "Vector store error"):
        super().__init__(message)


class RetrievalError(RAGException):
    """Raised when document retrieval fails."""

    def __init__(self, message: str = "Retrieval error"):
        super().__init__(message)


# --- Layer 3: Agent ---

class RoutingError(RAGException):
    """Raised when intent classification or routing fails."""

    def __init__(self, message: str = "Routing error"):
        super().__init__(message)
