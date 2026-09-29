from dataclasses import dataclass


@dataclass
class GenerationResult:
    text: str
    input_tokens: int
    output_tokens: int
    ttft: float
    total_latency: float


class Provider:
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 500,
    ) -> GenerationResult:
        raise NotImplementedError