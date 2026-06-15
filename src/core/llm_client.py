"""
LLM Client Factory — Provider abstraction with Protocol pattern.

Supports: Ollama (local), Groq (cloud), OpenAI (cloud).
Usage:
    llm = create_llm_client("ollama")
    response = llm.invoke("Hello!")
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Iterator, Protocol, runtime_checkable

from langchain_core.output_parsers import StrOutputParser

from src.core.config import get_settings
from src.core.exceptions import LLMConnectionError
from src.core.logger import get_logger

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)


@runtime_checkable
class LLMProvider(Protocol):
    """Abstract interface for all LLM providers."""

    def invoke(self, prompt: str) -> str:
        """Send a prompt and return the complete response."""
        ...


    def stream(self, prompt: str) -> Iterator[str]:
        """Send a prompt and stream response chunks."""
        ...


def create_llm_client(provider: str = "ollama") :
    """
    Factory function to create an LLM client.

    Args:
        provider: One of 'ollama', 'groq', 'openai'.

    Returns:
        An LLM client implementing LLMProvider protocol.

    Raises:
        LLMConnectionError: If the provider is unavailable.
        ValueError: If the provider is not supported.
    """
    settings = get_settings()

    match provider.lower():
        case "ollama":
            try:
                from langchain_ollama import ChatOllama

                llm = ChatOllama(
                    base_url=settings.OLLAMA_BASE_URL,
                    model=settings.OLLAMA_MODEL,
                    temperature=0.1,
                )
                logger.info("Ollama client created")
                return llm | StrOutputParser()
            except Exception as e:
                raise LLMConnectionError(f"Failed to connect to Ollama: {e}") from e

        case "groq":
            if not settings.GROQ_API_KEY:
                raise LLMConnectionError("GROQ_API_KEY not set in .env")
            try:
                from langchain_community.chat_models import ChatGroq

                llm = ChatGroq(
                    api_key=settings.GROQ_API_KEY,
                    model_name="llama-3.1-70b-versatile",
                    temperature=0.1,
                )
                logger.info("Groq client created")
                return llm | StrOutputParser()
            except Exception as e:
                raise LLMConnectionError(f"Failed to connect to Groq: {e}") from e

        case "openai":
            if not settings.OPENAI_API_KEY:
                raise LLMConnectionError("OPENAI_API_KEY not set in .env")
            try:
                from langchain_community.chat_models import ChatOpenAI

                llm = ChatOpenAI(
                    api_key=settings.OPENAI_API_KEY,
                    model="gpt-4o-mini",
                    temperature=0.1,
                )
                logger.info("OpenAI client created")
                return llm | StrOutputParser()
            except Exception as e:
                raise LLMConnectionError(f"Failed to connect to OpenAI: {e}") from e

        case _:
            raise ValueError(
                f"Unsupported LLM provider: '{provider}'. "
                f"Choose from: 'ollama', 'groq', 'openai'"
            )

if __name__ == "__main__":
    logger = get_logger(__name__)

    # Create an LLM client for testing
    llm = create_llm_client('ollama')

    # Test invoke method
    try:
        response = llm.invoke('Hello! How are you?')
        logger.info("LLM invoke test:", response=response)
    except Exception as e:
        logger.error(f"LLM invoke test failed: {e}")

    # Test stream method
    try:
        logger.info("LLM stream test")
        for chunk in llm.stream('Explain how RAG works in 1 sentence:'):
            print(chunk, end="", flush=True)
        print()
    except Exception as e:
        logger.error(f"LLM stream test failed: {e}")