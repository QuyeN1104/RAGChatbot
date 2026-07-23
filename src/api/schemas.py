"""
API Schemas - Pydantic request/response models.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Source(BaseModel):
    """Metadata for a retrieved source document."""

    source: str
    page: int | str | None = None


class ChatRequest(BaseModel):
    """Request body for POST /chat."""

    message: str = Field(..., min_length=1, description="User message")
    session_id: str | None = Field(default=None, description="Conversation session ID")
    top_k: int | None = Field(default=None, ge=1, le=20, description="Number of chunks to retrieve")
    mode: Literal["general", "rag"] = Field(default="general", description="Explicit chat mode")
    provider: str | None = Field(default=None, description="LLM provider: ollama, groq, openai, gemini")
    model: str | None = Field(default=None, description="Provider-specific model name")
    api_key: str | None = Field(default=None, description="Provider API key for this request only")


class ChatResponse(BaseModel):
    """Response body for POST /chat."""

    answer: str
    sources: list[Source]
    session_id: str
    provider: str
    model: str
    latency_ms: float | None = None


class ReadinessResponse(BaseModel):
    """API process readiness; model loading is request-driven."""

    status: str
    ready: bool
    total_ms: float
    timings_ms: dict[str, float]
    error: str | None = None


class UploadResponse(BaseModel):
    """Response body for POST /upload."""

    filename: str
    pages: int
    chunks: int
    document_ids: list[str]
    message: str


class HealthResponse(BaseModel):
    """Response body for GET /health."""

    status: str
    version: str

class DocumentListResponse(BaseModel):
    """Response body for GET /documents."""

    documents: list[str]


class DeleteResponse(BaseModel):
    """Generic delete/clear response."""

    message: str


class SessionSummary(BaseModel):
    """Summary of a stored chat session."""

    session_id: str
    topic: str | None = None
    last_user_message: str | None = None
    last_accessed: str | None = None
    message_count: int


class ChatMessage(BaseModel):
    """Stored chat message."""

    role: str
    content: str


class SessionDetailResponse(BaseModel):
    """Response body for GET /sessions/{session_id}."""

    session_id: str
    topic: str | None = None
    last_user_message: str | None = None
    last_accessed: str | None = None
    messages: list[ChatMessage]


class SessionListResponse(BaseModel):
    """Response body for GET /sessions."""

    sessions: list[SessionSummary]



class ModelChoice(BaseModel):
    """Frontend model picker option."""

    provider: str
    model: str
    label: str


class ModelListResponse(BaseModel):
    """Response body for GET /models."""

    default_provider: str
    default_model: str
    models: list[ModelChoice]
