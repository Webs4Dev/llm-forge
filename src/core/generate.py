from pathlib import Path

from providers.base import GenerationResult, Provider


PROJECT_ROOT = Path(__file__).resolve().parents[2]

POLICY_PATH = PROJECT_ROOT / "data" / "policy" / "policy-v1.txt"
PROMPT_PATH = PROJECT_ROOT / "data" / "prompts" / "tickets-v1.txt"


def load_policy() -> str:
    return POLICY_PATH.read_text(encoding="utf-8")


def load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def build_user_prompt(ticket_text: str) -> str:
    prompt_template = load_prompt()

    return prompt_template.replace(
        "{{ticket_text}}",
        ticket_text,
    )


def generate(
    provider: Provider,
    ticket_text: str,
    temperature: float = 0.0,
    max_tokens: int = 500,
) -> GenerationResult:

    policy = load_policy()
    user_prompt = build_user_prompt(ticket_text)

    return provider.generate(
        system_prompt=policy,
        user_prompt=user_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
    )