from unittest.mock import MagicMock, patch

import pytest
from langchain_core.documents import Document
from src.rag.retriever import (
    retrieve_context,
    generate_answer,
    ReRanker,
    retrieve_and_rerank,
    evaluate_reranking_ab,
)

def test_retrieve_context():
    mock_store = MagicMock()
    mock_doc = Document(page_content="test content", metadata={"source": "test.pdf"})
    mock_store.similarity_search.return_value = [mock_doc]

    docs = retrieve_context("test query", mock_store, top_k=1)

    assert len(docs) == 1
    assert docs[0].page_content == "test content"
    mock_store.similarity_search.assert_called_once_with(query="test query", k=1)

def test_generate_answer(mock_llm):
    docs = [
        Document(page_content="Content 1"),
        Document(page_content="Content 2")
    ]

    answer = generate_answer("What is the content?", docs, mock_llm)

    assert answer == "Mock answer"
    # Check that context and query were formatted into the prompt
    assert len(mock_llm.history) == 1
    assert "Content 1" in mock_llm.history[0]
    assert "Content 2" in mock_llm.history[0]
    assert "What is the content?" in mock_llm.history[0]

def test_generate_answer_with_history(mock_llm):
    docs = [Document(page_content="Content")]
    history = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"}
    ]

    answer = generate_answer("Follow up?", docs, mock_llm, history=history)

    assert answer == "Mock answer"
    assert len(mock_llm.history) == 1
    assert "Conversation History:" in mock_llm.history[0]
    assert "User: Hello" in mock_llm.history[0]
    assert "Assistant: Hi there" in mock_llm.history[0]

def test_retrieve_context_error():
    mock_store = MagicMock()
    mock_store.similarity_search.side_effect = Exception("Search error")

    docs = retrieve_context("query", mock_store)

    assert docs == []

def test_generate_answer_error(mock_llm):
    # Make LLM raise exception
    mock_llm.invoke = MagicMock(side_effect=Exception("LLM error"))

    answer = generate_answer("query", [], mock_llm)

    assert answer == "Sorry, an error occurred while generating the answer."


def test_reranker_lazy_loading():
    with (
        patch("sentence_transformers.CrossEncoder") as mock_cross_encoder,
        patch("torch.cuda.is_available", return_value=False),
    ):
        reranker = ReRanker(model_name="test-model")
        assert reranker._model is None

        # Accessing property should trigger loading
        _ = reranker.model
        assert reranker._model is not None
        mock_cross_encoder.assert_called_once_with("test-model", device="cpu")


def test_reranker_rerank():
    reranker = ReRanker(model_name="test-model")
    reranker._model = MagicMock()
    # Mock return values for predict
    reranker._model.predict.return_value = [0.1, 0.9, 0.5]

    docs = [
        Document(page_content="doc1", metadata={"id": 1}),
        Document(page_content="doc2", metadata={"id": 2}),
        Document(page_content="doc3", metadata={"id": 3}),
    ]

    ranked = reranker.rerank("query", docs, top_n=2)

    # Check that they are sorted descending: doc2 (0.9), doc3 (0.5), doc1 (0.1)
    # top_n=2 so doc2 and doc3
    assert len(ranked) == 2
    assert ranked[0].page_content == "doc2"
    assert ranked[0].metadata["rerank_score"] == 0.9
    assert ranked[1].page_content == "doc3"
    assert ranked[1].metadata["rerank_score"] == 0.5


def test_retrieve_and_rerank():
    mock_store = MagicMock()
    mock_reranker = MagicMock()

    mock_docs = [Document(page_content="doc1"), Document(page_content="doc2")]
    mock_store.similarity_search.return_value = mock_docs
    mock_reranker.rerank.return_value = [mock_docs[1]]

    result = retrieve_and_rerank(
        query="query",
        store=mock_store,
        reranker=mock_reranker,
        top_k=5,
        top_n=1
    )

    mock_store.similarity_search.assert_called_once_with(query="query", k=5)
    mock_reranker.rerank.assert_called_once_with("query", mock_docs, top_n=1)
    assert len(result) == 1
    assert result[0].page_content == "doc2"


def test_reranker_score_documents_preserves_order():
    reranker = ReRanker(model_name="test-model")
    reranker._model = MagicMock()
    reranker._model.predict.return_value = [0.2, 0.8]

    docs = [Document(page_content="doc1"), Document(page_content="doc2")]

    scored = reranker.score_documents("query", docs)

    reranker._model.predict.assert_called_once_with([
        ("query", "doc1"),
        ("query", "doc2"),
    ])
    assert scored == [(docs[0], 0.2), (docs[1], 0.8)]


def test_evaluate_reranking_ab_requires_10_queries():
    with pytest.raises(ValueError, match="exactly 10 queries"):
        evaluate_reranking_ab(["q1"], MagicMock(), MagicMock())


def test_evaluate_reranking_ab_measures_improvement_over_10_queries():
    mock_store = MagicMock()
    mock_reranker = MagicMock()
    queries = [f"query {index}" for index in range(10)]
    docs = [
        Document(page_content="semantic first"),
        Document(page_content="best match"),
        Document(page_content="weak match"),
    ]
    mock_store.similarity_search.return_value = docs
    mock_reranker.score_documents.side_effect = [
        [(docs[0], 0.1), (docs[1], 0.9), (docs[2], 0.2)]
        for _ in queries
    ]

    result = evaluate_reranking_ab(
        queries=queries,
        store=mock_store,
        reranker=mock_reranker,
        top_k=3,
        top_n=1,
    )

    assert result.query_count == 10
    assert result.semantic_avg_score == pytest.approx(0.1)
    assert result.reranked_avg_score == pytest.approx(0.9)
    assert result.improvement == pytest.approx(0.8)
    assert result.improved is True
    assert len(result.details) == 10
    assert mock_store.similarity_search.call_count == 10
    mock_store.similarity_search.assert_any_call(query="query 0", k=3)
