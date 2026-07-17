# AGENTS.md

## Mission

Build a production-minded Agentic RAG chatbot. Current priority: lower startup/chat latency and keep benchmarks reproducible without reducing answer quality.

## Start Every Session

1. Read `SOUL.md`, `MEMORY.md`, and `git status --short`.
2. Preserve unrelated user changes. Never delete `data/`, caches, or UI probe files without confirmation.
3. Read the two latest performance commits before changing the hot path: `1dfea37` and `b252132`.
4. Establish a baseline before claiming a speedup.

## Engineering Rules

- Do not mutate cached `Settings` per request. Request options belong in request/graph state.
- Keep heavyweight services cached: embedding model, Chroma, LLM client, compiled LangGraph, memory.
- Separate cold-start, warm sequential, and concurrent measurements.
- Report p50, p95, throughput, error rate, provider/model, concurrency, and `top_k`.
- A performance change needs a regression test or benchmark evidence.
- Do not commit model caches, vector DB data, API keys, or generated benchmark output.

## Verification

```bash
.venv/bin/python -m pytest
.venv/bin/python -m py_compile scripts/benchmark_api.py src/api/routes.py src/agent/graph.py
npm --prefix ui run build
python scripts/benchmark_api.py --requests 10 --concurrency 1
python scripts/benchmark_api.py --requests 20 --concurrency 4
```

Use `--max-p95-ms` and `--max-error-rate` only after recording a stable machine-specific baseline.
