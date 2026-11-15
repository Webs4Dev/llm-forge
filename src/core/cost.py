from pathlib import Path

import yaml


PRICING_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "pricing.yaml"
)


def load_pricing(path=PRICING_PATH) -> dict:
    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def get_model_prices(model: str, path=PRICING_PATH) -> tuple:
    """Return (input_per_1m, output_per_1m) for a model from pricing.yaml."""
    models = load_pricing(path)["models"]

    if model not in models:
        raise ValueError(
            f"No pricing for model '{model}' in {path}. "
            f"Add it before running."
        )

    prices = models[model]

    return (
        prices["input_per_1m_tokens"],
        prices["output_per_1m_tokens"],
    )


def calculate_cost(
    input_tokens: int,
    output_tokens: int,
    input_price_per_1m: float,
    output_price_per_1m: float,
) -> float:

    input_cost = (input_tokens / 1_000_000) * input_price_per_1m
    output_cost = (output_tokens / 1_000_000) * output_price_per_1m

    return input_cost + output_cost
