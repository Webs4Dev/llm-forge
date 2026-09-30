import os
import time

from dotenv import load_dotenv
from anthropic import Anthropic

from providers.base import GenerationResult, Provider

load_dotenv()


class AnthropicProvider(Provider):
    def __init__(self, model: str):
        self.model = model

        api_key = os.getenv("ANTHROPIC_API_KEY")

        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is not set in the environment."
            )

        self.client = Anthropic(api_key=api_key)

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 500,
    ) -> GenerationResult:

        start = time.perf_counter()

        response = self.client.messages.create(
            model=self.model,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": user_prompt,
                }
            ],
            max_tokens=max_tokens,
        )

        end = time.perf_counter()

        total_latency = end - start

        text = ""

        if response.content:
            text = response.content[0].text

        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens

        return GenerationResult(
            text=text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            ttft=total_latency,
            total_latency=total_latency,
        )