"""
API Dependencies - Dependency injection for FastAPI.

Provides singleton instances of LLM, VectorStore, Memory via FastAPI Depends().
"""

from __future__ import annotations

from functools import lru_cache

from src.agent.memory import ConversationMemory, get_memory as create_memory
from src.core.config import Settings, get_settings
from src.core.llm_client import LLMProvider, create_llm_client
from src.rag.vector_store import VectorStoreManager


@lru_cache(maxsize=1)
def get_app_settings() -> Settings:
    """Return cached application settings."""
    return get_settings()


@lru_cache(maxsize=1)
def get_llm_client() -> LLMProvider:
    """Return a cached default LLM client."""
    settings = get_app_settings()
    return create_llm_client(settings.DEFAULT_LLM_PROVIDER)


@lru_cache(maxsize=1)
def get_vector_store() -> VectorStoreManager:
    """Return a cached vector store manager."""
    return VectorStoreManager()


def get_memory() -> ConversationMemory:
    """Return the conversation memory singleton."""
    return create_memory()
