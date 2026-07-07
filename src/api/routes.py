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
from src.api.schemas import ChatRequest, ChatResponse, HealthResponse, Source, UploadResponse
from src.core.config import Settings
from src.core.exceptions import DocumentError, LLMConnectionError, RAGException, VectorStoreError
from src.core.llm_client import LLMProvider
from src.core.logger import get_logger
from src.rag.document import chunk_documents, load_pdf
from src.rag.retriever import generate_answer, retrieve_context
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


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    llm: LLMProvider = Depends(get_llm_client),
    vector_store: VectorStoreManager = Depends(get_vector_store),
    memory: ConversationMemory = Depends(get_memory),
    settings: Settings = Depends(get_app_settings),
) -> ChatResponse:
    """Answer a user message with retrieved document context."""
    message = request.message.strip()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="message must not be empty",
        )

    session_id = request.session_id or str(uuid4())
    top_k = request.top_k or settings.TOP_K

    try:
        history = memory.get_history(session_id)
        query = memory.reformulate_query(message, history, llm)
        documents = retrieve_context(query, vector_store, top_k=top_k)
        if not documents:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No relevant documents found for this query.",
            )

        answer = generate_answer(query, documents, llm, history=history)
        memory.add(message, answer, session_id)
        return ChatResponse(
            answer=answer,
            sources=_format_sources(documents),
            session_id=session_id,
        )
    except HTTPException:
        raise
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
