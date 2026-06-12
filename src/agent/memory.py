"""
Conversation Memory — Session-based history management.

Stores conversation history per session and supports query reformulation
using previous context for follow-up questions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.core.logger import get_logger

if TYPE_CHECKING:
    from src.core.llm_client import LLMProvider

logger = get_logger(__name__)


class ConversationMemory:
    """
    In-memory conversation history manager.

    Stores messages per session_id and can reformulate ambiguous
    follow-up queries using conversation context.
    """

    def __init__(self):
        """Initialize empty conversation store."""
        self._store: dict[str, list[dict]] = {}

    def add(self, user_msg: str, ai_msg: str, session_id: str) -> None:
        """
        Add a user-assistant message pair to the session history.

        Args:
            user_msg: User's message.
            ai_msg: Assistant's response.
            session_id: Session identifier.
        """
        # TODO: Implement in Sprint 1, Day 5
        raise NotImplementedError("Memory add will be implemented in Day 5")

    def get_history(self, session_id: str, last_n: int = 5) -> list[dict]:
        """
        Get recent conversation history for a session.

        Args:
            session_id: Session identifier.
            last_n: Number of recent message pairs to return.

        Returns:
            List of message dicts [{"role": "user"|"assistant", "content": str}].
        """
        # TODO: Implement in Sprint 1, Day 5
        raise NotImplementedError("Memory retrieval will be implemented in Day 5")

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
        # TODO: Implement in Sprint 1, Day 5
        raise NotImplementedError("Query reformulation will be implemented in Day 5")
