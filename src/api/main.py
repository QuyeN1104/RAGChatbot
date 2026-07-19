"""FastAPI application factory with request-driven model loading."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.dependencies import get_app_settings
from src.api.routes import router
from src.core.logger import get_logger
from src.core.readiness import mark_ready, reset_readiness

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Load configuration only. Request handlers initialize and cache model resources.
    get_app_settings()
    reset_readiness()
    mark_ready()
    logger.info("API ready; model resources will load on first use")
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
