"""Provider logic tested against stub clients (no network, no API cost).

These check our handling of the SDK response shapes; they cannot prove the
real APIs behave the same. The paid smoke scripts in scripts/smoke/ do that.
"""

from contextlib import contextmanager
from types import SimpleNamespace as NS

from src.core.schema import TICKET_OUTPUT_SCHEMA
from src.providers.anthropic import AnthropicProvider
from src.providers.openai import OpenAIProvider


def make(provider_class, client):
    provider = provider_class.__new__(provider_class)  # skip API key lookup
    provider.model = "test-model"
    provider.client = client
    return provider


class AnthropicStub:
    def __init__(self):
        self.requests = []
        self.messages = self

    def create(self, **request):
        self.requests.append(request)
        return NS(
            content=[NS(type="text", text='{"a": 1}')],
            usage=NS(input_tokens=11, output_tokens=7),
        )

    @contextmanager
    def stream(self, **request):
        self.requests.append(request)
        yield NS(
            text_stream=iter(['{"a"', ": 1}"]),
            get_final_message=lambda: NS(
                content=[NS(type="text", text='{"a": 1}')],
                usage=NS(input_tokens=11, output_tokens=7),
            ),
        )


def test_anthropic_non_streaming_has_no_ttft():
    client = AnthropicStub()
    result = make(AnthropicProvider, client).generate("sys", "user")

    assert result.text == '{"a": 1}'
    assert result.ttft is None
    assert client.requests[0]["output_config"]["format"]["schema"] == (
        TICKET_OUTPUT_SCHEMA
    )
    assert "temperature" not in client.requests[0]


def test_anthropic_streaming_measures_ttft_and_usage():
    client = AnthropicStub()
    result = make(AnthropicProvider, client).generate(
        "sys",
        "user",
        stream=True,
    )

    assert result.text == '{"a": 1}'
    assert result.input_tokens == 11
    assert result.output_tokens == 7
    assert 0 <= result.ttft <= result.total_latency
    assert client.requests[0]["output_config"]["format"]["type"] == (
        "json_schema"
    )


class OpenAIStub:
    def __init__(self):
        self.requests = []
        self.chat = NS(completions=self)

    def create(self, **request):
        self.requests.append(request)
        usage = NS(prompt_tokens=20, completion_tokens=9)

        if not request.get("stream"):
            return NS(
                choices=[NS(message=NS(content='{"b": 2}'))],
                usage=usage,
            )

        return iter([
            NS(choices=[NS(delta=NS(content=None))], usage=None),
            NS(choices=[NS(delta=NS(content='{"b"'))], usage=None),
            NS(choices=[NS(delta=NS(content=": 2}"))], usage=None),
            NS(choices=[], usage=usage),
        ])


def test_openai_non_streaming_has_no_ttft():
    client = OpenAIStub()
    result = make(OpenAIProvider, client).generate("sys", "user")

    assert result.text == '{"b": 2}'
    assert result.ttft is None
    assert "stream" not in client.requests[0]


def test_openai_streaming_measures_ttft_and_usage():
    client = OpenAIStub()
    result = make(OpenAIProvider, client).generate(
        "sys",
        "user",
        stream=True,
    )

    assert result.text == '{"b": 2}'
    assert result.input_tokens == 20
    assert result.output_tokens == 9
    assert 0 <= result.ttft <= result.total_latency
    assert client.requests[0]["stream_options"] == {"include_usage": True}
