"""Process-wide startup readiness and warmup timing state."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field


@dataclass
class ReadinessState:
    status: str = "starting"
    started_at: float = field(default_factory=time.perf_counter)
    ready_at: float | None = None
    error: str | None = None
    timings_ms: dict[str, float] = field(default_factory=dict)

    @property
    def total_ms(self) -> float:
        end = self.ready_at if self.ready_at is not None else time.perf_counter()
        return round((end - self.started_at) * 1000, 2)


_state = ReadinessState()
_lock = threading.Lock()


def reset_readiness() -> None:
    global _state
    with _lock:
        _state = ReadinessState()


def record_timing(name: str, elapsed_seconds: float) -> None:
    with _lock:
        _state.timings_ms[name] = round(elapsed_seconds * 1000, 2)


def mark_ready() -> None:
    with _lock:
        _state.status = "ready"
        _state.ready_at = time.perf_counter()
        _state.error = None


def mark_failed(error: Exception) -> None:
    with _lock:
        _state.status = "failed"
        _state.ready_at = time.perf_counter()
        _state.error = str(error)


def readiness_snapshot() -> dict[str, object]:
    with _lock:
        return {
            "status": _state.status,
            "ready": _state.status == "ready",
            "total_ms": _state.total_ms,
            "timings_ms": dict(_state.timings_ms),
            "error": _state.error,
        }
