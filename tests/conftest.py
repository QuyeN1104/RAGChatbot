"""Shared test fixtures for the RAG system."""

import pytest
import os
import tempfile
from fpdf import FPDF
from src.core.llm_client import LLMProvider


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


class MockLLM(LLMProvider):
    def __init__(self, response="This is a mock response"):
        self.response = response
        self.history = []

    def invoke(self, prompt: str) -> str:
        self.history.append(prompt)
        return self.response

    def stream(self, prompt: str):
        self.history.append(prompt)
        for chunk in self.response.split():
            yield chunk + " "


@pytest.fixture
def mock_llm():
    """Returns a mock LLM for testing."""
    return MockLLM(response="Mock answer")


@pytest.fixture
def test_pdf():
    """Creates a temporary PDF file for testing and yields its path."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="This is a test document for RAG.", ln=1, align="C")
    pdf.cell(200, 10, txt="It contains some useful information about testing.", ln=2, align="C")
    
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        pdf_path = tmp.name
        
    pdf.output(pdf_path)
    
    yield pdf_path
    
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
