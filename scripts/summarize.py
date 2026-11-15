"""Summarize run files with 95% bootstrap confidence intervals.

    python -m scripts.summarize --provider openai           # old baseline file
    python -m scripts.summarize <run_file> [<run_file> ...]
    python -m scripts.summarize --compare <run_a> <run_b>   # is B different from A?

The intervals show sampling noise across requests within a run. They do not
show drift between runs on different days; repeat runs (--repeats) for that.
"""

import argparse
from pathlib import Path

import numpy as np

from src.experiments.harness import print_summary
from src.experiments.runs import load_metadata, load_run
from src.experiments.stats import (
    bootstrap_ci,
    bootstrap_diff_ci,
    summarize_records,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = PROJECT_ROOT / "data" / "runs"

STATISTICS = {
    "mean": np.mean,
    "P50": lambda v: np.percentile(v, 50),
    "P95": lambda v: np.percentile(v, 95),
    "P99": lambda v: np.percentile(v, 99),
}


def _resolve(path):
    path = Path(path)
    return path if path.is_absolute() else PROJECT_ROOT / path


def _series(records):
    ok = [r for r in records if not r["error"]]

    series = {
        "latency": [r["total_latency"] for r in ok],
        "ttft": [r["ttft"] for r in ok if r["ttft"] is not None],
    }

    if all(r["cost"] is not None for r in records):
        series["cost/request"] = [r["cost"] for r in records]

    return series


def summarize_file(path):
    records = load_run(path)
    meta = load_metadata(path)

    print("=" * 60)
    print(f"Run: {path.name}")

    if meta:
        config = meta["config"]
        print(
            f"Config: provider={config['provider']} model={config['model']} "
            f"prompt={config['prompt_version']} "
            f"concurrency={config['concurrency']} stream={config['stream']}"
        )
        print(f"Git: {meta.get('git')}")
    else:
        print(
            "No metadata sidecar (run predates the harness). "
            "TTFT was not measured in this run."
        )

    wall_time = meta["summary"]["wall_time"] if meta else None
    print_summary(summarize_records(records, wall_time=wall_time))

    print("95% bootstrap confidence intervals")

    for name, values in _series(records).items():
        if not values:
            continue

        for stat_name in ["mean", "P50", "P95"]:
            stat = STATISTICS[stat_name]
            low, high = bootstrap_ci(values, stat)
            print(
                f"  {name:<13}{stat_name:<5} {stat(np.asarray(values)):.6f}"
                f"  [{low:.6f}, {high:.6f}]"
            )


def compare(path_a, path_b):
    series_a = _series(load_run(path_a))
    series_b = _series(load_run(path_b))

    print("=" * 60)
    print(f"A: {path_a.name}")
    print(f"B: {path_b.name}")
    print("Difference B - A with 95% bootstrap CI")
    print("(an interval that contains 0 means the difference is within noise)")

    for name in series_a:
        a = series_a[name]
        b = series_b.get(name, [])

        if not a or not b:
            continue

        for stat_name in ["mean", "P50", "P95", "P99"]:
            stat = STATISTICS[stat_name]
            diff = stat(np.asarray(b)) - stat(np.asarray(a))
            low, high = bootstrap_diff_ci(a, b, stat)
            verdict = (
                "within noise"
                if low <= 0 <= high
                else ("B higher" if low > 0 else "B lower")
            )
            print(
                f"  {name:<13}{stat_name:<5} {diff:+.6f}"
                f"  [{low:+.6f}, {high:+.6f}]  {verdict}"
            )


def main():
    parser = argparse.ArgumentParser(
        description="Summarize LLMForge run files with confidence intervals."
    )
    parser.add_argument("run_files", nargs="*")
    parser.add_argument(
        "--provider",
        choices=["fake", "openai", "anthropic"],
        help="Shortcut for data/runs/baseline_<provider>.jsonl.",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Compare exactly two run files.",
    )
    args = parser.parse_args()

    paths = [_resolve(p) for p in args.run_files]

    if args.provider:
        paths.append(RUNS_DIR / f"baseline_{args.provider}.jsonl")

    if not paths:
        parser.error("Give one or more run files, or --provider.")

    for path in paths:
        if not path.is_file():
            parser.error(f"Run file not found: {path}")

    if args.compare:
        if len(paths) != 2:
            parser.error("--compare needs exactly two run files.")

        compare(*paths)
        return

    for path in paths:
        summarize_file(path)


if __name__ == "__main__":
    main()
