import pytest
from unittest.mock import patch, MagicMock
from langchain_core.documents import Document
from src.rag.document import load_pdf, chunk_documents, DocumentError

def test_load_pdf(test_pdf):
    """Test loading a PDF file into Document objects."""
    docs = load_pdf(test_pdf)
    assert len(docs) > 0
    assert isinstance(docs[0], Document)
    assert "This is a test document" in docs[0].page_content

def test_load_pdf_invalid_path():
    """Test loading from an invalid path."""
    with pytest.raises(DocumentError):
        load_pdf("non_existent_file.pdf")

def test_chunk_documents():
    """Test chunking documents."""
    doc1 = Document(page_content="A" * 1000, metadata={"source": "test.pdf", "page": 1})
    chunks = chunk_documents([doc1])
    
    assert len(chunks) > 1
    assert chunks[0].metadata["source"] == "test.pdf"
    assert chunks[0].metadata["page"] == 1
    # Check that chunks are not too large
    for chunk in chunks:
        assert len(chunk.page_content) <= 550 # roughly CHUNK_SIZE

def test_chunk_documents_error():
    with patch("langchain_text_splitters.RecursiveCharacterTextSplitter") as mock:
        mock.side_effect = Exception("Chunking failed")
        doc1 = Document(page_content="A" * 1000, metadata={"source": "test.pdf", "page": 1})
        with pytest.raises(DocumentError, match="Chunking failed"):
            chunk_documents([doc1])
