from dataclasses import dataclass
from typing import Optional


@dataclass
class GenerationResult:
    text: str
    input_tokens: int
    output_tokens: int
    # Time to first token. Only measurable when the response is streamed;
    # None for non-streamed calls so it is never confused with total latency.
    ttft: Optional[float]
    total_latency: float
    cache_hit: bool = False


class Provider:
    model: str

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 500,
        stream: bool = False,
    ) -> GenerationResult:
        raise NotImplementedError
