import argparse
import json
import statistics
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = PROJECT_ROOT / "data" / "runs"


def load_results(provider):
    input_path = RUNS_DIR / f"baseline_{provider}.jsonl"

    if not input_path.exists():
        raise FileNotFoundError(
            f"Run file not found: {input_path}"
        )

    results = []

    with open(input_path, "r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                results.append(json.loads(line))

    return results


def percentile(values, percentile):
    values = sorted(values)

    if not values:
        return 0.0

    index = (len(values) - 1) * percentile / 100

    lower = int(index)
    upper = lower + 1

    if upper >= len(values):
        return values[lower]

    weight = index - lower

    return values[lower] + (
        values[upper] - values[lower]
    ) * weight


def summarize(provider):
    results = load_results(provider)

    if not results:
        print("No results found.")
        return

    latencies = [
        result["total_latency"]
        for result in results
    ]

    ttfts = [
        result["ttft"]
        for result in results
    ]

    costs = [
        result["cost"]
        for result in results
    ]

    input_tokens = [
        result["input_tokens"]
        for result in results
    ]

    output_tokens = [
        result["output_tokens"]
        for result in results
    ]

    parse_failures = sum(
        1
        for result in results
        if not result["parse_success"]
    )

    schema_failures = sum(
        1
        for result in results
        if not result["schema_valid"]
    )

    total_requests = len(results)

    average_latency = statistics.mean(latencies)
    average_ttft = statistics.mean(ttfts)
    average_cost = statistics.mean(costs)

    total_input_tokens = sum(input_tokens)
    total_output_tokens = sum(output_tokens)

    average_input_tokens = statistics.mean(
        input_tokens
    )

    average_output_tokens = statistics.mean(
        output_tokens
    )

    parse_failure_rate = (
        parse_failures / total_requests
    ) * 100

    schema_failure_rate = (
        schema_failures / total_requests
    ) * 100

    model = results[0].get(
        "model",
        "unknown"
    )

    print("=" * 55)
    print("LLMForge BASELINE SUMMARY")
    print("=" * 55)

    print(f"Provider:             {provider}")
    print(f"Model:                {model}")
    print(f"Total requests:       {total_requests}")

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
    print(
        f"P50 TTFT:             "
        f"{percentile(ttfts, 50):.4f} s"
    )
    print(
        f"P95 TTFT:             "
        f"{percentile(ttfts, 95):.4f} s"
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
    print(
        f"Average input/request:"
        f" {average_input_tokens:.2f}"
    )
    print(
        f"Average output/request:"
        f" {average_output_tokens:.2f}"
    )

    print()
    print("COST")
    print(
        f"Average cost/request: "
        f"${average_cost:.8f}"
    )
    print(
        f"Total cost:           "
        f"${sum(costs):.8f}"
    )

    print()
    print("OUTPUT VALIDITY")
    print(
        f"Parse failures:       "
        f"{parse_failures}"
    )
    print(
        f"Parse failure rate:   "
        f"{parse_failure_rate:.2f}%"
    )
    print(
        f"Schema failures:      "
        f"{schema_failures}"
    )
    print(
        f"Schema failure rate:  "
        f"{schema_failure_rate:.2f}%"
    )

    print("=" * 55)


def main():
    parser = argparse.ArgumentParser(
        description="Summarize an LLMForge baseline run."
    )

    parser.add_argument(
        "--provider",
        choices=[
            "fake",
            "openai",
            "anthropic",
        ],
        required=True,
        help=(
            "Provider whose baseline run "
            "should be summarized."
        ),
    )

    args = parser.parse_args()

    summarize(
        args.provider
    )


if __name__ == "__main__":
    main()