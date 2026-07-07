"""
Retriever — Semantic search and answer generation.

Two-stage retrieval: semantic search → (optional) re-ranking → LLM generation.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from statistics import mean
from typing import TYPE_CHECKING

from src.core.logger import get_logger

if TYPE_CHECKING:
    from langchain_core.documents import Document

    from src.core.llm_client import LLMProvider
    from src.rag.vector_store import VectorStoreManager

logger = get_logger(__name__)


@dataclass(frozen=True)
class RetrievalABResult:
    """A/B summary for semantic search vs semantic search plus reranking."""

    query_count: int
    semantic_avg_score: float
    reranked_avg_score: float
    improvement: float
    details: list[dict[str, object]]

    @property
    def improved(self) -> bool:
        """Whether reranking improved average cross-encoder relevance."""
        return self.improvement > 0


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
    history: list[dict] = None
) -> str:
    """
    Generate an answer using retrieved context, history and LLM.

    Assembles a RAG prompt with context documents and sends to LLM.

    Args:
        query: User question.
        context: Retrieved documents as context.
        llm: LLM provider instance.
        history: Optional list of previous conversation turns.

    Returns:
        Generated answer string.
    """
    prompt_template = """You are a helpful AI assistant. Use the following pieces of retrieved context and conversation history to answer the user's question.
If you don't know the answer based on the context, just say that you don't know, don't try to make up an answer.

Context:
{context}

Conversation History:
{history_str}

Question: {query}

Answer:"""

    # Combine document contents into a single string
    context_text = "\n\n---\n\n".join([doc.page_content for doc in context])
    
    # Format history
    history_str = ""
    if history:
        history_str = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in history])
    
    # Format the prompt
    formatted_prompt = prompt_template.format(context=context_text, history_str=history_str, query=query)
    
    try:
        logger.info("Generating answer using LLM...")
        return llm.invoke(formatted_prompt)
    except Exception as e:
        logger.error(f"Failed to generate answer: {e}")
        return "Sorry, an error occurred while generating the answer."


class ReRanker:
    """
    Reranker service using the BAAI/bge-reranker-v2-m3 cross-encoder.
    
    Lazy-loads the model on first use.
    """
    def __init__(self, model_name: str | None = None):
        """
        Initialize the ReRanker service.

        Args:
            model_name: HuggingFace model name. Defaults to settings.RERANKER_MODEL.
        """
        from src.core.config import get_settings
        self.settings = get_settings()
        self.model_name = model_name or getattr(self.settings, "RERANKER_MODEL", "BAAI/bge-reranker-v2-m3")
        self._model = None
        logger.info(f"Initialized ReRanker with model: {self.model_name} (lazy loading)")

    @property
    def model(self):
        """Lazy-loads the CrossEncoder model."""
        if self._model is None:
            import os
            if getattr(self.settings, "HF_TOKEN", ""):
                os.environ["HF_TOKEN"] = self.settings.HF_TOKEN
                
            from sentence_transformers import CrossEncoder
            import torch
            
            logger.info(f"Loading reranker model: {self.model_name}...")
            
            device = "cuda" if torch.cuda.is_available() else "cpu"
            try:
                self._model = CrossEncoder(self.model_name, device=device)
                logger.info(f"Reranker model loaded successfully on device: {device}")
            except Exception as e:
                logger.warning(f"Failed to load reranker on {device}: {e}. Trying CPU fallback...")
                try:
                    self._model = CrossEncoder(self.model_name, device="cpu")
                    logger.info("Reranker model loaded successfully on CPU.")
                except Exception as fallback_err:
                    logger.error(f"Fallback loading of reranker failed: {fallback_err}")
                    raise RuntimeError(f"Error loading reranker model {self.model_name}: {fallback_err}") from fallback_err
        return self._model

    def score_documents(self, query: str, documents: list[Document]) -> list[tuple[Document, float]]:
        """
        Score documents for a query with the cross-encoder without changing order.

        Args:
            query: The user query.
            documents: Candidate Document objects.

        Returns:
            List of (document, score) tuples in the original document order.
        """
        if not documents:
            return []

        pairs = [(query, doc.page_content) for doc in documents]
        scores = self.model.predict(pairs)
        return [(doc, float(score)) for doc, score in zip(documents, scores)]

    def rerank(
        self,
        query: str,
        documents: list[Document],
        top_n: int | None = None,
    ) -> list[Document]:
        """
        Scoring, sort, and select top_n documents based on relevance score.
        
        Args:
            query: The user query.
            documents: List of Document objects retrieved from semantic search.
            top_n: Number of documents to return. Defaults to settings.RERANKER_TOP_N.
            
        Returns:
            Sorted list of top_n Document objects.
        """
        if not documents:
            logger.info("No documents to rerank.")
            return []
            
        if top_n is None:
            top_n = getattr(self.settings, "RERANKER_TOP_N", 3)
            
        try:
            logger.info(f"Reranking {len(documents)} documents for query: '{query}'")
            
            ranked_docs = []
            for doc, score in self.score_documents(query, documents):
                new_doc = copy.deepcopy(doc)
                if not new_doc.metadata:
                    new_doc.metadata = {}
                new_doc.metadata["rerank_score"] = float(score)
                ranked_docs.append(new_doc)
                
            # Sort documents by rerank_score in descending order
            ranked_docs.sort(key=lambda x: x.metadata["rerank_score"], reverse=True)
            
            # Return top_n
            return ranked_docs[:top_n]
        except Exception as e:
            logger.error(f"Failed to rerank documents: {e}")
            # If reranking fails, return first top_n of original documents as fallback
            return documents[:top_n]


def retrieve_and_rerank(
    query: str,
    store: VectorStoreManager,
    reranker: ReRanker,
    top_k: int = 5,
    top_n: int = 3,
) -> list[Document]:
    """
    Two-stage retrieval pipeline:
    1. Retrieve top_k documents using similarity search.
    2. Rerank the retrieved documents to top_n using the cross-encoder reranker.
    
    Args:
        query: User question.
        store: Vector store manager.
        reranker: ReRanker instance.
        top_k: Number of documents to retrieve in stage 1.
        top_n: Number of documents to select after reranking.
        
    Returns:
        List of reranked Document objects.
    """
    try:
        logger.info(f"Two-stage pipeline: retrieve top {top_k} and rerank to top {top_n}")
        # Retrieve candidate documents (stage 1)
        candidates = retrieve_context(query, store, top_k=top_k)
        
        # Rerank candidates (stage 2)
        reranked_docs = reranker.rerank(query, candidates, top_n=top_n)
        return reranked_docs
    except Exception as e:
        logger.error(f"Error in retrieve_and_rerank pipeline: {e}")
        return []


def evaluate_reranking_ab(
    queries: list[str],
    store: VectorStoreManager,
    reranker: ReRanker,
    top_k: int = 10,
    top_n: int = 3,
) -> RetrievalABResult:
    """
    Measure semantic search against semantic search plus reranking on 10 queries.

    The semantic arm keeps the vector-store order and compares its top_n documents.
    The reranked arm sorts the same top_k candidates by cross-encoder score and
    compares its top_n documents. Average cross-encoder score is used as the
    relevance metric for both arms.

    Args:
        queries: Exactly 10 benchmark questions.
        store: Vector store manager.
        reranker: ReRanker instance.
        top_k: Number of semantic candidates to retrieve per query.
        top_n: Number of final documents to compare per query.

    Returns:
        RetrievalABResult with aggregate scores and per-query details.

    Raises:
        ValueError: If queries does not contain exactly 10 items.
    """
    if len(queries) != 10:
        raise ValueError("A/B evaluation requires exactly 10 queries.")

    details: list[dict[str, object]] = []
    semantic_query_scores: list[float] = []
    reranked_query_scores: list[float] = []

    for query in queries:
        candidates = retrieve_context(query, store, top_k=top_k)
        scored_candidates = reranker.score_documents(query, candidates)

        semantic_top = scored_candidates[:top_n]
        reranked_top = sorted(scored_candidates, key=lambda item: item[1], reverse=True)[:top_n]

        semantic_score = mean([score for _, score in semantic_top]) if semantic_top else 0.0
        reranked_score = mean([score for _, score in reranked_top]) if reranked_top else 0.0

        semantic_query_scores.append(semantic_score)
        reranked_query_scores.append(reranked_score)
        details.append(
            {
                "query": query,
                "semantic_avg_score": semantic_score,
                "reranked_avg_score": reranked_score,
                "improvement": reranked_score - semantic_score,
                "candidate_count": len(candidates),
            }
        )

    semantic_avg = mean(semantic_query_scores)
    reranked_avg = mean(reranked_query_scores)

    return RetrievalABResult(
        query_count=len(queries),
        semantic_avg_score=semantic_avg,
        reranked_avg_score=reranked_avg,
        improvement=reranked_avg - semantic_avg,
        details=details,
    )


if __name__ == "__main__":  # pragma: no cover
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
