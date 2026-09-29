from src.core.cost import calculate_cost


def test_calculate_cost():
    cost = calculate_cost(
        input_tokens=1000,
        output_tokens=200,
        input_price_per_1m=1.0,
        output_price_per_1m=5.0,
    )

    assert cost == 0.002


def test_zero_tokens():
    cost = calculate_cost(
        input_tokens=0,
        output_tokens=0,
        input_price_per_1m=1.0,
        output_price_per_1m=5.0,
    )

    assert cost == 0.0


def test_input_cost_only():
    cost = calculate_cost(
        input_tokens=1_000_000,
        output_tokens=0,
        input_price_per_1m=2.0,
        output_price_per_1m=5.0,
    )

    assert cost == 2.0


def test_output_cost_only():
    cost = calculate_cost(
        input_tokens=0,
        output_tokens=1_000_000,
        input_price_per_1m=2.0,
        output_price_per_1m=5.0,
    )

    assert cost == 5.0