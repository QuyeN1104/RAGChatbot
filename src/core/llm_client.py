"""
LLM Client Factory - Provider abstraction with Protocol pattern.

Supports: Ollama (local), Groq, OpenAI, and Gemini.
User-supplied API keys can be passed per request and are not cached here.
"""

from __future__ import annotations

from typing import Iterator, Protocol, runtime_checkable

from langchain_core.output_parsers import StrOutputParser

from src.core.config import get_settings
from src.core.exceptions import LLMConnectionError
from src.core.logger import get_logger

logger = get_logger(__name__)

SUPPORTED_LLM_PROVIDERS = ("ollama", "groq", "openai", "gemini")


@runtime_checkable
class LLMProvider(Protocol):
    """Abstract interface for all LLM providers."""

    def invoke(self, prompt: str) -> str:
        """Send a prompt and return the complete response."""
        ...

    def stream(self, prompt: str) -> Iterator[str]:
        """Send a prompt and stream response chunks."""
        ...


def _normalize_provider(provider: str | None) -> str:
    settings = get_settings()
    selected = (provider or settings.DEFAULT_LLM_PROVIDER or "ollama").strip().lower()
    if selected == "google":
        selected = "gemini"
    if selected not in SUPPORTED_LLM_PROVIDERS:
        supported = ", ".join(SUPPORTED_LLM_PROVIDERS)
        raise ValueError(f"Unsupported LLM provider: '{provider}'. Choose from: {supported}")
    return selected


def _clean_api_key(api_key: str | None) -> str:
    return (api_key or "").strip()


def default_model_for_provider(provider: str) -> str:
    """Return the configured default model for a provider."""
    settings = get_settings()
    match _normalize_provider(provider):
        case "ollama":
            return settings.OLLAMA_MODEL
        case "groq":
            return settings.GROQ_MODEL
        case "openai":
            return settings.OPENAI_MODEL
        case "gemini":
            return settings.GEMINI_MODEL
        case _:
            raise ValueError(f"Unsupported LLM provider: '{provider}'")


def get_available_models() -> list[dict[str, str]]:
    """Return static model choices for the frontend model picker."""
    settings = get_settings()
    return [
        {
            "provider": "ollama",
            "model": settings.OLLAMA_MODEL,
            "label": f"Ollama - {settings.OLLAMA_MODEL}",
        },
        {
            "provider": "gemini",
            "model": settings.GEMINI_MODEL,
            "label": f"Gemini - {settings.GEMINI_MODEL}",
        },
        {
            "provider": "openai",
            "model": settings.OPENAI_MODEL,
            "label": f"OpenAI - {settings.OPENAI_MODEL}",
        },
        {
            "provider": "groq",
            "model": settings.GROQ_MODEL,
            "label": f"Groq - {settings.GROQ_MODEL}",
        },
    ]


def create_llm_client(
    provider: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
) -> LLMProvider:
    """
    Create an LLM client.

    Args:
        provider: One of 'ollama', 'groq', 'openai', 'gemini'.
        model: Optional model override for the selected provider.
        api_key: Optional user-supplied API key for this request only.

    Raises:
        LLMConnectionError: If credentials or provider package are unavailable.
        ValueError: If provider is unsupported.
    """
    settings = get_settings()
    selected_provider = _normalize_provider(provider)
    selected_model = (model or default_model_for_provider(selected_provider)).strip()
    request_api_key = _clean_api_key(api_key)

    match selected_provider:
        case "ollama":
            try:
                from langchain_ollama import ChatOllama

                llm = ChatOllama(
                    base_url=settings.OLLAMA_BASE_URL,
                    model=selected_model,
                    temperature=settings.TEMPERATURE,
                )
                logger.info(f"Ollama client created with model: {selected_model}")
                return llm | StrOutputParser()
            except Exception as e:
                raise LLMConnectionError(f"Failed to connect to Ollama: {e}") from e

        case "groq":
            resolved_key = request_api_key or settings.GROQ_API_KEY
            if not resolved_key:
                raise LLMConnectionError("Groq API key is required for this model.")
            try:
                from langchain_groq import ChatGroq
            except ImportError:
                try:
                    from langchain_community.chat_models import ChatGroq
                except ImportError as e:
                    raise LLMConnectionError(
                        "Groq support requires langchain-groq or langchain-community."
                    ) from e
            try:
                llm = ChatGroq(
                    api_key=resolved_key,
                    model=selected_model,
                    temperature=settings.TEMPERATURE,
                    timeout=settings.LLM_TIMEOUT_SECONDS,
                    max_retries=settings.LLM_MAX_RETRIES,
                )
                logger.info(f"Groq client created with model: {selected_model}")
                return llm | StrOutputParser()
            except Exception as e:
                raise LLMConnectionError(f"Failed to connect to Groq: {e}") from e

        case "openai":
            resolved_key = request_api_key or settings.OPENAI_API_KEY
            if not resolved_key:
                raise LLMConnectionError("OpenAI API key is required for this model.")
            try:
                from langchain_openai import ChatOpenAI
            except ImportError as e:
                raise LLMConnectionError("OpenAI support requires langchain-openai.") from e
            try:
                llm = ChatOpenAI(
                    api_key=resolved_key,
                    model=selected_model,
                    temperature=settings.TEMPERATURE,
                    timeout=settings.LLM_TIMEOUT_SECONDS,
                    max_retries=settings.LLM_MAX_RETRIES,
                )
                logger.info(f"OpenAI client created with model: {selected_model}")
                return llm | StrOutputParser()
            except Exception as e:
                raise LLMConnectionError(f"Failed to connect to OpenAI: {e}") from e

        case "gemini":
            resolved_key = request_api_key or settings.GEMINI_API_KEY or settings.GOOGLE_API_KEY
            if not resolved_key:
                raise LLMConnectionError("Gemini API key is required for this model.")
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
            except ImportError as e:
                raise LLMConnectionError("Gemini support requires langchain-google-genai.") from e
            try:
                llm = ChatGoogleGenerativeAI(
                    api_key=resolved_key,
                    model=selected_model,
                    temperature=settings.TEMPERATURE,
                    request_timeout=settings.LLM_TIMEOUT_SECONDS,
                    retries=settings.LLM_MAX_RETRIES,
                )
                logger.info(f"Gemini client created with model: {selected_model}")
                return llm | StrOutputParser()
            except Exception as e:
                raise LLMConnectionError(f"Failed to connect to Gemini: {e}") from e

        case _:
            supported = ", ".join(SUPPORTED_LLM_PROVIDERS)
            raise ValueError(f"Unsupported LLM provider: '{provider}'. Choose from: {supported}")


if __name__ == "__main__":
    llm = create_llm_client("ollama")
    try:
        response = llm.invoke("Hello! How are you?")
        logger.info(f"LLM invoke test: {response}")
    except Exception as e:
        logger.error(f"LLM invoke test failed: {e}")
