"""Small dependency-free HTTP benchmark for startup, history, and chat latency."""

from __future__ import annotations

import argparse
import json
import statistics
import time
import urllib.error
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed


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
    rank = (len(ordered) - 1) * fraction
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    weight = rank - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def summarize(values: list[float]) -> dict[str, float]:
    if not values:
        return {key: 0.0 for key in ("min_ms", "mean_ms", "p50_ms", "p95_ms", "max_ms")}
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
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--max-p95-ms", type=float)
    parser.add_argument("--max-error-rate", type=float, default=0.0)
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

    if args.requests < 1 or args.warmup < 0 or not 1 <= args.concurrency <= args.requests:
        parser.error("require requests >= concurrency >= 1 and warmup >= 0")

    def chat_once() -> tuple[float, float]:
        payload = {
            "message": args.query,
            "session_id": "benchmark-" + str(uuid.uuid4()),
            "provider": default_provider,
            "model": default_model,
        }
        response, wall_ms = request_json(base + "/chat", method="POST", payload=payload)
        return wall_ms, float(response.get("latency_ms") or wall_ms)

    for _ in range(args.warmup):
        chat_once()
    wall_values: list[float] = []
    server_values: list[float] = []
    errors: list[str] = []
    load_started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = [executor.submit(chat_once) for _ in range(args.requests)]
        for future in as_completed(futures):
            try:
                wall_ms, server_ms = future.result()
                wall_values.append(wall_ms)
                server_values.append(server_ms)
            except Exception as error:
                errors.append(str(error))
    load_seconds = time.perf_counter() - load_started

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
        "passed": not errors,
        "chat_wall": summarize(wall_values),
        "chat_server": summarize(server_values),
        "throughput_rps": round(len(wall_values) / load_seconds, 2),
        "error_rate": round(len(errors) / args.requests, 4),
        "errors": errors[:5],
        "requests": args.requests,
        "concurrency": args.concurrency,
        "provider": default_provider,
        "model": default_model,
    }
    failures = []
    if args.max_p95_ms is not None and report["chat_wall"]["p95_ms"] > args.max_p95_ms:
        failures.append("p95 threshold exceeded")
    if report["error_rate"] > args.max_error_rate:
        failures.append("error-rate threshold exceeded")
    report["passed"] = not failures
    report["failures"] = failures
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    try:
        main()
    except urllib.error.URLError as error:
        raise SystemExit("Benchmark request failed: " + str(error)) from error
