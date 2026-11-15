"""Baseline: one provider, prompt v1, no cache, sequential requests.

    python -m scripts.run_baseline --provider fake
    python -m scripts.run_baseline --provider openai --unique --repeats 3
"""

import argparse

from src.experiments.harness import (
    add_common_args,
    configs_from_args,
    run_experiment,
)


def main():
    parser = argparse.ArgumentParser(
        description="Run the LLMForge baseline on the frozen workload."
    )
    add_common_args(parser)
    args = parser.parse_args()

    for config in configs_from_args("baseline", args):
        run_experiment(config)


if __name__ == "__main__":
    main()
