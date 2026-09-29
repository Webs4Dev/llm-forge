import json
import statistics
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = PROJECT_ROOT / "data" / "runs" / "baseline.jsonl"


def load_results():
    results = []

    with open(INPUT_PATH, "r", encoding="utf-8") as file:
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

    return values[lower] + (values[upper] - values[lower]) * weight


def summarize():
    results = load_results()

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

    parse_failures = sum(
        1
        for result in results
        if not result["parse_success"]
    )

    total_requests = len(results)

    average_latency = statistics.mean(latencies)
    average_ttft = statistics.mean(ttfts)
    average_cost = statistics.mean(costs)

    parse_failure_rate = (
        parse_failures / total_requests
    ) * 100

    print("=" * 50)
    print("LLMForge BASELINE SUMMARY")
    print("=" * 50)

    print(f"Total requests:       {total_requests}")

    print()
    print("LATENCY")
    print(f"Average latency:      {average_latency:.4f} s")
    print(f"P50 latency:          {percentile(latencies, 50):.4f} s")
    print(f"P95 latency:          {percentile(latencies, 95):.4f} s")
    print(f"P99 latency:          {percentile(latencies, 99):.4f} s")

    print()
    print("TTFT")
    print(f"Average TTFT:          {average_ttft:.4f} s")
    print(f"P50 TTFT:              {percentile(ttfts, 50):.4f} s")
    print(f"P95 TTFT:              {percentile(ttfts, 95):.4f} s")

    print()
    print("COST")
    print(f"Average cost/request: ${average_cost:.8f}")

    print()
    print("OUTPUT VALIDITY")
    print(f"Parse failures:        {parse_failures}")
    print(f"Parse failure rate:    {parse_failure_rate:.2f}%")

    print("=" * 50)


if __name__ == "__main__":
    summarize()