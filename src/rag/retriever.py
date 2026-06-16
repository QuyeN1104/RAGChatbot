"""
Retriever — Semantic search and answer generation.

Two-stage retrieval: semantic search → (optional) re-ranking → LLM generation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.core.logger import get_logger

if TYPE_CHECKING:
    from langchain_core.documents import Document

    from src.core.llm_client import LLMProvider
    from src.rag.vector_store import VectorStoreManager

logger = get_logger(__name__)


def retrieve_context(
    query: str,
    store: VectorStoreManager,
    top_k: int = 5,
) -> list[Document]:
    """
    Retrieve relevant documents for a query via semantic search.

    Args:
        query: User question.
        store: Vector store manager instance.
        top_k: Number of documents to retrieve.

    Returns:
        List of relevant Document objects.
    """
    try:
        logger.info(f"Retrieving top {top_k} contexts for query: '{query}'")
        return store.similarity_search(query=query, k=top_k)
    except Exception as e:
        logger.error(f"Failed to retrieve context: {e}")
        return []


def generate_answer(
    query: str,
    context: list[Document],
    llm: LLMProvider,
) -> str:
    """
    Generate an answer using retrieved context and LLM.

    Assembles a RAG prompt with context documents and sends to LLM.

    Args:
        query: User question.
        context: Retrieved documents as context.
        llm: LLM provider instance.

    Returns:
        Generated answer string.
    """
    prompt_template = """You are a helpful AI assistant. Use the following pieces of retrieved context to answer the user's question.
If you don't know the answer based on the context, just say that you don't know, don't try to make up an answer.

Context:
{context}

Question: {query}

Answer:"""

    # Combine document contents into a single string
    context_text = "\n\n---\n\n".join([doc.page_content for doc in context])
    
    # Format the prompt
    formatted_prompt = prompt_template.format(context=context_text, query=query)
    
    try:
        logger.info("Generating answer using LLM...")
        return llm.invoke(formatted_prompt)
    except Exception as e:
        logger.error(f"Failed to generate answer: {e}")
        return "Sorry, an error occurred while generating the answer."


if __name__ == "__main__":
    from langchain_core.documents import Document

    from src.core.llm_client import create_llm_client
    from src.rag.vector_store import VectorStoreManager

    try:
        logger.info("--- Testing Retriever ---")
        
        # 1. Initialize Vector Store
        store = VectorStoreManager()
        
        # Add some sample documents for testing
        test_docs = [
            Document(
                page_content="RAG (Retrieval-Augmented Generation) combines search with language models.",
                metadata={"source": "test_1"}
            ),
            Document(
                page_content="LangChain is a powerful framework for building applications with LLMs.",
                metadata={"source": "test_2"}
            )
        ]
        store.add_documents(test_docs)
        
        # 2. Test Context Retrieval
        test_query = "What is RAG?"
        retrieved_docs = retrieve_context(test_query, store, top_k=1)
        
        if retrieved_docs:
            logger.info(f"Top retrieved context: {retrieved_docs[0].page_content}")
        else:
            logger.warning("No documents retrieved.")
            
        # 3. Test Answer Generation
        # Note: You can change 'ollama' to 'groq' or 'openai' if you have the API keys configured in .env
        logger.info("Initializing LLM (ollama)...")
        test_llm = create_llm_client("ollama")
        
        answer = generate_answer(test_query, retrieved_docs, test_llm)
        logger.info(f"Generated Answer:\n{answer}")

    except Exception as e:
        logger.error(f"Retriever test failed: {e}")
