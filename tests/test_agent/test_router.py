import pytest
from src.agent.router import classify_intent, execute_route
from unittest.mock import MagicMock

def test_classify_intent_internal_doc(mock_llm):
    # Mock LLM to return INTERNAL_DOC
    mock_llm.response = "INTERNAL_DOC"
    
    intent = classify_intent("What does the document say about RAG?", mock_llm)
    
    assert intent == "INTERNAL_DOC"
    assert len(mock_llm.history) == 1
    assert "What does the document say about RAG?" in mock_llm.history[0]

def test_classify_intent_general_chat(mock_llm):
    # Mock LLM to return GENERAL_CHAT
    mock_llm.response = "GENERAL_CHAT"
    
    intent = classify_intent("Hello, how are you?", mock_llm)
    
    assert intent == "GENERAL_CHAT"

def test_classify_intent_fallback(mock_llm):
    # Mock LLM returns garbage, it should fallback or just return the text
    # The actual implementation of classify_intent strips and returns the upper text
    # If the LLM returns "some random text", it will return "SOME RANDOM TEXT"
    # Wait, the current implementation of classify_intent does:
    # return llm.invoke(prompt).strip().upper()
    mock_llm.response = "   internal_doc   "
    
    intent = classify_intent("Query", mock_llm)
    assert intent == "INTERNAL_DOC"

def test_classify_intent_error(mock_llm):
    mock_llm.invoke = MagicMock(side_effect=Exception("LLM error"))
    intent = classify_intent("Query", mock_llm)
    assert intent == "INTERNAL_DOC"

def test_execute_route_internal_doc(mock_llm):
    rag_chain = MagicMock(return_value="RAG answer")
    answer = execute_route("INTERNAL_DOC", "query", rag_chain, mock_llm)
    assert answer == "RAG answer"
    rag_chain.assert_called_once_with("query")

def test_execute_route_internal_doc_error(mock_llm):
    rag_chain = MagicMock(side_effect=Exception("RAG error"))
    answer = execute_route("INTERNAL_DOC", "query", rag_chain, mock_llm)
    assert answer == "Sorry, I encountered an error while searching the documents."

def test_execute_route_general_chat(mock_llm):
    mock_llm.response = "General chat answer"
    rag_chain = MagicMock()
    answer = execute_route("GENERAL_CHAT", "query", rag_chain, mock_llm)
    assert answer == "General chat answer"

def test_execute_route_general_chat_error(mock_llm):
    mock_llm.invoke = MagicMock(side_effect=Exception("LLM error"))
    rag_chain = MagicMock()
    answer = execute_route("GENERAL_CHAT", "query", rag_chain, mock_llm)
    assert answer == "Sorry, I encountered an error while processing your message."
