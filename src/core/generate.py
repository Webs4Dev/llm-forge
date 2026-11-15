import time
from pathlib import Path

from src.providers.base import GenerationResult
from src.optimization.cache.key import create_cache_key


PROJECT_ROOT = Path(__file__).resolve().parents[2]

POLICY_DIR = PROJECT_ROOT / "data" / "policy"
PROMPT_DIR = PROJECT_ROOT / "data" / "prompts"

DEFAULT_PROMPT_VERSION = "v1"


def policy_path(version: str = DEFAULT_PROMPT_VERSION) -> Path:
    return POLICY_DIR / f"policy-{version}.txt"


def prompt_path(version: str = DEFAULT_PROMPT_VERSION) -> Path:
    return PROMPT_DIR / f"tickets-{version}.txt"


def load_policy(version: str = DEFAULT_PROMPT_VERSION) -> str:
    return policy_path(version).read_text(
        encoding="utf-8"
    )


def load_prompt(version: str = DEFAULT_PROMPT_VERSION) -> str:
    return prompt_path(version).read_text(
        encoding="utf-8"
    )


def build_user_prompt(
    ticket_text: str,
    version: str = DEFAULT_PROMPT_VERSION,
) -> str:
    prompt_template = load_prompt(version)

    return prompt_template.replace(
        "{{ticket_text}}",
        ticket_text,
    )


def generate(
    provider,
    ticket_text,
    temperature=0.0,
    max_tokens=500,
    cache=None,
    prompt_version=DEFAULT_PROMPT_VERSION,
    stream=False,
):
    """Run one ticket through the provider, optionally via an exact cache.

    `prompt_version` selects both the system policy and the user prompt
    template (policy-<v>.txt and tickets-<v>.txt). `cache` is any object with
    get(key) and set(key, value).
    """
    policy = load_policy(prompt_version)

    user_prompt = build_user_prompt(
        ticket_text,
        prompt_version,
    )

    if cache is not None:

        cache_key = create_cache_key(
            system_prompt=policy,
            user_prompt=user_prompt,
            model=provider.model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        lookup_start = time.perf_counter()

        cached_text = cache.get(
            cache_key
        )

        lookup_latency = time.perf_counter() - lookup_start

        if cached_text is not None:

            # No tokens were billed; latency is the real cache lookup time.
            return GenerationResult(
                text=cached_text,
                input_tokens=0,
                output_tokens=0,
                ttft=lookup_latency,
                total_latency=lookup_latency,
                cache_hit=True,
            )

    result = provider.generate(
        system_prompt=policy,
        user_prompt=user_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=stream,
    )

    if cache is not None:

        cache.set(
            cache_key,
            result.text,
        )

    return result
