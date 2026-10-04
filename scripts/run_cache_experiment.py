import argparse
import json
import random
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))


from src.core.generate import generate
from src.core.cost import calculate_cost, load_pricing
from src.core.schema import validate_output
from src.optimization.cache.redis_cache import RedisExactCache
from src.providers.fake import FakeProvider
from src.providers.openai import OpenAIProvider
from src.providers.anthropic import AnthropicProvider


DATASET_PATH = (
    PROJECT_ROOT
    / "data"
    / "datasets"
    / "tickets-seed.jsonl"
)

PRICING_PATH = PROJECT_ROOT / "data" / "pricing.yaml"

OUTPUT_DIR = PROJECT_ROOT / "data" / "runs"

TOTAL_REQUESTS = 150
SEED = 42


def load_tickets():
    tickets = []

    with open(
        DATASET_PATH,
        "r",
        encoding="utf-8",
    ) as file:

        for line in file:
            if line.strip():
                tickets.append(
                    json.loads(line)
                )

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

    model_pricing = pricing["models"][model_name]

    return (
        model_pricing["input_per_1m_tokens"],
        model_pricing["output_per_1m_tokens"],
    )


def build_workload(tickets, duplicate_rate):
    rng = random.Random(SEED)

    if not tickets:
        raise ValueError("No tickets available.")

    # We need at least one occurrence of every ticket
    # so that we have a pool of previously seen tickets.
    unique_workload = tickets.copy()

    remaining_requests = TOTAL_REQUESTS - len(
        unique_workload
    )

    duplicate_count = round(
        remaining_requests * duplicate_rate
    )

    new_count = (
        remaining_requests - duplicate_count
    )

    workload = []

    # First occurrence of every ticket.
    workload.extend(
        (ticket, False)
        for ticket in unique_workload
    )

    # Add intentionally duplicated requests.
    for _ in range(duplicate_count):
        ticket = rng.choice(
            unique_workload
        )

        workload.append(
            (ticket, True)
        )

    # Add the remaining requests.
    # These are also selected from the 30-ticket
    # dataset, but they are marked False because
    # they are not intentionally generated as duplicates.
    for _ in range(new_count):
        ticket = rng.choice(
            unique_workload
        )

        workload.append(
            (ticket, False)
        )

    rng.shuffle(workload)

    return workload


def calculate_duplicate_rate(
    duplicate_flags,
):
    if not duplicate_flags:
        return 0.0

    duplicates = sum(
        duplicate_flags
    )

    return duplicates / len(
        duplicate_flags
    )


def run_cache_experiment(
    provider_name,
    duplicate_rate,
    limit=None,
):

    tickets = load_tickets()

    if limit is not None:

        if limit <= 0:
            raise ValueError(
                "--limit must be greater than 0."
            )

        tickets = tickets[:limit]

    if not tickets:
        raise ValueError(
            "No tickets available."
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

    cache = RedisExactCache(
        url="redis://localhost:6380/0",
        ttl=3600,
    )

    # Start every experiment with an empty cache.
    cache.clear()

    workload = build_workload(
        tickets=tickets,
        duplicate_rate=duplicate_rate,
    )

    duplicate_flags = [
        item[1]
        for item in workload
    ]

    actual_duplicate_rate = (
        calculate_duplicate_rate(
            duplicate_flags
        )
    )

    print(
        f"Requested duplicate rate: "
        f"{duplicate_rate:.0%}"
    )

    print(
        f"Actual duplicate rate:    "
        f"{actual_duplicate_rate:.2%}"
    )

    print()

    duplicate_label = int(
        duplicate_rate * 100
    )

    output_path = (
        OUTPUT_DIR
        / f"cache_{provider_name}_"
        f"{duplicate_label}pct.jsonl"
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    total_requests = 0
    total_cost = 0.0
    llm_calls = 0

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as output_file:

        for (
            request_index,
            item,
        ) in enumerate(
            workload,
            start=1,
        ):

            ticket, intentional_duplicate = item

            case_id = ticket["case_id"]

            ticket_text = ticket[
                "input"
            ][
                "ticket_text"
            ]

            hits_before = cache.hits
            misses_before = cache.misses

            start = time.perf_counter()

            result = generate(
                provider=provider,
                ticket_text=ticket_text,
                temperature=0.0,
                max_tokens=500,
                cache=cache,
            )

            end = time.perf_counter()

            total_latency = (
                end - start
            )

            cache_hit = (
                cache.hits > hits_before
            )

            cache_miss = (
                cache.misses > misses_before
            )

            if cache_miss:
                llm_calls += 1

            cost = calculate_cost(
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                input_price_per_1m=input_price,
                output_price_per_1m=output_price,
            )

            total_cost += cost

            parse_success = is_valid_json(
                result.text
            )

            schema_valid, schema_error = (
                validate_output(
                    result.text
                )
            )

            record = {
                "provider": provider_name,
                "model": model_name,

                "requested_duplicate_rate": (
                    duplicate_rate
                ),

                "actual_duplicate_rate": (
                    actual_duplicate_rate
                ),

                "request_index": (
                    request_index
                ),

                "case_id": case_id,

                "intentional_duplicate": (
                    intentional_duplicate
                ),

                "cache_hit": cache_hit,
                "cache_miss": cache_miss,

                "input_tokens": (
                    result.input_tokens
                ),

                "output_tokens": (
                    result.output_tokens
                ),

                "ttft": result.ttft,

                "total_latency": (
                    total_latency
                ),

                "cost": cost,

                "raw_output": result.text,

                "parse_success": (
                    parse_success
                ),

                "schema_valid": (
                    schema_valid
                ),

                "schema_error": (
                    schema_error
                ),
            }

            output_file.write(
                json.dumps(record)
                + "\n"
            )

            total_requests += 1

            print(
                f"{request_index:03d} | "
                f"{case_id} | "
                f"{'DUP' if intentional_duplicate else 'NEW'} | "
                f"{'HIT' if cache_hit else 'MISS'} | "
                f"{total_latency:.4f}s"
            )

    hit_rate = (
        cache.hits / total_requests
        if total_requests > 0
        else 0.0
    )

    print()

    print(
        "Cache experiment complete."
    )

    print(
        f"Provider: {provider_name}"
    )

    print(
        f"Model: {model_name}"
    )

    print(
        f"Requested duplicate rate: "
        f"{duplicate_rate:.0%}"
    )

    print(
        f"Actual duplicate rate: "
        f"{actual_duplicate_rate:.2%}"
    )

    print(
        f"Total requests: "
        f"{total_requests}"
    )

    print(
        f"LLM calls: "
        f"{llm_calls}"
    )

    print(
        f"Cache hits: "
        f"{cache.hits}"
    )

    print(
        f"Cache misses: "
        f"{cache.misses}"
    )

    print(
        f"Cache hit rate: "
        f"{hit_rate:.2%}"
    )

    print(
        f"Total cost: "
        f"${total_cost:.8f}"
    )

    print(
        f"Output: "
        f"{output_path}"
    )


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Run the LLMForge Redis "
            "cache experiment."
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
    )

    parser.add_argument(
        "--duplicate-rate",
        type=float,
        choices=[
            0.0,
            0.3,
            0.7,
        ],
        required=True,
        help=(
            "Requested duplicate "
            "workload rate."
        ),
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help=(
            "Limit the number of "
            "seed tickets used."
        ),
    )

    args = parser.parse_args()

    run_cache_experiment(
        provider_name=args.provider,
        duplicate_rate=args.duplicate_rate,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()