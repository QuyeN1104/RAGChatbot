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
    try:
        from langchain_community.document_loaders import PyPDFLoader
        
        path_str = str(file_path)
        path_obj = Path(path_str)
        
        if not path_obj.exists() or not path_obj.is_file():
            raise FileNotFoundError(f"File not found: {path_str}")

        logger.info(f"Loading PDF file: {path_str}")
        loader = PyPDFLoader(path_str)
        docs = loader.load()
        logger.info(f"Successfully loaded {len(docs)} pages from {path_str}")
        
        return docs
    except Exception as e:
        logger.error(f"Failed to load PDF: {e}")
        raise DocumentError(f"Cannot load PDF file '{file_path}': {e}") from e


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
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        
        settings = get_settings()
        final_chunk_size = chunk_size if chunk_size is not None else settings.CHUNK_SIZE
        final_overlap = overlap if overlap is not None else settings.CHUNK_OVERLAP
        
        logger.info(f"Chunking {len(docs)} documents with size={final_chunk_size}, overlap={final_overlap}")
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=final_chunk_size,
            chunk_overlap=final_overlap,
            length_function=len,
        )
        
        # split_documents automatically propagates the metadata from the parent docs to the chunks
        chunked_docs = text_splitter.split_documents(docs)
        logger.info(f"Successfully generated {len(chunked_docs)} chunks from {len(docs)} pages.")
        
        return chunked_docs
    except Exception as e:
        logger.error(f"Failed to chunk documents: {e}")
        raise DocumentError(f"Error during chunking: {e}") from e


if __name__ == "__main__":  # pragma: no cover
    try:
        logger = get_logger(__name__)
        docs = load_pdf("data/raw_pdfs/example.pdf")
        
        chunks = chunk_documents(docs)
        
        logger.info(f"Loaded {len(docs)} pages.")
        logger.info(f"Chunked into {len(chunks)} smaller pieces.")
        
        # In ra thử chunk đầu tiên để kiểm tra metadata
        if chunks:
            logger.info("Sample First Chunk:")
            logger.info(f"Metadata: {chunks[0].metadata}")
            logger.info(f"Content snippet: {chunks[0].page_content[:200]}...")
            
    except DocumentError as e:
        logger.error(f"Document error: {e}")