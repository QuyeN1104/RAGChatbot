"""
Embedding Service — Vector representation of text.

Wraps sentence-transformers model for document and query embedding.
"""

from __future__ import annotations

from src.core.logger import get_logger
from src.core.config import get_settings
from src.core.exceptions import EmbeddingError

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
        self.settings = get_settings()
        self.model_name = model_name or self.settings.EMBEDDING_MODEL
        self._embedder = None
        logger.info(f"Initialized EmbeddingService with model: {self.model_name} (lazy loading)")

    @property
    def embedder(self):
        """Lazy-loads the HuggingFaceEmbeddings model."""
        if self._embedder is None:
            import os
            if self.settings.HF_TOKEN:
                os.environ["HF_TOKEN"] = self.settings.HF_TOKEN
                
            from langchain_huggingface import HuggingFaceEmbeddings
            logger.info(f"Loading embedding model: {self.model_name}...")
            
            try:
                self._embedder = HuggingFaceEmbeddings(model_name=self.model_name)
                logger.info("Embedding model loaded successfully on default device.")
            except Exception as e:
                if "CUDA out of memory" in str(e) or "CUDA error" in str(e):
                    logger.warning(f"GPU OOM detected ({e}). Falling back to CPU...")
                    try:
                        import torch
                        if torch.cuda.is_available():
                            torch.cuda.empty_cache()
                            
                        self._embedder = HuggingFaceEmbeddings(
                            model_name=self.model_name, 
                            model_kwargs={'device': 'cpu'}
                        )
                        logger.info("Embedding model loaded successfully on CPU.")
                    except Exception as fallback_err:
                        logger.error(f"Fallback to CPU failed: {fallback_err}")
                        raise EmbeddingError(f"Error loading {self.model_name}: {fallback_err}") from fallback_err
                else:
                    logger.error(f"Failed to load embedding model: {e}")
                    raise EmbeddingError(f"Error loading embedding model {self.model_name}: {e}") from e
                    
        return self._embedder

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Encode a list of document texts into vectors."""
        if not texts:
            return []
        try:
            return self.embedder.embed_documents(texts)
        except Exception as e:
            logger.error(f"Failed to embed documents: {e}")
            raise EmbeddingError(f"Error embedding documents: {e}") from e

    def embed_query(self, text: str) -> list[float]:
        """Encode a single query text into a vector."""
        if not text.strip():
            return []
        try:
            return self.embedder.embed_query(text)
        except Exception as e:
            logger.error(f"Failed to embed query: {e}")
            raise EmbeddingError(f"Error embedding query: {e}") from e


if __name__ == "__main__":
    try:
        service = EmbeddingService()
        sample_texts = ["Đây là câu kiểm tra 1.", "Câu kiểm tra số 2."]
        
        logger.info("Testing embed_documents...")
        vectors = service.embed_documents(sample_texts)
        logger.info(f"Embedded {len(vectors)} documents. Vector length: {len(vectors[0])}")
        
        logger.info("Testing embed_query...")
        q_vector = service.embed_query("Xin chào")
        logger.info(f"Query vector length: {len(q_vector)}")
    except EmbeddingError as e:
        logger.error(f"Embedding test failed: {e}")
