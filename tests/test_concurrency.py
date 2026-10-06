import json
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.providers.fake import FakeProvider


WORKLOAD_PATH = "data/workloads/workload-300.jsonl"

CONCURRENCY_LEVELS = [1, 2, 5, 10]


def load_workload():
    requests = []

    with open(WORKLOAD_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                requests.append(json.loads(line))

    return requests


def percentile(values, percentile):
    values = sorted(values)

    index = int((percentile / 100) * (len(values) - 1))

    return values[index]


def run_request(provider, request):
    start = time.perf_counter()

    provider.generate(
        system_prompt="test",
        user_prompt=request["ticket_text"],
        temperature=0.0,
        max_tokens=500,
    )

    end = time.perf_counter()

    return end - start


def run_experiment(requests, concurrency):
    provider = FakeProvider(
        response='{"category":"billing","urgency":"high","summary":"test","suggested_reply":"test","needs_escalation":true}',
        input_tokens=100,
        output_tokens=50,
        latency=0.1,
    )

    request_latencies = []

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
            request_latencies.append(
                future.result()
            )

    end = time.perf_counter()

    total_time = end - start

    return {
        "concurrency": concurrency,
        "total_time": total_time,
        "latencies": request_latencies,
    }


def main():
    requests = load_workload()

    print("Requests:", len(requests))
    print()

    print("=" * 90)
    print("CONCURRENCY EXPERIMENT")
    print("=" * 90)

    print(
        f"{'Concurrency':<14}"
        f"{'Total Time':<16}"
        f"{'Throughput':<16}"
        f"{'Avg Latency':<16}"
        f"{'P50':<12}"
        f"{'P95':<12}"
        f"{'P99':<12}"
    )

    print("-" * 90)

    for concurrency in CONCURRENCY_LEVELS:

        result = run_experiment(
            requests,
            concurrency,
        )

        latencies = result["latencies"]
        total_time = result["total_time"]

        throughput = len(requests) / total_time

        average_latency = statistics.mean(
            latencies
        )

        p50 = percentile(latencies, 50)
        p95 = percentile(latencies, 95)
        p99 = percentile(latencies, 99)

        print(
            f"{concurrency:<14}"
            f"{total_time:<16.4f}"
            f"{throughput:<16.2f}"
            f"{average_latency:<16.4f}"
            f"{p50:<12.4f}"
            f"{p95:<12.4f}"
            f"{p99:<12.4f}"
        )


if __name__ == "__main__":
    main()