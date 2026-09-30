import argparse
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from core.generate import generate
from core.cost import calculate_cost, load_pricing
from core.schema import validate_output
from providers.fake import FakeProvider
from providers.openai import OpenAIProvider
from providers.anthropic import AnthropicProvider


DATASET_PATH = PROJECT_ROOT / "data" / "datasets" / "tickets-seed.jsonl"
PRICING_PATH = PROJECT_ROOT / "data" / "pricing.yaml"
OUTPUT_DIR = PROJECT_ROOT / "data" / "runs"

REPEATS = 5


def load_tickets():
    tickets = []

    with open(DATASET_PATH, "r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                tickets.append(json.loads(line))

    return tickets


def is_valid_json(text):
    try:
        json.loads(text)
        return True
    except json.JSONDecodeError:
        return False


def create_provider(provider_name):
    if provider_name == "fake":
        return FakeProvider(
            response=json.dumps({
                "category": "general",
                "urgency": "low",
                "summary": "Fake provider response.",
                "suggested_reply": "This is a fake provider response.",
                "needs_escalation": False,
            }),
            input_tokens=100,
            output_tokens=50,
            latency=0.1,
        )

    if provider_name == "openai":
        return OpenAIProvider(
            model="gpt-5.6-luna"
        )

    if provider_name == "anthropic":
        return AnthropicProvider(
            model="claude-haiku-4-5"
        )

    raise ValueError(
        f"Unsupported provider: {provider_name}"
    )


def get_model_name(provider_name):
    if provider_name == "openai":
        return "gpt-5.6-luna"

    if provider_name == "anthropic":
        return "claude-haiku-4-5"

    return "fake"


def get_pricing(provider_name):
    pricing = load_pricing(PRICING_PATH)

    model_name = get_model_name(provider_name)

    if model_name not in pricing["models"]:
        raise ValueError(
            f"No pricing found for model: {model_name}"
        )

    model_pricing = pricing["models"][model_name]

    return (
        model_pricing["input_per_1m_tokens"],
        model_pricing["output_per_1m_tokens"],
    )


def run_baseline(provider_name, limit=None):

    if provider_name in {"openai", "anthropic"} and limit is None:
        raise ValueError(
            f"For {provider_name}, you must specify --limit "
            "to avoid accidentally making a large number "
            "of API requests."
        )

    tickets = load_tickets()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    provider = create_provider(provider_name)

    model_name = get_model_name(provider_name)

    input_price, output_price = get_pricing(
        provider_name
    )

    output_path = (
        OUTPUT_DIR
        / f"baseline_{provider_name}.jsonl"
    )

    total_requests = 0

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as output_file:

        for ticket in tickets:

            case_id = ticket["case_id"]

            ticket_text = ticket["input"]["ticket_text"]

            for repeat in range(1, REPEATS + 1):

                if (
                    limit is not None
                    and total_requests >= limit
                ):
                    break

                start = time.perf_counter()

                result = generate(
                    provider=provider,
                    ticket_text=ticket_text,
                    temperature=0.0,
                    max_tokens=500,
                )

                end = time.perf_counter()

                total_latency = end - start

                cost = calculate_cost(
                    input_tokens=result.input_tokens,
                    output_tokens=result.output_tokens,
                    input_price_per_1m=input_price,
                    output_price_per_1m=output_price,
                )

                parse_success = is_valid_json(
                    result.text
                )

                schema_valid, schema_error = validate_output(
                    result.text
                )

                record = {
                    "provider": provider_name,
                    "model": model_name,
                    "case_id": case_id,
                    "repeat": repeat,
                    "input_tokens": result.input_tokens,
                    "output_tokens": result.output_tokens,
                    "ttft": result.ttft,
                    "total_latency": total_latency,
                    "cost": cost,
                    "raw_output": result.text,
                    "parse_success": parse_success,
                    "schema_valid": schema_valid,
                    "schema_error": schema_error,
                }

                output_file.write(
                    json.dumps(record) + "\n"
                )

                total_requests += 1

                print(
                    f"{case_id} | "
                    f"repeat={repeat} | "
                    f"provider={provider_name} | "
                    f"latency={total_latency:.4f}s"
                )

    print()
    print("Baseline complete.")
    print(f"Provider: {provider_name}")
    print(f"Model: {model_name}")
    print(f"Total requests: {total_requests}")
    print(f"Output: {output_path}")


def main():

    parser = argparse.ArgumentParser(
        description="Run the LLMForge baseline workload."
    )

    parser.add_argument(
        "--provider",
        choices=[
            "fake",
            "openai",
            "anthropic",
        ],
        required=True,
        help="Provider to use for the baseline run.",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of requests to run.",
    )

    args = parser.parse_args()

    run_baseline(
        provider_name=args.provider,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()