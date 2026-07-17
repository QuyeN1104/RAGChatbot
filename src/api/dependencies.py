"""FastAPI dependency singletons and cached chat runtimes."""

from __future__ import annotations

from functools import lru_cache

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


@lru_cache(maxsize=16)
def get_llm_client_for(provider: str, model: str) -> LLMProvider:
    """Reuse provider clients so transports and local model state stay warm."""
    return create_llm_client(provider, model)


@lru_cache(maxsize=16)
def get_agent_runtime(provider: str, model: str):
    """Compile one LangGraph runtime per configured provider/model pair."""
    llm = get_llm_client_for(provider, model)
    return create_agent_graph(llm=llm, vector_store=get_vector_store(), memory=get_memory())


@lru_cache(maxsize=1)
def get_llm_client() -> LLMProvider:
    settings = get_app_settings()
    provider = settings.DEFAULT_LLM_PROVIDER.strip().lower()
    return get_llm_client_for(provider, default_model_for_provider(provider))
