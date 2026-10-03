import os
from pathlib import Path

from src.providers.base import GenerationResult, Provider
from src.optimization.cache.key import create_cache_key


PROJECT_ROOT = Path(__file__).resolve().parents[2]

POLICY_PATH = PROJECT_ROOT / "data" / "policy" / "policy-v1.txt"
PROMPT_PATH = PROJECT_ROOT / "data" / "prompts" / "tickets-v1.txt"


def load_policy() -> str:
    return POLICY_PATH.read_text(
        encoding="utf-8"
    )


def load_prompt() -> str:
    return PROMPT_PATH.read_text(
        encoding="utf-8"
    )


def build_user_prompt(ticket_text: str) -> str:
    prompt_template = load_prompt()

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
):
    policy = load_policy()

    user_prompt = build_user_prompt(
        ticket_text
    )

    if cache is not None:

        cache_key = create_cache_key(
            system_prompt=policy,
            user_prompt=user_prompt,
            model=provider.model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        cached_text = cache.get(
            cache_key
        )

        if cached_text is not None:

            return GenerationResult(
                text=cached_text,
                input_tokens=0,
                output_tokens=0,
                ttft=0.0,
                total_latency=0.0,
            )

    result = provider.generate(
        system_prompt=policy,
        user_prompt=user_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    if cache is not None:

        cache.set(
            cache_key,
            result.text,
        )

    return result