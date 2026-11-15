"""Model comparison: the baseline configuration with a different model.

Any model listed in data/pricing.yaml can be used.

    python -m scripts.run_model_comparison --provider openai --model gpt-6-luna
"""

import argparse

from src.experiments.harness import (
    add_common_args,
    configs_from_args,
    run_experiment,
)


def main():
    parser = argparse.ArgumentParser(
        description="Run one model on the frozen workload for comparison."
    )
    add_common_args(parser)
    args = parser.parse_args()

    if args.model is None:
        parser.error("--model is required for a model comparison.")

    for config in configs_from_args("model_comparison", args):
        run_experiment(config)


if __name__ == "__main__":
    main()
