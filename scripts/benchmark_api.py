"""Small dependency-free HTTP benchmark for startup, history, and chat latency."""

from __future__ import annotations

import argparse
import json
import statistics
import time
import urllib.error
import urllib.request
import uuid


def request_json(url: str, method: str = "GET", payload: dict | None = None) -> tuple[dict, float]:
    body = json.dumps(payload).encode() if payload is not None else None
    headers = {"Content-Type": "application/json"} if body else {}
    started = time.perf_counter()
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=180) as response:
        result = json.load(response)
    return result, (time.perf_counter() - started) * 1000


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * fraction)))
    return ordered[index]


def summarize(values: list[float]) -> dict[str, float]:
    return {
        "min_ms": round(min(values), 2),
        "mean_ms": round(statistics.mean(values), 2),
        "p50_ms": round(percentile(values, 0.50), 2),
        "p95_ms": round(percentile(values, 0.95), 2),
        "max_ms": round(max(values), 2),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark Agentic RAG API")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--requests", type=int, default=5)
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--query", default="Tóm tắt nội dung chính trong tài liệu.")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")

    ready, ready_wall = request_json(base + "/ready")
    if not ready.get("ready"):
        raise SystemExit("API is not ready: " + str(ready.get("error") or ready.get("status")))

    models, models_ms = request_json(base + "/models")
    sessions, sessions_ms = request_json(base + "/sessions")
    default_provider = models["default_provider"]
    default_model = models["default_model"]

    wall_values: list[float] = []
    server_values: list[float] = []
    total = args.warmup + args.requests
    for index in range(total):
        payload = {
            "message": args.query,
            "session_id": "benchmark-" + str(uuid.uuid4()),
            "provider": default_provider,
            "model": default_model,
        }
        response, wall_ms = request_json(base + "/chat", method="POST", payload=payload)
        if index >= args.warmup:
            wall_values.append(wall_ms)
            server_values.append(float(response.get("latency_ms") or wall_ms))

    report = {
        "startup": {
            "ready_probe_wall_ms": round(ready_wall, 2),
            "backend_total_ms": ready.get("total_ms"),
            "stages_ms": ready.get("timings_ms"),
        },
        "read_paths": {
            "models_ms": round(models_ms, 2),
            "sessions_ms": round(sessions_ms, 2),
            "session_count": len(sessions.get("sessions", [])),
        },
        "chat_wall": summarize(wall_values),
        "chat_server": summarize(server_values),
        "requests": args.requests,
        "provider": default_provider,
        "model": default_model,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except urllib.error.URLError as error:
        raise SystemExit("Benchmark request failed: " + str(error)) from error
