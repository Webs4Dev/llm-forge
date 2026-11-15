import os
import time

from dotenv import load_dotenv
from anthropic import Anthropic

from src.core.schema import TICKET_OUTPUT_SCHEMA
from src.providers.base import GenerationResult, Provider

load_dotenv()


# Explicit so they are recorded in run metadata. max_retries=2 matches the
# SDK default used by all earlier runs; the SDK default timeout is 10 minutes,
# which would let a single hung request stall an experiment.
DEFAULT_TIMEOUT_SECONDS = 60.0
DEFAULT_MAX_RETRIES = 2


class AnthropicProvider(Provider):

    def __init__(
        self,
        model: str,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ):
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries

        api_key = os.getenv("ANTHROPIC_API_KEY")

        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is not set in the environment."
            )

        self.client = Anthropic(
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries,
        )

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 500,
        stream: bool = False,
    ) -> GenerationResult:
        # Note: temperature is accepted for interface compatibility but is not
        # sent, exactly as in all recorded runs (the API default is used).

        request = {
            "model": self.model,
            "system": system_prompt,
            "messages": [
                {
                    "role": "user",
                    "content": user_prompt,
                }
            ],
            "max_tokens": max_tokens,
            "output_config": {
                "format": {
                    "type": "json_schema",
                    "schema": TICKET_OUTPUT_SCHEMA,
                }
            },
        }

        if stream:
            return self._generate_streaming(request)

        start = time.perf_counter()

        response = self.client.messages.create(**request)

        total_latency = time.perf_counter() - start

        text = ""

        if response.content:
            text = response.content[0].text

        return GenerationResult(
            text=text,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            ttft=None,
            total_latency=total_latency,
        )

    def _generate_streaming(self, request) -> GenerationResult:
        start = time.perf_counter()
        ttft = None

        with self.client.messages.stream(**request) as stream:
            for _ in stream.text_stream:
                if ttft is None:
                    ttft = time.perf_counter() - start

            message = stream.get_final_message()

        total_latency = time.perf_counter() - start

        text = "".join(
            block.text
            for block in message.content
            if block.type == "text"
        )

        return GenerationResult(
            text=text,
            input_tokens=message.usage.input_tokens,
            output_tokens=message.usage.output_tokens,
            ttft=ttft,
            total_latency=total_latency,
        )
