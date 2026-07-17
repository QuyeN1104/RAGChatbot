from scripts.benchmark_api import percentile, summarize


def test_percentile_interpolates():
    assert percentile([10.0, 20.0], 0.5) == 15.0
    assert percentile([30.0, 10.0, 20.0], 0.95) == 29.0


def test_summarize_empty():
    assert summarize([]) == {"min_ms": 0.0, "mean_ms": 0.0, "p50_ms": 0.0, "p95_ms": 0.0, "max_ms": 0.0}
