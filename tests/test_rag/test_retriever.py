import pytest
from unittest.mock import MagicMock
from langchain_core.documents import Document
from src.rag.retriever import retrieve_context, generate_answer

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
