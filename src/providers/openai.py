import os
import time

from dotenv import load_dotenv
from openai import OpenAI

from providers.base import GenerationResult, Provider

load_dotenv()


class OpenAIProvider(Provider):

    def __init__(self, model: str):
        self.model = model

        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY is not set in the environment."
            )

        self.client = OpenAI(api_key=api_key)

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 500,
    ) -> GenerationResult:

        start = time.perf_counter()

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "support_ticket",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "enum": [
                                    "billing",
                                    "technical",
                                    "account",
                                    "delivery",
                                    "refund",
                                    "fraud",
                                    "general",
                                ],
                            },
                            "urgency": {
                                "type": "string",
                                "enum": [
                                    "low",
                                    "medium",
                                    "high",
                                ],
                            },
                            "summary": {
                                "type": "string",
                            },
                            "suggested_reply": {
                                "type": "string",
                            },
                            "needs_escalation": {
                                "type": "boolean",
                            },
                        },
                        "required": [
                            "category",
                            "urgency",
                            "summary",
                            "suggested_reply",
                            "needs_escalation",
                        ],
                        "additionalProperties": False,
                    },
                },
            },
            max_completion_tokens=max_tokens,
        )

        end = time.perf_counter()

        total_latency = end - start

        text = response.choices[0].message.content or ""

        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens

        return GenerationResult(
            text=text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            ttft=total_latency,
            total_latency=total_latency,
        )