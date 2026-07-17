"""FastAPI application factory with blocking startup warmup."""

from __future__ import annotations

import asyncio
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.dependencies import (
    get_agent_runtime,
    get_app_settings,
    get_llm_client_for,
    get_memory,
    get_vector_store,
)
from src.api.routes import router
from src.core.llm_client import default_model_for_provider, get_available_models
from src.core.logger import get_logger
from src.core.readiness import mark_failed, mark_ready, record_timing, reset_readiness

logger = get_logger(__name__)


def _measure(name: str, operation):
    started = time.perf_counter()
    result = operation()
    elapsed = time.perf_counter() - started
    record_timing(name, elapsed)
    logger.info("Startup stage %s completed in %.2f ms", name, elapsed * 1000)
    return result


def _warmup_dependencies() -> None:
    """Load all request-critical resources before the API accepts traffic."""
    settings = get_app_settings()
    _measure("memory_load", get_memory)

    vector_store = get_vector_store()
    _measure("embedding_and_chroma_load", lambda: vector_store.vector_store)
    _measure("embedding_inference", lambda: vector_store.embedding_service.embed_query("warmup"))

    _measure("model_configuration", get_available_models)
    provider = settings.DEFAULT_LLM_PROVIDER.strip().lower()
    model = default_model_for_provider(provider)
    llm = _measure("default_llm_client", lambda: get_llm_client_for(provider, model))
    _measure("langgraph_compile", lambda: get_agent_runtime(provider, model))

    if settings.STARTUP_WARMUP_LLM:
        _measure("default_llm_inference", lambda: llm.invoke("Reply with exactly: OK"))


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_app_settings()
    reset_readiness()
    try:
        if settings.STARTUP_WARMUP:
            await asyncio.to_thread(_warmup_dependencies)
        mark_ready()
        logger.info("API readiness warmup completed")
    except Exception as error:
        mark_failed(error)
        logger.exception("API startup warmup failed")
        if settings.STARTUP_FAIL_FAST:
            raise
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Agentic RAG API",
        description="Enterprise RAG System with Local LLM",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000", "http://127.0.0.1:3000",
            "http://localhost:5173", "http://127.0.0.1:5173",
            "https://*.vercel.app",
        ],
        allow_origin_regex=r"https://.*\.vercel\.app",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        logger.warning(f"Validation error for {request.url.path}: {exc}")
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": exc.errors()})

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(f"Unhandled API error for {request.url.path}")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": "Internal server error."})

    return app


app = create_app()
