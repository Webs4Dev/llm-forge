import numpy as np

from src.experiments.stats import (
    bootstrap_ci,
    bootstrap_diff_ci,
    percentile,
    summarize_records,
)


def record(latency, ttft=None, error=False, cost=0.001, cache_hit=False):
    return {
        "total_latency": latency,
        "ttft": ttft,
        "error": error,
        "cost": cost,
        "cache_hit": cache_hit,
        "input_tokens": 10,
        "output_tokens": 5,
        "parse_success": not error,
        "schema_valid": not error,
    }


def test_percentile_interpolates():
    assert percentile([1, 2, 3, 4], 50) == 2.5
    assert percentile([], 50) is None


def test_bootstrap_ci_contains_estimate_and_is_reproducible():
    values = np.random.default_rng(1).normal(2.0, 0.3, 300)

    low, high = bootstrap_ci(values, np.mean)

    assert low < np.mean(values) < high
    assert (low, high) == bootstrap_ci(values, np.mean)


def test_bootstrap_diff_ci_detects_shift_and_noise():
    rng = np.random.default_rng(2)
    a = rng.normal(2.0, 0.3, 300)
    shifted = a + 1.0
    same = rng.normal(2.0, 0.3, 300)

    low, high = bootstrap_diff_ci(a, shifted, np.mean)
    assert low > 0

    low, high = bootstrap_diff_ci(a, same, np.mean)
    assert low <= 0 <= high


def test_summary_excludes_errors_from_latency_and_counts_them():
    records = [record(1.0), record(3.0), record(50.0, error=True)]

    summary = summarize_records(records, wall_time=2.0)

    assert summary["errors"] == 1
    assert summary["latency_mean"] == 2.0
    assert summary["throughput"] == 1.5


def test_summary_reports_ttft_only_when_measured():
    summary = summarize_records([record(1.0), record(2.0, ttft=0.4)])

    assert summary["ttft_measured"] == 1
    assert summary["ttft_mean"] == 0.4


def test_summary_cost_unknown_if_any_cost_missing():
    summary = summarize_records([record(1.0), record(1.0, cost=None)])

    assert summary["total_cost"] is None
