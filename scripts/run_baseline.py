import argparse
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src.core.generate import generate
from src.core.cost import calculate_cost, load_pricing
from src.core.schema import validate_output
from src.providers.fake import FakeProvider
from src.providers.openai import OpenAIProvider
from src.providers.anthropic import AnthropicProvider


WORKLOAD_PATH = (
    PROJECT_ROOT
    / "data"
    / "workloads"
    / "workload-300.jsonl"
)

PRICING_PATH = (
    PROJECT_ROOT
    / "data"
    / "pricing.yaml"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "runs"
)

TOTAL_REQUESTS = 300


def load_workload():
    workload = []

    with open(
        WORKLOAD_PATH,
        "r",
        encoding="utf-8",
    ) as file:

        for line in file:
            if line.strip():
                workload.append(
                    json.loads(line)
                )

    if len(workload) != TOTAL_REQUESTS:
        raise ValueError(
            f"Expected {TOTAL_REQUESTS} requests "
            f"but found {len(workload)}."
        )

    return workload


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
                "suggested_reply": (
                    "This is a fake provider response."
                ),
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

    pricing = load_pricing(
        PRICING_PATH
    )

    model_name = get_model_name(
        provider_name
    )

    if model_name not in pricing["models"]:
        raise ValueError(
            f"No pricing found for model: "
            f"{model_name}"
        )

    model_pricing = pricing["models"][
        model_name
    ]

    return (
        model_pricing[
            "input_per_1m_tokens"
        ],
        model_pricing[
            "output_per_1m_tokens"
        ],
    )


def run_baseline(
    provider_name,
    limit=None,
):

    workload = load_workload()

    # --limit is only for small sanity tests.
    # The actual 300-request baseline uses
    # the complete frozen workload.

    if limit is not None:

        if limit <= 0:
            raise ValueError(
                "--limit must be greater than 0."
            )

        if limit > len(workload):
            raise ValueError(
                f"--limit cannot be greater than "
                f"the workload size "
                f"({len(workload)})."
            )

        workload = workload[:limit]

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    provider = create_provider(
        provider_name
    )

    model_name = get_model_name(
        provider_name
    )

    input_price, output_price = get_pricing(
        provider_name
    )

    output_path = (
        OUTPUT_DIR
        / f"baseline_{provider_name}.jsonl"
    )

    total_requests = 0
    total_cost = 0.0

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as output_file:

        for request in workload:

            request_index = request[
                "request_index"
            ]

            case_id = request[
                "case_id"
            ]

            ticket_text = request[
                "ticket_text"
            ]

            start = time.perf_counter()

            result = generate(
                provider=provider,
                ticket_text=ticket_text,
                temperature=0.0,
                max_tokens=500,
            )

            end = time.perf_counter()

            measured_latency = (
                end - start
            )

            cost = calculate_cost(
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                input_price_per_1m=input_price,
                output_price_per_1m=output_price,
            )

            parse_success = is_valid_json(
                result.text
            )

            schema_valid, schema_error = (
                validate_output(
                    result.text
                )
            )

            record = {
                "request_index": request_index,
                "case_id": case_id,
                "provider": provider_name,
                "model": model_name,
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
                "ttft": result.ttft,
                "total_latency": measured_latency,
                "cost": cost,
                "raw_output": result.text,
                "parse_success": parse_success,
                "schema_valid": schema_valid,
                "schema_error": schema_error,
            }

            output_file.write(
                json.dumps(record)
                + "\n"
            )

            output_file.flush()

            total_requests += 1
            total_cost += cost

            print(
                f"{request_index:03d}/"
                f"{len(workload)} | "
                f"{case_id} | "
                f"provider={provider_name} | "
                f"latency="
                f"{measured_latency:.4f}s"
            )

    average_cost = (
        total_cost / total_requests
        if total_requests
        else 0.0
    )

    print()
    print("Baseline complete.")
    print(
        f"Provider: {provider_name}"
    )
    print(
        f"Model: {model_name}"
    )
    print(
        f"Requests: {total_requests}"
    )
    print(
        f"Total cost: ${total_cost:.8f}"
    )
    print(
        f"Average cost/request: "
        f"${average_cost:.8f}"
    )
    print(
        f"Output: {output_path}"
    )


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Run the LLMForge baseline "
            "using the frozen workload."
        )
    )

    parser.add_argument(
        "--provider",
        choices=[
            "fake",
            "openai",
            "anthropic",
        ],
        required=True,
        help="Provider to use.",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help=(
            "Optional number of workload "
            "requests for a small sanity test."
        ),
    )

    args = parser.parse_args()

    run_baseline(
        provider_name=args.provider,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()