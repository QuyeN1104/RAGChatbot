# MEMORY.md

## Current Objective

Improve processing speed and benchmark quality for the Agentic RAG chatbot.

## Session State — 2026-07-18

Branch: `feat/gememi-integration`.

Recent performance work already committed:

- `1dfea37 perf: warm backend and reduce chat latency`
- `b252132 feat: gate chat UI on backend readiness`

Work completed in this session but not committed:

- Fixed a concurrency bug: `/chat` no longer mutates the cached global `Settings.TOP_K`.
- Added `top_k` to `AgentState`; each graph invocation now carries its own retrieval limit.
- Extended `scripts/benchmark_api.py` with interpolated percentiles, concurrent load, throughput, error rate, and optional p95/error thresholds.
- Added unit tests for benchmark percentile/empty-summary behavior.
- Ignored `data/model_cache/` so downloaded Hugging Face model weights are not staged.

Verification:

- 21 targeted tests passed on 2026-07-18.
- Python compilation and `git diff --check` passed.
- A live API benchmark was not run in this session; backend/model services were not started.

## Worktree Ownership

Pre-existing user changes observed before this session:

- `.gitignore` already had `.codex/*`.
- `docker-compose.yml` mounted `./data/model_cache:/app/.cache`.
- `data/model_cache/` contained a partial BGE-M3 download.
- `ui/src/.write-check` was untracked.

Also observed later: untracked `skills-lock.json`. Preserve these unless the user explicitly asks to clean them.

Changes made by this session:

- `.gitignore`: added `data/model_cache/`.
- `src/agent/state.py`, `src/agent/graph.py`, `src/api/routes.py`.
- `scripts/benchmark_api.py`, `tests/test_benchmark_api.py`.
- `AGENTS.md`, `MEMORY.md`, `SOUL.md`.

## Next Steps

1. Start the real stack and capture two baselines: sequential (`c=1`) and concurrent (`c=4`).
2. Save machine/provider/model configuration beside results; do not compare unlike environments.
3. Profile stage timings inside `/chat` (reformulate, route, embed/search, generation, memory) to find the dominant warm-path cost.
4. Decide whether LLM reformulation/classification quality justifies their extra calls; defaults currently use fast routing and disabled reformulation.
5. Add API tests proving two simultaneous `top_k` values remain isolated.
6. Run the entire pytest suite and UI build before commit.

## Useful Commands

```bash
python scripts/benchmark_api.py --requests 10 --concurrency 1
python scripts/benchmark_api.py --requests 20 --concurrency 4 --max-error-rate 0
python scripts/benchmark_api.py --requests 20 --concurrency 4 --max-p95-ms 30000
```

Do not set a universal p95 threshold until a stable baseline exists for the selected provider/model and hardware.
