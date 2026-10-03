import time

from src.providers.base import GenerationResult, Provider


class FakeProvider(Provider):
    def __init__(
        self,
        response,
        input_tokens,
        output_tokens,
        latency,
    ):
        self.model = "fake"
        self.response = response
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.latency = latency

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 500,
    ) -> GenerationResult:

        start = time.perf_counter()

        time.sleep(self.latency)

        end = time.perf_counter()

        total_latency = end - start

        return GenerationResult(
            text=self.response,
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
            ttft=total_latency,
            total_latency=total_latency,
        )