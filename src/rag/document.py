"""
Document Processing — PDF loading and text chunking.

Handles the ingestion pipeline: PDF → pages → chunks with metadata.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from src.core.config import get_settings
from src.core.exceptions import DocumentError
from src.core.logger import get_logger

if TYPE_CHECKING:
    from langchain_core.documents import Document

logger = get_logger(__name__)


def load_pdf(file_path: str | Path) -> list[Document]:
    """
    Load a PDF file and return a list of LangChain Documents.

    Each Document contains the text of one page with metadata:
    - source: original filename
    - page: page number (0-indexed)

    Args:
        file_path: Path to the PDF file.

    Returns:
        List of Document objects, one per page.

    Raises:
        DocumentError: If the file cannot be loaded.
    """
    # TODO: Implement in Sprint 1, Day 2
    raise NotImplementedError("PDF loading will be implemented in Day 2")


def chunk_documents(
    docs: list[Document],
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[Document]:
    """
    Split documents into smaller chunks for embedding.

    Uses RecursiveCharacterTextSplitter to preserve semantic boundaries.
    Metadata from parent documents is propagated to all child chunks.

    Args:
        docs: List of documents to chunk.
        chunk_size: Maximum chunk size in characters. Defaults to settings.
        overlap: Overlap between chunks. Defaults to settings.

    Returns:
        List of chunked Document objects with preserved metadata.
    """
    # TODO: Implement in Sprint 1, Day 2
    raise NotImplementedError("Chunking will be implemented in Day 2")
