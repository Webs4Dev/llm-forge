"""Concurrency: the baseline configuration at several concurrency levels.

Unlike the original version of this script, requests now use the same
policy and prompt template as the baseline, so results are comparable.

    python -m scripts.run_concurrency --provider fake
    python -m scripts.run_concurrency --provider openai --levels 1 5 --unique
"""

import argparse

from src.experiments.harness import (
    add_common_args,
    configs_from_args,
    run_experiment,
)


DEFAULT_LEVELS = [1, 2, 5, 10]


def _fmt(value):
    return "n/a" if value is None else f"{value:.4f}"


def main():
    parser = argparse.ArgumentParser(
        description="Run the LLMForge concurrency experiment."
    )
    add_common_args(parser)
    parser.add_argument(
        "--levels",
        type=int,
        nargs="+",
        default=DEFAULT_LEVELS,
    )
    args = parser.parse_args()

    rows = []

    for level in args.levels:
        for config in configs_from_args(
            "concurrency",
            args,
            concurrency=level,
        ):
            _, _, summary = run_experiment(config)
            rows.append((level, config.repeat, summary))

    print()
    print(
        f"{'Level':<7}{'Repeat':<8}{'Wall s':<10}{'Req/s':<8}"
        f"{'Mean':<9}{'P50':<9}{'P95':<9}{'P99':<9}{'Errors':<7}"
    )

    for level, repeat, s in rows:
        print(
            f"{level:<7}{repeat:<8}{s['wall_time']:<10.2f}"
            f"{s['throughput']:<8.2f}{_fmt(s['latency_mean']):<9}"
            f"{_fmt(s['latency_p50']):<9}{_fmt(s['latency_p95']):<9}"
            f"{_fmt(s['latency_p99']):<9}{s['errors']:<7}"
        )


if __name__ == "__main__":
    main()
