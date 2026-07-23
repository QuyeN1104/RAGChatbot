from unittest.mock import MagicMock

from langchain_core.documents import Document

from src.agent.graph import create_agent_graph


def test_general_mode_skips_retrieval(mock_llm):
    store = MagicMock()
    memory = MagicMock()
    memory.get_history.return_value = []
    graph = create_agent_graph(mock_llm, store, memory)

    result = graph.invoke({"query": "Hello", "session_id": "general", "mode": "general"})

    assert result["answer"] == "Mock answer"
    assert result["sources"] == []
    store.similarity_search.assert_not_called()
    memory.add.assert_called_once_with("Hello", "Mock answer", "general")


def test_rag_mode_retrieves_documents(mock_llm):
    store = MagicMock()
    store.similarity_search.return_value = [
        Document(page_content="RAG context", metadata={"source": "/tmp/guide.pdf", "page": 3})
    ]
    memory = MagicMock()
    memory.get_history.return_value = []
    graph = create_agent_graph(mock_llm, store, memory)

    result = graph.invoke({"query": "Summarize", "session_id": "rag", "mode": "rag", "top_k": 2})

    store.similarity_search.assert_called_once_with(query="Summarize", k=2)
    assert result["sources"] == [{"source": "guide.pdf", "page": 3}]
    memory.add.assert_called_once_with("Summarize", "Mock answer", "rag")
