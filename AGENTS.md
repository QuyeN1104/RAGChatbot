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


## Gemini API Development

- Read Gemini credentials from `GEMINI_API_KEY`; `GOOGLE_API_KEY` is supported only as a compatibility fallback. Never hardcode, log, commit, or place keys in URLs.
- If a key appears in code or logs (commonly `AIza...`), stop and tell the user to revoke it in Google AI Studio before continuing.
- Use provider `gemini` and a model from `GEMINI_MODEL` (default: `gemini-flash-latest`). User-supplied `api_key` values are request-scoped and must never enter a shared cache.
- For a configured server key, use the cached runtime in `src/api/dependencies.py`; do not call `create_llm_client` directly from a normal request path.
- Keep model resources lazy: API startup and readiness probes must not construct clients, compile LangGraph, load Chroma, load embeddings, or invoke a model. The first real chat/RAG request pays cold-start cost; later requests reuse cached resources.
- Cold initialization must be concurrency-safe so simultaneous first requests do not create duplicate clients or graphs.
- Test Gemini directly with a header, never a query parameter:

```bash
curl https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent -H "Content-Type: application/json" -H "X-goog-api-key: $GEMINI_API_KEY" -X POST -d '{"contents":[{"parts":[{"text":"Hello"}]}]}'
```
