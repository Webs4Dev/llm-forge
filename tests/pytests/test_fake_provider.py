from src.providers.fake import FakeProvider


def test_fake_provider_returns_response():
    provider = FakeProvider(
        response='{"category":"billing"}'
    )

    result = provider.generate(
        system_prompt="Test system prompt",
        user_prompt="Test user prompt",
    )

    assert result.text == '{"category":"billing"}'


def test_fake_provider_returns_token_counts():
    provider = FakeProvider(
        response="test",
        input_tokens=200,
        output_tokens=50,
    )

    result = provider.generate(
        system_prompt="Test system prompt",
        user_prompt="Test user prompt",
    )

    assert result.input_tokens == 200
    assert result.output_tokens == 50


def test_fake_provider_returns_latency():
    provider = FakeProvider(
        response="test",
        latency=0.01,
    )

    result = provider.generate(
        system_prompt="Test system prompt",
        user_prompt="Test user prompt",
    )

    assert result.total_latency >= 0.01
    assert result.ttft >= 0.01


def test_fake_provider_uses_default_values():
    provider = FakeProvider(
        response="test"
    )

    result = provider.generate(
        system_prompt="Test system prompt",
        user_prompt="Test user prompt",
    )

    assert result.input_tokens == 100
    assert result.output_tokens == 50
    assert result.text == "test"