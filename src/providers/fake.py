import time

from src.providers.base import GenerationResult, Provider


class FakeProvider(Provider):
    """Deterministic provider for infrastructure experiments (no API cost).

    It returns the whole response at once, so TTFT equals total latency
    whether or not streaming is requested.
    """

    def __init__(
        self,
        response,
        input_tokens=100,
        output_tokens=50,
        latency=0.0,
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
        stream: bool = False,
    ) -> GenerationResult:

        start = time.perf_counter()

        time.sleep(self.latency)

        total_latency = time.perf_counter() - start

        return GenerationResult(
            text=self.response,
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
            ttft=total_latency,
            total_latency=total_latency,
        )
