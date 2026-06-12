"""
FastAPI Application Factory — Main API entry point.

Usage:
    uvicorn src.api.main:create_app --factory --reload
"""

from __future__ import annotations

from fastapi import FastAPI


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI instance.
    """
    app = FastAPI(
        title="Agentic RAG API",
        description="Enterprise RAG System with Local LLM",
        version="0.1.0",
    )

    # TODO: Include routers in Sprint 2, Day 12
    # from src.api.routes import router
    # app.include_router(router)

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "version": "0.1.0"}

    return app
