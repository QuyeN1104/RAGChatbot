"""FastAPI dependency singletons and cached chat runtimes."""

from __future__ import annotations

from functools import lru_cache
from threading import RLock

from src.agent.graph import create_agent_graph
from src.agent.memory import ConversationMemory, get_memory as create_memory
from src.core.config import Settings, get_settings
from src.core.llm_client import LLMProvider, create_llm_client, default_model_for_provider
from src.rag.vector_store import VectorStoreManager


@lru_cache(maxsize=1)
def get_app_settings() -> Settings:
    return get_settings()


@lru_cache(maxsize=1)
def get_vector_store() -> VectorStoreManager:
    return VectorStoreManager()


def get_memory() -> ConversationMemory:
    return create_memory()


_runtime_lock = RLock()


@lru_cache(maxsize=16)
def _get_llm_client_for(provider: str, model: str) -> LLMProvider:
    return create_llm_client(provider, model)


def get_llm_client_for(provider: str, model: str) -> LLMProvider:
    """Lazy-load and reuse clients, including under concurrent cold traffic."""
    # lru_cache may execute a missing call more than once under concurrent misses.
    with _runtime_lock:
        return _get_llm_client_for(provider, model)


@lru_cache(maxsize=16)
def _get_agent_runtime(provider: str, model: str):
    """Compile one LangGraph runtime per configured provider/model pair."""
    llm = get_llm_client_for(provider, model)
    return create_agent_graph(llm=llm, vector_store=get_vector_store(), memory=get_memory())


def get_agent_runtime(provider: str, model: str):
    """Lazy-load and reuse one runtime, including under concurrent cold traffic."""
    with _runtime_lock:
        return _get_agent_runtime(provider, model)


@lru_cache(maxsize=1)
def get_llm_client() -> LLMProvider:
    settings = get_app_settings()
    provider = settings.DEFAULT_LLM_PROVIDER.strip().lower()
    return get_llm_client_for(provider, default_model_for_provider(provider))
