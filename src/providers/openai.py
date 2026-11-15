import os
import time

from dotenv import load_dotenv
from openai import OpenAI

from src.core.schema import TICKET_OUTPUT_SCHEMA
from src.providers.base import GenerationResult, Provider

load_dotenv()


# Explicit so they are recorded in run metadata. max_retries=2 matches the
# SDK default used by all earlier runs.
DEFAULT_TIMEOUT_SECONDS = 60.0
DEFAULT_MAX_RETRIES = 2


class OpenAIProvider(Provider):

    def __init__(
        self,
        model: str,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ):
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries

        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY is not set in the environment."
            )

        self.client = OpenAI(
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
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "support_ticket",
                    "strict": True,
                    "schema": TICKET_OUTPUT_SCHEMA,
                },
            },
            "max_completion_tokens": max_tokens,
        }

        if stream:
            return self._generate_streaming(request)

        start = time.perf_counter()

        response = self.client.chat.completions.create(**request)

        total_latency = time.perf_counter() - start

        return GenerationResult(
            text=response.choices[0].message.content or "",
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
            ttft=None,
            total_latency=total_latency,
        )

    def _generate_streaming(self, request) -> GenerationResult:
        start = time.perf_counter()
        ttft = None
        parts = []
        usage = None

        chunks = self.client.chat.completions.create(
            **request,
            stream=True,
            # Usage arrives in a final chunk with an empty choices list.
            stream_options={"include_usage": True},
        )

        for chunk in chunks:
            if chunk.usage is not None:
                usage = chunk.usage

            if not chunk.choices:
                continue

            content = chunk.choices[0].delta.content

            if content:
                if ttft is None:
                    ttft = time.perf_counter() - start

                parts.append(content)

        total_latency = time.perf_counter() - start

        if usage is None:
            raise RuntimeError(
                "OpenAI stream ended without a usage chunk."
            )

        return GenerationResult(
            text="".join(parts),
            input_tokens=usage.prompt_tokens,
            output_tokens=usage.completion_tokens,
            ttft=ttft,
            total_latency=total_latency,
        )
