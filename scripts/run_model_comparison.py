import argparse
import json
import statistics
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src.core.generate import build_user_prompt, load_policy
from src.providers.openai import OpenAIProvider


WORKLOAD_PATH = (
    PROJECT_ROOT
    / "data"
    / "workloads"
    / "workload-300.jsonl"
)

RESULTS_DIR = (
    PROJECT_ROOT
    / "data"
    / "run"
    / "model_comparison"
)

SUPPORTED_MODELS = [
    "gpt-5.6-luna",
    "gpt-6-luna",
]


def load_workload():
    requests = []

    with open(WORKLOAD_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                requests.append(json.loads(line))

    return requests


def percentile(values, percentile):
    values = sorted(values)

    index = int(
        (percentile / 100) * (len(values) - 1)
    )

    return values[index]


def calculate_cost(model, input_tokens, output_tokens):

    prices = {
        "gpt-5.6-luna": {
            "input": 0.20,
            "output": 1.20,
        },
        "gpt-6-luna": {
            "input": 0.10,
            "output": 0.50,
        },
    }

    price = prices[model]

    input_cost = (
        input_tokens / 1_000_000
    ) * price["input"]

    output_cost = (
        output_tokens / 1_000_000
    ) * price["output"]

    return input_cost + output_cost


def save_results(model, results):

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        RESULTS_DIR
        / f"{model}.jsonl"
    )

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as f:

        for result in results:
            f.write(
                json.dumps(
                    result,
                    ensure_ascii=False,
                )
                + "\n"
            )

    return output_path


def run_model(model, requests, policy):

    provider = OpenAIProvider(model)

    results = []

    for index, request in enumerate(
        requests,
        start=1,
    ):

        user_prompt = build_user_prompt(
            request["ticket_text"]
        )

        start = time.perf_counter()

        try:

            result = provider.generate(
                system_prompt=policy,
                user_prompt=user_prompt,
                temperature=0.0,
                max_tokens=500,
            )

            end = time.perf_counter()

            latency = end - start

            results.append(
                {
                    "request_index": index,
                    "case_id": request["case_id"],
                    "model": model,
                    "ticket_text": request["ticket_text"],
                    "output": result.text,
                    "input_tokens": result.input_tokens,
                    "output_tokens": result.output_tokens,
                    "ttft": result.ttft,
                    "latency": latency,
                    "error": False,
                    "error_message": None,
                }
            )

        except Exception as error:

            end = time.perf_counter()

            results.append(
                {
                    "request_index": index,
                    "case_id": request["case_id"],
                    "model": model,
                    "ticket_text": request["ticket_text"],
                    "output": "",
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "ttft": 0.0,
                    "latency": end - start,
                    "error": True,
                    "error_message": str(error),
                }
            )

        if index % 10 == 0:
            print(
                f"{model}: "
                f"{index}/{len(requests)}"
            )

    return results


def summarize(model, results):

    successful = [
        result
        for result in results
        if not result["error"]
    ]

    errors = [
        result
        for result in results
        if result["error"]
    ]

    latencies = [
        result["latency"]
        for result in successful
    ]

    ttfts = [
        result["ttft"]
        for result in successful
    ]

    total_input_tokens = sum(
        result["input_tokens"]
        for result in successful
    )

    total_output_tokens = sum(
        result["output_tokens"]
        for result in successful
    )

    total_cost = calculate_cost(
        model,
        total_input_tokens,
        total_output_tokens,
    )

    return {
        "model": model,
        "requests": len(results),
        "successful": len(successful),
        "errors": len(errors),
        "average_latency": (
            statistics.mean(latencies)
            if latencies
            else 0.0
        ),
        "p50": (
            percentile(latencies, 50)
            if latencies
            else 0.0
        ),
        "p95": (
            percentile(latencies, 95)
            if latencies
            else 0.0
        ),
        "p99": (
            percentile(latencies, 99)
            if latencies
            else 0.0
        ),
        "average_ttft": (
            statistics.mean(ttfts)
            if ttfts
            else 0.0
        ),
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
        "total_cost": total_cost,
        "average_cost": (
            total_cost / len(results)
            if results
            else 0.0
        ),
    }


def print_summary(summary):

    print()
    print(
        "Completed:",
        summary["successful"],
        "/",
        summary["requests"],
    )

    print(
        "Errors:",
        summary["errors"],
    )

    print(
        "Average latency:",
        f"{summary['average_latency']:.4f}s",
    )

    print(
        "P50:",
        f"{summary['p50']:.4f}s",
    )

    print(
        "P95:",
        f"{summary['p95']:.4f}s",
    )

    print(
        "P99:",
        f"{summary['p99']:.4f}s",
    )

    print(
        "Average TTFT:",
        f"{summary['average_ttft']:.4f}s",
    )

    print(
        "Input tokens:",
        summary["input_tokens"],
    )

    print(
        "Output tokens:",
        summary["output_tokens"],
    )

    print(
        "Average cost/request:",
        f"${summary['average_cost']:.8f}",
    )

    print(
        "Total cost:",
        f"${summary['total_cost']:.8f}",
    )


def main():

    parser = argparse.ArgumentParser(
        description="Run final OpenAI model comparison"
    )

    parser.add_argument(
        "--model",
        choices=SUPPORTED_MODELS,
        required=True,
        help="OpenAI model to evaluate",
    )

    args = parser.parse_args()

    requests = load_workload()
    policy = load_policy()

    print(
        "Model:",
        args.model,
    )

    print(
        "Requests:",
        len(requests),
    )

    print(
        "Results directory:",
        RESULTS_DIR,
    )

    print()

    print("=" * 80)
    print(
        f"Running model: {args.model}"
    )
    print("=" * 80)

    results = run_model(
        args.model,
        requests,
        policy,
    )

    output_path = save_results(
        args.model,
        results,
    )

    summary = summarize(
        args.model,
        results,
    )

    print_summary(summary)

    print()
    print(
        "Saved results:",
        output_path,
    )

    print()
    print("=" * 80)
    print("MODEL RUN COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()