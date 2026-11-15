"""Exact cache: baseline plus the Redis exact cache, starting empty.

Needs Redis (docker compose up -d). Uses the full 300-request workload,
because the 200 duplicate requests are what the cache is measured on.

    python -m scripts.run_exact_cache --provider fake
"""

import argparse
import os

from src.experiments.harness import (
    add_common_args,
    configs_from_args,
    run_experiment,
)
from src.optimization.cache.redis_cache import RedisExactCache


DEFAULT_REDIS_URL = "redis://localhost:6380/0"


def main():
    parser = argparse.ArgumentParser(
        description="Run the LLMForge Redis exact-cache experiment."
    )
    add_common_args(parser)
    args = parser.parse_args()

    if args.unique:
        parser.error(
            "--unique removes the duplicate requests the cache relies on."
        )

    redis_url = os.getenv("REDIS_URL", DEFAULT_REDIS_URL)

    for config in configs_from_args("exact_cache", args, cache=True):
        # A separate namespace per provider/model/repeat, emptied first, so
        # parallel runs sharing one Redis cannot interfere with each other.
        cache = RedisExactCache(
            url=redis_url,
            ttl=3600,
            namespace=(
                f"llmforge:{config.provider}:{config.model}:"
                f"{config.prompt_version}:r{config.repeat}"
            ),
        )
        cache.clear()

        run_experiment(config, cache=cache)


if __name__ == "__main__":
    main()
