"""
Conversation Memory — Session-based history management.

Stores conversation history per session and supports query reformulation
using previous context for follow-up questions.
"""

from __future__ import annotations

import datetime
import json
import os
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from functools import lru_cache

from src.core.logger import get_logger

if TYPE_CHECKING:
    from src.core.llm_client import LLMProvider

logger = get_logger(__name__)


class BaseMemoryStore(ABC):
    """Abstract interface for a conversation memory store."""
    
    @abstractmethod
    def add_message(self, session_id: str, role: str, content: str) -> None:
        """Add a single message to the session."""
        pass
        
    @abstractmethod
    def get_messages(self, session_id: str, last_n: int) -> list[dict]:
        """Get the recent message pairs for a session."""
        pass
        
    @abstractmethod
    def clear_session(self, session_id: str) -> None:
        """Clear all messages in a session."""
        pass


class DictMemoryStore(BaseMemoryStore):
    """File-backed dictionary storage for session persistence."""
    
    def __init__(self):
        from src.core.config import get_settings
        self.settings = get_settings()
        self.storage_file = os.path.join(self.settings.DATA_DIR, "chat_history.json")
        self._store: dict[str, dict] = self._load()
        
    def _load(self) -> dict:
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load chat history: {e}")
        return {}
        
    def _save(self):
        try:
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump(self._store, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save chat history: {e}")

    def add_message(self, session_id: str, role: str, content: str) -> None:
        if session_id not in self._store:
            self._store[session_id] = {
                "messages": [], 
                "last_accessed": "",
                "last_user_message": "",
                "topic": "New Session"
            }
            
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._store[session_id]["last_accessed"] = now
        
        if role == "user":
            self._store[session_id]["last_user_message"] = content
            if not self._store[session_id]["messages"]:
                self._store[session_id]["topic"] = content[:30] + ("..." if len(content) > 30 else "")
                
        self._store[session_id]["messages"].append({"role": role, "content": content})
        self._save()
        
    def get_messages(self, session_id: str, last_n: int) -> list[dict]:
        if session_id not in self._store:
            return []
            
        self._store[session_id]["last_accessed"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._save()
        
        history = self._store[session_id]["messages"]
        if last_n <= 0:
            return []
        return history[-(last_n * 2):]

    def clear_session(self, session_id: str) -> None:
        self._store.pop(session_id, None)
        self._save()


class ConversationMemory:
    """
    Conversation history manager and processor.

    Uses an injected memory store to persist messages and handles
    reformulating ambiguous follow-up queries using conversation context.
    """

    def __init__(self, store: BaseMemoryStore):
        """Initialize with a specific storage backend."""
        self.store = store

    def add(self, user_msg: str, ai_msg: str, session_id: str) -> None:
        """
        Add a user-assistant message pair to the session history.

        Args:
            user_msg: User's message.
            ai_msg: Assistant's response.
            session_id: Session identifier.
        """
        self.store.add_message(session_id, "user", user_msg)
        self.store.add_message(session_id, "assistant", ai_msg)
        logger.debug(f"Added message pair to session {session_id}")

    def get_history(self, session_id: str, last_n: int = 5) -> list[dict]:
        """
        Get recent conversation history for a session.

        Args:
            session_id: Session identifier.
            last_n: Number of recent message pairs to return.

        Returns:
            List of message dicts [{"role": "user"|"assistant", "content": str}].
        """
        return self.store.get_messages(session_id, last_n)

    def reformulate_query(
        self,
        query: str,
        history: list[dict],
        llm: LLMProvider,
    ) -> str:
        """
        Reformulate an ambiguous query using conversation history.

        Example: "Cái đó là gì?" → "Vector database là gì?" (based on context)

        Args:
            query: Current user query.
            history: Recent conversation history.
            llm: LLM provider for reformulation.

        Returns:
            Reformulated query string.
        """
        if not history:
            return query
            
        history_str = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in history])
        
        prompt = f"""Given the following conversation history and a follow-up question, rephrase the follow-up question to be a standalone question, in its original language.
If the follow-up question contains references like "it", "that", "cái đó", "vậy", "còn", or implicitly refers to a topic in the history, YOU MUST replace them with the explicit subject from the history.
If the follow-up question is already fully self-contained, return it exactly as is. 
Do NOT answer the question, only output the reformulated question.

Chat History:
{history_str}

Follow-up Question: {query}
Standalone Question:"""

        try:
            logger.info("Reformulating query based on history...")
            reformulated = llm.invoke(prompt).strip()
            
            if reformulated:
                logger.info(f"Query reformulated: '{query}' -> '{reformulated}'")
                return reformulated
            return query
        except Exception as e:
            logger.error(f"Failed to reformulate query: {e}")
            return query


@lru_cache(maxsize=1)
def get_memory() -> ConversationMemory:
    """Singleton factory for ConversationMemory. Cached after first call."""
    # Using the in-memory dictionary store for local development
    store = DictMemoryStore()
    return ConversationMemory(store=store)


if __name__ == "__main__":
    from src.core.llm_client import create_llm_client

    logger.info("--- Testing Conversation Memory ---")
    memory = get_memory()
    session = "user_123"

    # Add history
    memory.add("Xin chào", "Chào bạn, tôi có thể giúp gì cho bạn?", session)
    memory.add("Chính sách nghỉ phép của công ty thế nào?", "Nhân viên có 12 ngày phép một năm.", session)

    history = memory.get_history(session)
    logger.info(f"Retrieved {len(history)} messages from history.")

    # Test Reformulation
    try:
        llm = create_llm_client("ollama")
        ambiguous_query = "Vậy thực tập sinh thì sao?"
        
        standalone_query = memory.reformulate_query(ambiguous_query, history, llm)
        logger.info(f"Final Query: {standalone_query}")
    except Exception as e:
        logger.error(f"Test failed: {e}")
