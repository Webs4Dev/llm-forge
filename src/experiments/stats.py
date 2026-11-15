"""Shared statistics for experiment runs.

One percentile definition for every script (linear interpolation, the same
method numpy uses by default). Earlier scripts mixed truncation and
interpolation, which made P95/P99 slightly inconsistent between experiments.
"""

import numpy as np


def percentile(values, q):
    if len(values) == 0:
        return None

    return float(np.percentile(np.asarray(values, dtype=float), q))


def mean(values):
    if len(values) == 0:
        return None

    return float(np.mean(values))


def bootstrap_ci(
    values,
    statistic,
    n_resamples=2000,
    confidence=0.95,
    seed=0,
):
    """Percentile-bootstrap confidence interval for statistic(values).

    This measures how much the statistic would move if the same run had
    sampled different requests. It does NOT capture run-to-run drift
    (provider load at a different time of day); only repeated runs show that.
    """
    values = np.asarray(values, dtype=float)

    if len(values) == 0:
        return None, None

    rng = np.random.default_rng(seed)
    indexes = rng.integers(0, len(values), size=(n_resamples, len(values)))
    estimates = np.array([statistic(values[row]) for row in indexes])

    alpha = (1 - confidence) / 2

    return (
        float(np.quantile(estimates, alpha)),
        float(np.quantile(estimates, 1 - alpha)),
    )


def bootstrap_diff_ci(
    values_a,
    values_b,
    statistic,
    n_resamples=2000,
    confidence=0.95,
    seed=0,
):
    """CI for statistic(b) - statistic(a), resampling each run independently.

    If the interval contains 0, the difference is within sampling noise.
    """
    a = np.asarray(values_a, dtype=float)
    b = np.asarray(values_b, dtype=float)

    if len(a) == 0 or len(b) == 0:
        return None, None

    rng = np.random.default_rng(seed)
    idx_a = rng.integers(0, len(a), size=(n_resamples, len(a)))
    idx_b = rng.integers(0, len(b), size=(n_resamples, len(b)))

    diffs = np.array([
        statistic(b[row_b]) - statistic(a[row_a])
        for row_a, row_b in zip(idx_a, idx_b)
    ])

    alpha = (1 - confidence) / 2

    return (
        float(np.quantile(diffs, alpha)),
        float(np.quantile(diffs, 1 - alpha)),
    )


def summarize_records(records, wall_time=None):
    """Aggregate canonical run records (see src.experiments.runs).

    Latency and TTFT statistics use successful requests only; errors are
    counted separately. TTFT is summarized only for records that measured it.
    """
    ok = [r for r in records if not r["error"]]

    latencies = [r["total_latency"] for r in ok]
    ttfts = [r["ttft"] for r in ok if r["ttft"] is not None]
    costs = [r["cost"] for r in records]

    total_cost = (
        None
        if any(c is None for c in costs)
        else float(sum(costs))
    )

    summary = {
        "requests": len(records),
        "successful": len(ok),
        "errors": len(records) - len(ok),
        "error_rate": (
            (len(records) - len(ok)) / len(records)
            if records
            else 0.0
        ),
        "cache_hits": sum(1 for r in records if r["cache_hit"]),
        "latency_mean": mean(latencies),
        "latency_p50": percentile(latencies, 50),
        "latency_p95": percentile(latencies, 95),
        "latency_p99": percentile(latencies, 99),
        "ttft_measured": len(ttfts),
        "ttft_mean": mean(ttfts),
        "ttft_p50": percentile(ttfts, 50),
        "ttft_p95": percentile(ttfts, 95),
        "input_tokens": sum(r["input_tokens"] for r in records),
        "output_tokens": sum(r["output_tokens"] for r in records),
        "total_cost": total_cost,
        "average_cost": (
            total_cost / len(records)
            if total_cost is not None and records
            else None
        ),
        "parse_failures": sum(1 for r in ok if not r["parse_success"]),
        "schema_failures": sum(1 for r in ok if not r["schema_valid"]),
        "wall_time": wall_time,
        "throughput": (
            len(records) / wall_time
            if wall_time
            else None
        ),
    }

    return summary
