import argparse
import json
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))


from src.providers.fake import FakeProvider
from src.providers.openai import OpenAIProvider
from src.providers.anthropic import AnthropicProvider


WORKLOAD_PATH = (
    PROJECT_ROOT
    / "data"
    / "workloads"
    / "workload-300.jsonl"
)

CONCURRENCY_LEVELS = [1, 2, 5, 10]


def load_workload():
    requests = []

    with open(WORKLOAD_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                requests.append(json.loads(line))

    return requests


def create_provider(provider_name):

    if provider_name == "fake":
        return FakeProvider(
            response=(
                '{"category":"billing",'
                '"urgency":"high",'
                '"summary":"test",'
                '"suggested_reply":"test",'
                '"needs_escalation":true}'
            ),
            input_tokens=100,
            output_tokens=50,
            latency=0.1,
        )

    if provider_name == "openai":
        return OpenAIProvider(
            "gpt-5.6-luna"
        )

    if provider_name == "anthropic":
        return AnthropicProvider(
            "claude-haiku-4-5"
        )

    raise ValueError(
        f"Unsupported provider: {provider_name}"
    )


def percentile(values, percentile):
    values = sorted(values)

    index = int(
        (percentile / 100) * (len(values) - 1)
    )

    return values[index]


def run_request(provider, request):

    start = time.perf_counter()

    result = provider.generate(
        system_prompt="",
        user_prompt=request["ticket_text"],
        temperature=0.0,
        max_tokens=500,
    )

    end = time.perf_counter()

    return {
        "latency": end - start,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
        "ttft": result.ttft,
    }


def run_experiment(
    requests,
    provider_name,
    concurrency,
):

    provider = create_provider(
        provider_name
    )

    results = []
    errors = []

    start = time.perf_counter()

    with ThreadPoolExecutor(
        max_workers=concurrency
    ) as executor:

        futures = [
            executor.submit(
                run_request,
                provider,
                request,
            )
            for request in requests
        ]

        for future in as_completed(futures):

            try:
                results.append(
                    future.result()
                )

            except Exception as error:
                errors.append(str(error))

    end = time.perf_counter()

    total_time = end - start

    return (
        results,
        errors,
        total_time,
    )


def main():

    parser = argparse.ArgumentParser(
        description="Run LLM concurrency experiment"
    )

    parser.add_argument(
        "--provider",
        choices=[
            "fake",
            "openai",
            "anthropic",
        ],
        required=True,
        help="Provider to benchmark",
    )

    args = parser.parse_args()

    requests = load_workload()

    print(
        "Provider:",
        args.provider,
    )

    print(
        "Requests:",
        len(requests),
    )

    print()

    print("=" * 110)
    print("CONCURRENCY EXPERIMENT")
    print("=" * 110)

    print(
        f"{'Concurrency':<14}"
        f"{'Total Time':<16}"
        f"{'Throughput':<16}"
        f"{'Avg Latency':<16}"
        f"{'P50':<12}"
        f"{'P95':<12}"
        f"{'P99':<12}"
        f"{'Errors':<10}"
    )

    print("-" * 110)

    for concurrency in CONCURRENCY_LEVELS:

        results, errors, total_time = (
            run_experiment(
                requests,
                args.provider,
                concurrency,
            )
        )

        if not results:

            print(
                f"{concurrency:<14}"
                f"{total_time:<16.4f}"
                f"{'N/A':<16}"
                f"{'N/A':<16}"
                f"{'N/A':<12}"
                f"{'N/A':<12}"
                f"{'N/A':<12}"
                f"{len(errors):<10}"
            )

            continue

        latencies = [
            result["latency"]
            for result in results
        ]

        throughput = (
            len(results)
            / total_time
        )

        average_latency = (
            statistics.mean(latencies)
        )

        p50 = percentile(
            latencies,
            50,
        )

        p95 = percentile(
            latencies,
            95,
        )

        p99 = percentile(
            latencies,
            99,
        )

        print(
            f"{concurrency:<14}"
            f"{total_time:<16.4f}"
            f"{throughput:<16.2f}"
            f"{average_latency:<16.4f}"
            f"{p50:<12.4f}"
            f"{p95:<12.4f}"
            f"{p99:<12.4f}"
            f"{len(errors):<10}"
        )


if __name__ == "__main__":
    main()