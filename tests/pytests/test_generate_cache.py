from src.core.generate import generate
from src.providers.fake import FakeProvider


class DictCache:
    def __init__(self):
        self.data = {}

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value):
        self.data[key] = value


def test_second_identical_request_is_a_cache_hit():
    provider = FakeProvider(response="ok", input_tokens=100, output_tokens=50)
    cache = DictCache()

    first = generate(provider, "ticket", cache=cache)
    second = generate(provider, "ticket", cache=cache)

    assert first.cache_hit is False
    assert first.input_tokens == 100

    assert second.cache_hit is True
    assert second.text == "ok"
    assert second.input_tokens == 0
    assert second.output_tokens == 0
    # Lookup time is recorded rather than a hardcoded zero.
    assert second.total_latency > 0


def test_prompt_version_is_part_of_the_cache_key():
    provider = FakeProvider(response="ok")
    cache = DictCache()

    generate(provider, "ticket", cache=cache, prompt_version="v1")
    other = generate(provider, "ticket", cache=cache, prompt_version="v2")

    assert other.cache_hit is False
