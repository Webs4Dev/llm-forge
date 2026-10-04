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
from src.optimization.cache.redis_cache import RedisExactCache

from src.providers.fake import FakeProvider
from src.providers.openai import OpenAIProvider
from src.providers.anthropic import AnthropicProvider


WORKLOAD_PATH = (
    PROJECT_ROOT
    / "data"
    / "workloads"
    / "workload-300.jsonl"
)

PRICING_PATH = PROJECT_ROOT / "data" / "pricing.yaml"
OUTPUT_DIR = PROJECT_ROOT / "data" / "runs"

TOTAL_REQUESTS = 300


def load_workload():
    requests = []

    with open(
        WORKLOAD_PATH,
        "r",
        encoding="utf-8",
    ) as file:

        for line in file:
            if line.strip():
                requests.append(json.loads(line))

    if len(requests) != TOTAL_REQUESTS:
        raise ValueError(
            f"Expected {TOTAL_REQUESTS} requests, "
            f"found {len(requests)}"
        )

    return requests


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
    pricing = load_pricing(PRICING_PATH)

    model_name = get_model_name(
        provider_name
    )

    model_pricing = pricing["models"][model_name]

    return (
        model_pricing["input_per_1m_tokens"],
        model_pricing["output_per_1m_tokens"],
    )


def is_valid_json(text):
    try:
        json.loads(text)
        return True

    except json.JSONDecodeError:
        return False


def percentile(values, percentile_value):
    values = sorted(values)

    if not values:
        return 0.0

    index = (
        (len(values) - 1)
        * percentile_value
        / 100
    )

    lower = int(index)
    upper = lower + 1

    if upper >= len(values):
        return values[lower]

    weight = index - lower

    return (
        values[lower]
        + (
            values[upper]
            - values[lower]
        )
        * weight
    )


def run_cache_experiment(provider_name):
    workload = load_workload()

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

    # Start with an empty cache.
    cache.clear()

    output_path = (
        OUTPUT_DIR
        / f"exact_cache_{provider_name}.jsonl"
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    latencies = []
    ttfts = []
    costs = []

    total_input_tokens = 0
    total_output_tokens = 0

    total_cost = 0.0
    llm_calls = 0

    parse_failures = 0
    schema_failures = 0

    cache_hits = 0
    cache_misses = 0

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

            total_latency = (
                time.perf_counter()
                - start
            )

            cache_hit = (
                cache.hits > hits_before
            )

            cache_miss = (
                cache.misses > misses_before
            )

            if cache_hit:
                cache_hits += 1

            if cache_miss:
                cache_misses += 1
                llm_calls += 1

            cost = calculate_cost(
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                input_price_per_1m=input_price,
                output_price_per_1m=output_price,
            )

            total_cost += cost

            total_input_tokens += (
                result.input_tokens
            )

            total_output_tokens += (
                result.output_tokens
            )

            latencies.append(
                total_latency
            )

            ttfts.append(
                result.ttft
            )

            costs.append(cost)

            parse_success = is_valid_json(
                result.text
            )

            schema_valid, schema_error = (
                validate_output(
                    result.text
                )
            )

            if not parse_success:
                parse_failures += 1

            if not schema_valid:
                schema_failures += 1

            record = {
                "provider": provider_name,
                "model": model_name,
                "request_index": request_index,
                "case_id": case_id,
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

            output_file.flush()

            print(
                f"{request_index:03d} | "
                f"{case_id} | "
                f"{'HIT' if cache_hit else 'MISS'} | "
                f"{total_latency:.4f}s"
            )

    total_requests = len(workload)

    hit_rate = (
        cache_hits / total_requests
        if total_requests > 0
        else 0.0
    )

    miss_rate = (
        cache_misses / total_requests
        if total_requests > 0
        else 0.0
    )

    average_latency = (
        sum(latencies)
        / len(latencies)
    )

    average_ttft = (
        sum(ttfts)
        / len(ttfts)
    )

    average_cost = (
        total_cost
        / total_requests
    )

    print()
    print("=" * 60)
    print("LLMForge EXACT CACHE EXPERIMENT")
    print("=" * 60)

    print(f"Provider:             {provider_name}")
    print(f"Model:                {model_name}")
    print(f"Total requests:       {total_requests}")

    print()
    print("CACHE")
    print(f"Cache hits:           {cache_hits}")
    print(f"Cache misses:         {cache_misses}")
    print(f"Cache hit rate:       {hit_rate:.2%}")
    print(f"Cache miss rate:      {miss_rate:.2%}")
    print(f"LLM calls:            {llm_calls}")
    print(
        f"LLM calls avoided:    "
        f"{cache_hits}"
    )

    print()
    print("LATENCY")
    print(
        f"Average latency:      "
        f"{average_latency:.4f} s"
    )
    print(
        f"P50 latency:          "
        f"{percentile(latencies, 50):.4f} s"
    )
    print(
        f"P95 latency:          "
        f"{percentile(latencies, 95):.4f} s"
    )
    print(
        f"P99 latency:          "
        f"{percentile(latencies, 99):.4f} s"
    )

    print()
    print("TTFT")
    print(
        f"Average TTFT:         "
        f"{average_ttft:.4f} s"
    )

    print()
    print("TOKENS")
    print(
        f"Total input tokens:   "
        f"{total_input_tokens}"
    )
    print(
        f"Total output tokens:  "
        f"{total_output_tokens}"
    )

    print()
    print("COST")
    print(
        f"Average cost/request: "
        f"${average_cost:.8f}"
    )
    print(
        f"Total cost:           "
        f"${total_cost:.8f}"
    )

    print()
    print("OUTPUT VALIDITY")
    print(
        f"Parse failures:       "
        f"{parse_failures}"
    )
    print(
        f"Schema failures:      "
        f"{schema_failures}"
    )

    print()
    print(
        f"Output: {output_path}"
    )

    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Run the LLMForge Redis "
            "exact-cache experiment."
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

    args = parser.parse_args()

    run_cache_experiment(
        provider_name=args.provider
    )


if __name__ == "__main__":
    main()