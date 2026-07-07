"""
API Routes - Endpoint definitions.

Endpoints:
    POST /chat    - Send a message and get a RAG-powered response
    POST /upload  - Upload a PDF for ingestion
    GET /health   - Health check
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from src.agent.memory import ConversationMemory
from src.api.dependencies import get_app_settings, get_llm_client, get_memory, get_vector_store
from src.api.schemas import (
    ChatRequest,
    ChatResponse,
    DeleteResponse,
    DocumentListResponse,
    HealthResponse,
    SessionDetailResponse,
    SessionListResponse,
    SessionSummary,
    Source,
    UploadResponse,
)
from src.core.config import Settings
from src.core.exceptions import DocumentError, LLMConnectionError, RAGException, VectorStoreError
from src.core.llm_client import LLMProvider
from src.core.logger import get_logger
from src.rag.document import chunk_documents, load_pdf
from src.agent.graph import create_agent_graph
from src.rag.vector_store import VectorStoreManager

logger = get_logger(__name__)
router = APIRouter()


def _format_sources(documents: list) -> list[Source]:
    """Extract stable source metadata from retrieved documents."""
    sources: list[Source] = []
    seen: set[tuple[str, int | str | None]] = set()

    for doc in documents:
        metadata = doc.metadata or {}
        source = Path(str(metadata.get("source", "Unknown"))).name
        page = metadata.get("page")
        key = (source, page)
        if key in seen:
            continue
        seen.add(key)
        sources.append(Source(source=source, page=page))

    return sources


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Return API health status."""
    return HealthResponse(status="healthy", version="0.1.0")




@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    vector_store: VectorStoreManager = Depends(get_vector_store),
) -> DocumentListResponse:
    """List uploaded document sources."""
    try:
        return DocumentListResponse(documents=vector_store.list_documents())
    except VectorStoreError as e:
        logger.error(f"Document listing failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.delete("/documents/{source_name}", response_model=DeleteResponse)
async def delete_document(
    source_name: str,
    vector_store: VectorStoreManager = Depends(get_vector_store),
) -> DeleteResponse:
    """Delete all vector chunks for a document source."""
    try:
        deleted = vector_store.delete_document(source_name)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document '{source_name}' not found.",
            )
        return DeleteResponse(message=f"Deleted document: {source_name}")
    except HTTPException:
        raise
    except VectorStoreError as e:
        logger.error(f"Document deletion failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    memory: ConversationMemory = Depends(get_memory),
) -> SessionListResponse:
    """List server-side memory sessions."""
    store = getattr(memory.store, "_store", {})
    sessions = []
    for session_id, metadata in store.items():
        sessions.append(
            SessionSummary(
                session_id=session_id,
                topic=metadata.get("topic"),
                last_user_message=metadata.get("last_user_message"),
                last_accessed=metadata.get("last_accessed"),
                message_count=len(metadata.get("messages", [])),
            )
        )
    sessions.sort(key=lambda item: item.last_accessed or "", reverse=True)
    return SessionListResponse(sessions=sessions)


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: str,
    memory: ConversationMemory = Depends(get_memory),
) -> SessionDetailResponse:
    """Return full server-side messages for a session."""
    store = getattr(memory.store, "_store", {})
    metadata = store.get(session_id)
    if metadata is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )

    return SessionDetailResponse(
        session_id=session_id,
        topic=metadata.get("topic"),
        last_user_message=metadata.get("last_user_message"),
        last_accessed=metadata.get("last_accessed"),
        messages=metadata.get("messages", []),
    )


@router.delete("/sessions/{session_id}", response_model=DeleteResponse)
async def clear_session(
    session_id: str,
    memory: ConversationMemory = Depends(get_memory),
) -> DeleteResponse:
    """Clear server-side history for a session."""
    memory.store.clear_session(session_id)
    return DeleteResponse(message=f"Cleared session: {session_id}")


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    llm: LLMProvider = Depends(get_llm_client),
    vector_store: VectorStoreManager = Depends(get_vector_store),
    memory: ConversationMemory = Depends(get_memory),
    settings: Settings = Depends(get_app_settings),
) -> ChatResponse:
    """Answer a user message using the same routed graph as the CLI."""
    message = request.message.strip()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="message must not be empty",
        )

    session_id = request.session_id or str(uuid4())

    try:
        if request.top_k is not None:
            settings.TOP_K = request.top_k
        app = create_agent_graph(llm=llm, vector_store=vector_store, memory=memory)
        result = app.invoke({"query": message, "session_id": session_id})
        raw_sources = result.get("sources", []) or []
        sources = [Source(source=str(src.get("source", "Unknown")), page=src.get("page")) for src in raw_sources]
        return ChatResponse(
            answer=result.get("answer", ""),
            sources=sources,
            session_id=session_id,
        )
    except (LLMConnectionError, VectorStoreError, RAGException) as e:
        logger.error(f"Chat request failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e
    except Exception as e:
        logger.exception("Unexpected chat request failure")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while processing chat request.",
        ) from e


@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile,
    vector_store: VectorStoreManager = Depends(get_vector_store),
) -> UploadResponse:
    """Upload a PDF, chunk it, and ingest it into the vector database."""
    filename = Path(file.filename or "").name
    if not filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="filename is required")

    valid_pdf_content_type = file.content_type in {"application/pdf", "application/x-pdf"}
    valid_pdf_extension = filename.lower().endswith(".pdf")
    if not valid_pdf_content_type and not valid_pdf_extension:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF uploads are supported",
        )

    temp_path: Path | None = None
    try:
        suffix = Path(filename).suffix or ".pdf"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            temp_path = Path(tmp.name)
            while chunk := await file.read(1024 * 1024):
                tmp.write(chunk)

        pages = load_pdf(temp_path)
        for page in pages:
            page.metadata = page.metadata or {}
            page.metadata["source"] = filename

        chunks = chunk_documents(pages)
        document_ids = vector_store.add_documents(chunks)

        return UploadResponse(
            filename=filename,
            pages=len(pages),
            chunks=len(chunks),
            document_ids=document_ids,
            message="PDF ingested successfully",
        )
    except HTTPException:
        raise
    except DocumentError as e:
        logger.error(f"PDF upload failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except VectorStoreError as e:
        logger.error(f"Vector store ingestion failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e
    except Exception as e:
        logger.exception("Unexpected upload failure")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while ingesting PDF.",
        ) from e
    finally:
        await file.close()
        if temp_path and temp_path.exists():
            temp_path.unlink(missing_ok=True)
