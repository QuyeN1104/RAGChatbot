"""
Agent Graph — LangGraph orchestration for the RAG Chatbot.

This module defines the state machine (nodes and edges) for the chatbot,
connecting memory, intent classification, retrieval, and generation.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from langgraph.graph import END, StateGraph

from src.agent.state import AgentState
from src.agent.router import classify_intent, classify_intent_fast
from src.rag.retriever import retrieve_context, generate_answer
from src.core.config import get_settings
from src.core.logger import get_logger

if TYPE_CHECKING:
    from src.core.llm_client import LLMProvider
    from src.rag.vector_store import VectorStoreManager
    from src.agent.memory import ConversationMemory

logger = get_logger(__name__)


def create_agent_graph(
    llm: LLMProvider,
    vector_store: VectorStoreManager,
    memory: ConversationMemory
):
    """
    Build and compile the LangGraph application.
    
    Args:
        llm: The language model client.
        vector_store: The vector database manager.
        memory: The conversation memory singleton.
        
    Returns:
        A compiled LangGraph app that takes an AgentState.
    """
    settings = get_settings()

    # ==========================
    # NODE DEFINITIONS
    # ==========================

    def reformulate_node(state: AgentState) -> dict:
        """Node: Reformulates the query based on conversation history."""
        logger.info("--- NODE: Reformulate Query ---")
        query = state["query"]
        session_id = state.get("session_id", "default")
        
        history = memory.get_history(session_id, last_n=settings.MEMORY_HISTORY_PAIRS)
        standalone_query = (
            memory.reformulate_query(query, history, llm)
            if settings.ENABLE_LLM_QUERY_REFORMULATION and history
            else query
        )
        
        return {
            "reformulated_query": standalone_query,
            "history": history
        }

    def classify_node(state: AgentState) -> dict:
        """Node: Classifies the intent of the reformulated query."""
        logger.info("--- NODE: Classify Intent ---")
        query = state.get("reformulated_query", state["query"])
        intent = (
            classify_intent(query, llm)
            if settings.ENABLE_LLM_INTENT_CLASSIFICATION
            else classify_intent_fast(query)
        )
        return {"intent": intent}

    def retrieve_node(state: AgentState) -> dict:
        """Node: Retrieves context from the vector store for RAG."""
        logger.info("--- NODE: Retrieve Context ---")
        query = state.get("reformulated_query", state["query"])
        top_k = state.get("top_k", settings.TOP_K)
        docs = retrieve_context(query, vector_store, top_k)
        return {"context": docs}

    def generate_rag_node(state: AgentState) -> dict:
        """Node: Generates an answer using the retrieved context."""
        logger.info("--- NODE: Generate RAG Answer ---")
        query = state.get("reformulated_query", state["query"])
        docs = state.get("context", [])
        history = state.get("history", [])
        
        if not docs:
            return {
                "answer": "Xin lỗi, tôi không tìm thấy thông tin nào liên quan trong tài liệu.",
                "sources": []
            }
            
        answer = generate_answer(query, docs, llm, history)
        
        # Format sources metadata
        source_metadata = []
        for doc in docs:
            source = doc.metadata.get("source", "Unknown")
            page = doc.metadata.get("page", "Unknown")
            source_name = Path(source).name
            source_metadata.append({"source": source_name, "page": page})
            
        return {"answer": answer, "sources": source_metadata}

    def general_chat_node(state: AgentState) -> dict:
        """Node: Generates a direct answer for general chat."""
        logger.info("--- NODE: General Chat ---")
        query = state.get("reformulated_query", state["query"])
        history = state.get("history", [])
        
        system_prompt = "You are a friendly, helpful, and concise AI assistant. Answer the user's general question directly."
        history_str = ""
        if history:
            history_str = "\nConversation History:\n" + "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in history])
            
        formatted_prompt = f"{system_prompt}{history_str}\n\nUser: {query}\nAssistant:"
        answer = llm.invoke(formatted_prompt).strip()
        
        return {"answer": answer, "sources": []}

    def memory_save_node(state: AgentState) -> dict:
        """Node: Saves the final answer to the conversation memory."""
        logger.info("--- NODE: Save to Memory ---")
        query = state["query"]  # Save original query, not reformulated
        answer = state.get("answer", "")
        session_id = state.get("session_id", "default")
        
        memory.add(query, answer, session_id)
        return {}

    # ==========================
    # CONDITIONAL EDGES
    # ==========================

    def route_intent(state: AgentState) -> str:
        """Route to RAG or General Chat based on intent."""
        intent = state.get("intent", "GENERAL_CHAT")
        if intent == "INTERNAL_DOC":
            return "retrieve"
        return "general_chat"

    # ==========================
    # GRAPH ASSEMBLY
    # ==========================
    
    workflow = StateGraph(AgentState)

    # Add Nodes
    workflow.add_node("reformulate", reformulate_node)
    workflow.add_node("classify", classify_node)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("generate_rag", generate_rag_node)
    workflow.add_node("general_chat", general_chat_node)
    workflow.add_node("memory_save", memory_save_node)

    # Set Entry Point
    workflow.set_entry_point("reformulate")

    # Add Edges
    workflow.add_edge("reformulate", "classify")
    
    workflow.add_conditional_edges(
        "classify",
        route_intent,
        {
            "retrieve": "retrieve",
            "general_chat": "general_chat"
        }
    )
    
    workflow.add_edge("retrieve", "generate_rag")
    workflow.add_edge("generate_rag", "memory_save")
    workflow.add_edge("general_chat", "memory_save")
    workflow.add_edge("memory_save", END)

    return workflow.compile()
