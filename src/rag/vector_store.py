"""
Vector Store Manager — ChromaDB abstraction layer.

Handles document storage, similarity search, and collection management.
Uses deterministic UUIDs for idempotent upserts.
"""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

from src.core.logger import get_logger
from src.core.config import get_settings
from src.core.exceptions import VectorStoreError
from src.rag.embedding import EmbeddingService

if TYPE_CHECKING:
    from langchain_core.documents import Document

logger = get_logger(__name__)


class VectorStoreManager:
    """
    Abstraction over ChromaDB for vector storage operations.

    Supports lazy initialization and deterministic chunk IDs
    to prevent duplicate insertions on re-ingestion.
    """

    def __init__(self):
        """Initialize the vector store manager."""
        self.settings = get_settings()
        self._vector_store = None
        self._embedding_service = None
        logger.info(f"Initialized VectorStoreManager for collection: {self.settings.CHROMA_COLLECTION}")

    @property
    def embedding_service(self):
        """Lazy-loads the embedding service."""
        if self._embedding_service is None:
            self._embedding_service = EmbeddingService()
        return self._embedding_service

    @property
    def vector_store(self):
        """Lazy-loads the Chroma vector store."""
        if self._vector_store is None:
            try:
                from langchain_chroma import Chroma
                self._vector_store = Chroma(
                    collection_name=self.settings.CHROMA_COLLECTION,
                    embedding_function=self.embedding_service.embedder,
                    persist_directory=self.settings.CHROMA_PERSIST_DIR,
                )
                logger.info(f"Loaded Chroma vector store from {self.settings.CHROMA_PERSIST_DIR}")
            except Exception as e:
                logger.error(f"Failed to load vector store: {e}")
                raise VectorStoreError(f"Error loading vector store: {e}") from e
        return self._vector_store

    def _generate_deterministic_id(self, doc: Document) -> str:
        """Generate a deterministic ID based on document content and source metadata."""
        content = doc.page_content
        source = doc.metadata.get("source", "unknown")
        page = str(doc.metadata.get("page", ""))
        
        unique_string = f"{source}-{page}-{content}"
        return hashlib.sha256(unique_string.encode('utf-8')).hexdigest()

    def add_documents(self, docs: list[Document]) -> list[str]:
        """Add documents to the vector store. Returns list of document IDs."""
        if not docs:
            return []
            
        try:
            ids = [self._generate_deterministic_id(doc) for doc in docs]
            
            self.vector_store.add_documents(documents=docs, ids=ids)
            logger.info(f"Upserted {len(docs)} documents to vector store.")
            return ids
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise VectorStoreError(f"Error adding documents: {e}") from e

    def similarity_search(self, query: str, k: int = 5) -> list[Document]:
        """Search for similar documents given a query string."""
        if not query.strip():
            return []
            
        try:
            results = self.vector_store.similarity_search(query=query, k=k)
            logger.info(f"Found {len(results)} results for query: '{query}'")
            return results
        except Exception as e:
            logger.error(f"Failed to perform similarity search: {e}")
            raise VectorStoreError(f"Error searching vector store: {e}") from e

    def list_documents(self) -> list[str]:
        """List unique document sources in the vector store."""
        try:
            results = self.vector_store.get()
            if not results or not results.get("metadatas"):
                return []
            
            sources = set()
            for meta in results["metadatas"]:
                if meta and "source" in meta:
                    sources.add(meta["source"])
            return sorted(list(sources))
        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            raise VectorStoreError(f"Error listing documents: {e}") from e

    def delete_document(self, source_name: str) -> bool:
        """Delete all chunks associated with a specific document source."""
        try:
            results = self.vector_store.get(where={"source": source_name})
            ids = results.get("ids", [])
            if not ids:
                return False
            
            self.vector_store.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} chunks for document: {source_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            raise VectorStoreError(f"Error deleting document: {e}") from e

    def delete_collection(self) -> None:
        """Delete the entire collection from the vector store."""
        try:
            # Recreate Chroma object without loading it from disk
            from langchain_chroma import Chroma
            import chromadb
            
            client = chromadb.PersistentClient(path=self.settings.CHROMA_PERSIST_DIR)
            try:
                client.delete_collection(self.settings.CHROMA_COLLECTION)
                logger.info(f"Deleted collection: {self.settings.CHROMA_COLLECTION}")
            except Exception as e:
                # If collection doesn't exist, chromadb might raise an exception
                logger.info(f"Collection {self.settings.CHROMA_COLLECTION} could not be deleted or does not exist: {e}")
            
            self._vector_store = None
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
            raise VectorStoreError(f"Error deleting collection: {e}") from e


if __name__ == "__main__":
    from langchain_core.documents import Document
    
    try:
        manager = VectorStoreManager()
        manager.delete_collection()
        
        sample_docs = [
            Document(page_content="AI agents are the future.", metadata={"source": "test.txt", "page": 1}),
            Document(page_content="RAG improves LLM accuracy.", metadata={"source": "test.txt", "page": 2})
        ]
        
        logger.info("Testing add_documents...")
        ids = manager.add_documents(sample_docs)
        logger.info(f"Added docs with IDs: {ids}")
        
        logger.info("Testing idempotent add_documents...")
        ids2 = manager.add_documents(sample_docs)
        logger.info(f"Added again, should have same IDs: {ids == ids2}")
        
        logger.info("Testing similarity_search...")
        results = manager.similarity_search("How to improve LLMs?", k=1)
        if results:
            logger.info(f"Top result: {results[0].page_content}")
            
    except VectorStoreError as e:
        logger.error(f"Vector store test failed: {e}")
