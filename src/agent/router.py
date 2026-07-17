"""
Intent Router — Classify and dispatch user queries.

Routes to RAG pipeline (document questions) or direct LLM (general chat).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from src.core.logger import get_logger

if TYPE_CHECKING:
    from src.core.llm_client import LLMProvider

logger = get_logger(__name__)


def classify_intent(
    query: str,
    llm: LLMProvider,
) -> Literal["INTERNAL_DOC", "GENERAL_CHAT"]:
    """
    Classify user query intent.

    Args:
        query: User's question.
        llm: LLM provider for classification.

    Returns:
        "INTERNAL_DOC" for document-related questions,
        "GENERAL_CHAT" for general conversation.
    """
    prompt = f"""You are an intent classification system.
Classify the following user query into one of these two categories:
- INTERNAL_DOC: The query is asking for specific factual information, documentation, company policies, or detailed technical knowledge that requires searching a database.
- GENERAL_CHAT: The query is a simple greeting, general conversation, or a question that can be answered with common knowledge without needing specific documents.

Output EXACTLY one word: either "INTERNAL_DOC" or "GENERAL_CHAT". Do not include any other text, explanation, or punctuation.

User Query: {query}
Intent:"""
    
    try:
        logger.info(f"Classifying intent for query: '{query}'")
        response = llm.invoke(prompt).strip().upper()
        
        # Clean up the response just in case the LLM is chatty
        if "INTERNAL_DOC" in response:
            logger.info("Intent classified as: INTERNAL_DOC")
            return "INTERNAL_DOC"
        else:
            logger.info("Intent classified as: GENERAL_CHAT")
            return "GENERAL_CHAT"
            
    except Exception as e:
        logger.error(f"Failed to classify intent: {e}. Defaulting to INTERNAL_DOC.")
        return "INTERNAL_DOC"



def classify_intent_fast(query: str) -> Literal["INTERNAL_DOC", "GENERAL_CHAT"]:
    """Deterministic low-latency router; defaults substantive questions to RAG."""
    normalized = " ".join(query.strip().lower().split())
    general_prefixes = (
        "xin chào", "chào", "hello", "hi ", "hey", "cảm ơn", "thanks",
        "bạn là ai", "what are you", "how are you",
    )
    if normalized in {"hi", "hello", "hey", "chào", "xin chào"}:
        return "GENERAL_CHAT"
    if any(normalized.startswith(prefix) for prefix in general_prefixes):
        return "GENERAL_CHAT"
    return "INTERNAL_DOC"

def execute_route(
    intent: str,
    query: str,
    rag_chain,
    llm: LLMProvider,
) -> str:
    """
    Dispatch query to the appropriate handler based on intent.

    Args:
        intent: Classified intent ("INTERNAL_DOC" or "GENERAL_CHAT").
        query: User's question.
        rag_chain: RAG pipeline callable.
        llm: LLM provider for direct responses.

    Returns:
        Generated answer string.
    """
    logger.info(f"Executing route for intent: {intent}")
    
    if intent == "INTERNAL_DOC":
        try:
            logger.info("Routing to RAG pipeline...")
            return rag_chain(query)
        except Exception as e:
            logger.error(f"RAG chain failed: {e}")
            return "Sorry, I encountered an error while searching the documents."
    else:
        try:
            logger.info("Routing to general chat (Direct LLM)...")
            system_prompt = "You are a friendly, helpful, and concise AI assistant. Answer the user's general question directly."
            formatted_prompt = f"{system_prompt}\n\nUser: {query}\nAssistant:"
            return llm.invoke(formatted_prompt)
        except Exception as e:
            logger.error(f"General chat LLM failed: {e}")
            return "Sorry, I encountered an error while processing your message."
