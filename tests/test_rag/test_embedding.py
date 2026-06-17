import pytest
from unittest.mock import patch, MagicMock
from src.rag.embedding import EmbeddingService, EmbeddingError

@pytest.fixture
def mock_hf_embeddings():
    with patch("langchain_huggingface.HuggingFaceEmbeddings") as mock:
        mock_instance = MagicMock()
        mock_instance.embed_documents.return_value = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        mock_instance.embed_query.return_value = [0.1, 0.2, 0.3]
        mock.return_value = mock_instance
        yield mock

def test_embedding_service_init():
    service = EmbeddingService()
    assert service._embedder is None
    assert service.model_name is not None

def test_embedding_service_lazy_load(mock_hf_embeddings):
    service = EmbeddingService()
    embedder = service.embedder
    assert embedder is not None
    mock_hf_embeddings.assert_called_once()

def test_embed_documents(mock_hf_embeddings):
    service = EmbeddingService()
    texts = ["hello", "world"]
    embeddings = service.embed_documents(texts)
    
    assert len(embeddings) == 2
    assert len(embeddings[0]) == 3
    mock_hf_embeddings.return_value.embed_documents.assert_called_once_with(texts)

def test_embed_query(mock_hf_embeddings):
    service = EmbeddingService()
    embedding = service.embed_query("hello")
    
    assert len(embedding) == 3
    mock_hf_embeddings.return_value.embed_query.assert_called_once_with("hello")

def test_embedding_service_fallback():
    with patch("langchain_huggingface.HuggingFaceEmbeddings") as mock_hf:
        # Simulate CUDA OOM on first try
        mock_hf.side_effect = [Exception("CUDA out of memory"), MagicMock()]
        
        service = EmbeddingService()
        embedder = service.embedder
        
        assert embedder is not None
        assert mock_hf.call_count == 2
        
        # Second call should be with cpu
        args, kwargs = mock_hf.call_args
        assert kwargs.get("model_kwargs") == {"device": "cpu"}

def test_embed_documents_empty():
    service = EmbeddingService()
    assert service.embed_documents([]) == []

def test_embed_query_empty():
    service = EmbeddingService()
    assert service.embed_query("  ") == []

def test_embed_documents_error(mock_hf_embeddings):
    service = EmbeddingService()
    mock_hf_embeddings.return_value.embed_documents.side_effect = Exception("Test error")
    with pytest.raises(EmbeddingError, match="Test error"):
        service.embed_documents(["hello"])

def test_embed_query_error(mock_hf_embeddings):
    service = EmbeddingService()
    mock_hf_embeddings.return_value.embed_query.side_effect = Exception("Test error")
    with pytest.raises(EmbeddingError, match="Test error"):
        service.embed_query("hello")

def test_embedding_service_fallback_error():
    with patch("langchain_huggingface.HuggingFaceEmbeddings") as mock_hf:
        # Simulate CUDA OOM on first try, then CPU fallback also fails
        mock_hf.side_effect = [Exception("CUDA out of memory"), Exception("CPU fallback failed")]
        
        service = EmbeddingService()
        with pytest.raises(EmbeddingError, match="CPU fallback failed"):
            _ = service.embedder
