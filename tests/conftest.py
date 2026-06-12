"""Shared test fixtures for the RAG system."""

import pytest


@pytest.fixture
def sample_text() -> str:
    """Sample text for testing document processing."""
    return (
        "Retrieval-Augmented Generation (RAG) is a technique that combines "
        "information retrieval with text generation. It first retrieves relevant "
        "documents from a knowledge base, then uses them as context for the LLM "
        "to generate accurate answers."
    )


@pytest.fixture
def settings():
    """Test settings with overrides for testing."""
    from src.core.config import Settings

    return Settings(
        OLLAMA_BASE_URL="http://localhost:11434",
        OLLAMA_MODEL="llama3",
        CHROMA_PERSIST_DIR="./data/test_vector_db",
        CHROMA_COLLECTION="test_documents",
        LOG_LEVEL="DEBUG",
    )
