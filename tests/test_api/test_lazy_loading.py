"""Regression tests for request-driven, cached model initialization."""

import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from src.api import dependencies
from src.api import main
from src.core.readiness import readiness_snapshot


def test_lifespan_marks_ready_without_loading_model_resources(monkeypatch):
    settings_calls = 0

    def load_settings():
        nonlocal settings_calls
        settings_calls += 1
        return object()

    monkeypatch.setattr(main, "get_app_settings", load_settings)

    async def exercise_lifespan():
        async with main.lifespan(main.app):
            snapshot = readiness_snapshot()
            assert snapshot["ready"] is True
            assert snapshot["timings_ms"] == {}

    asyncio.run(exercise_lifespan())
    assert settings_calls == 1


def test_concurrent_first_requests_share_cached_client_and_graph(monkeypatch):
    dependencies._get_agent_runtime.cache_clear()
    dependencies._get_llm_client_for.cache_clear()
    calls = {"client": 0, "graph": 0}
    calls_lock = threading.Lock()
    client = object()
    graph = object()

    def create_client(provider, model):
        with calls_lock:
            calls["client"] += 1
        time.sleep(0.01)
        return client

    def create_graph(**kwargs):
        with calls_lock:
            calls["graph"] += 1
        time.sleep(0.01)
        assert kwargs["llm"] is client
        return graph

    monkeypatch.setattr(dependencies, "create_llm_client", create_client)
    monkeypatch.setattr(dependencies, "create_agent_graph", create_graph)
    monkeypatch.setattr(dependencies, "get_vector_store", lambda: object())
    monkeypatch.setattr(dependencies, "get_memory", lambda: object())

    with ThreadPoolExecutor(max_workers=8) as executor:
        runtimes = list(executor.map(
            lambda _: dependencies.get_agent_runtime("gemini", "gemini-test"),
            range(8),
        ))

    assert all(runtime is graph for runtime in runtimes)
    assert calls == {"client": 1, "graph": 1}

    dependencies._get_agent_runtime.cache_clear()
    dependencies._get_llm_client_for.cache_clear()


def test_document_metadata_does_not_load_embedding(monkeypatch, tmp_path):
    import sys
    from types import SimpleNamespace

    from src.rag.vector_store import VectorStoreManager

    collection = SimpleNamespace(get=lambda **kwargs: {"metadatas": [{"source": "guide.pdf"}]})
    client = SimpleNamespace(get_or_create_collection=lambda name: collection)
    monkeypatch.setitem(sys.modules, "chromadb", SimpleNamespace(PersistentClient=lambda path: client))

    manager = VectorStoreManager()
    manager.settings.CHROMA_PERSIST_DIR = str(tmp_path)

    assert manager.list_documents() == ["guide.pdf"]
    assert manager._embedding_service is None
    assert manager._vector_store is None
