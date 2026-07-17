"""
Pydantic Settings — Centralized configuration management.

All settings are loaded from .env file and can be overridden via environment variables.
Uses @lru_cache for singleton pattern to avoid re-reading .env on every access.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide configuration loaded from environment variables."""
    # -- DATA DIRECTORY --
    DATA_DIR: str = "./data"
    # --- LLM Runtime ---
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "bot-rag"
    TEMPERATURE:float = 0.1

    # --- LLM Fallback ---
    GROQ_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    DEFAULT_LLM_PROVIDER: str = "ollama"
    GROQ_MODEL: str = "llama-3.1-70b-versatile"
    OPENAI_MODEL: str = "gpt-5.4-mini"
    GEMINI_MODEL: str = "gemini-2.5-flash"
    LLM_TIMEOUT_SECONDS: float = 20.0
    LLM_MAX_RETRIES: int = 1
    CHAT_TIMEOUT_SECONDS: float = 80.0

    # --- Embedding ---
    HF_TOKEN: str = ""
    EMBEDDING_MODEL: str = "BAAI/bge-m3"

    # --- Vector Database ---
    CHROMA_PERSIST_DIR: str = "./data/vector_db"
    CHROMA_COLLECTION: str = "documents"

    # --- RAG Pipeline ---
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    TOP_K: int = 5

    # --- Re-ranker ---
    RERANKER_MODEL: str = "BAAI/bge-reranker-v2-m3"
    RERANKER_TOP_N: int = 3

    # --- Startup & Performance ---
    STARTUP_WARMUP: bool = True
    STARTUP_WARMUP_LLM: bool = True
    STARTUP_FAIL_FAST: bool = True
    ENABLE_LLM_QUERY_REFORMULATION: bool = False
    ENABLE_LLM_INTENT_CLASSIFICATION: bool = False
    SESSION_HISTORY_LIMIT: int = 100
    MEMORY_HISTORY_PAIRS: int = 5

    # --- API Server ---
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # --- Logging ---
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Singleton factory for Settings. Cached after first call."""
    return Settings()
