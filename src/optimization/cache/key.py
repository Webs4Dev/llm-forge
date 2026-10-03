import hashlib


def create_cache_key(
    system_prompt: str,
    user_prompt: str,
    model: str,
    temperature: float,
    max_tokens: int,
) -> str:

    content = (
        f"model={model}\n"
        f"temperature={temperature}\n"
        f"max_tokens={max_tokens}\n"
        f"system={system_prompt}\n"
        f"user={user_prompt}"
    )

    return hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()