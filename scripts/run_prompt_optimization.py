"""Prompt optimization: the baseline configuration with another prompt version.

The version selects both data/policy/policy-<v>.txt and
data/prompts/tickets-<v>.txt. Prices come from data/pricing.yaml.

    python -m scripts.run_prompt_optimization --provider openai
    python -m scripts.run_prompt_optimization --provider openai --prompt-version v1
"""

import argparse

from src.experiments.harness import (
    add_common_args,
    configs_from_args,
    run_experiment,
)


def main():
    parser = argparse.ArgumentParser(
        description="Run LLMForge prompt optimization."
    )
    add_common_args(parser)
    parser.set_defaults(prompt_version="v2")
    args = parser.parse_args()

    for config in configs_from_args("prompt_optimization", args):
        run_experiment(config)


if __name__ == "__main__":
    main()
