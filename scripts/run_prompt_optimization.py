import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src.providers.fake import FakeProvider
from src.providers.openai import OpenAIProvider
from src.providers.anthropic import AnthropicProvider


load_dotenv()


WORKLOAD_PATH = PROJECT_ROOT / "data" / "workloads" / "workload-300.jsonl"
POLICY_PATH = PROJECT_ROOT / "data" / "policy" / "policy-v2.txt"
PROMPT_PATH = PROJECT_ROOT / "data" / "prompts" / "tickets-v2.txt"

OUTPUT_DIR = PROJECT_ROOT / "data" / "runs"


PRICES = {
    "openai": {
        "input": 0.20,
        "output": 1.20,
    },
    "anthropic": {
        "input": 1.00,
        "output": 5.00,
    },
}


MODELS = {
    "openai": "gpt-5.6-luna",
    "anthropic": "claude-haiku-4-5",
}


def load_workload():
    records = []

    with open(WORKLOAD_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    return records


def load_policy():
    return POLICY_PATH.read_text(encoding="utf-8")


def load_prompt_template():
    return PROMPT_PATH.read_text(encoding="utf-8")


def build_user_prompt(ticket_text, prompt_template):
    return prompt_template.replace(
        "{{ticket_text}}",
        ticket_text,
    )


def calculate_cost(provider, input_tokens, output_tokens):
    prices = PRICES[provider]

    input_cost = (
        input_tokens / 1_000_000
    ) * prices["input"]

    output_cost = (
        output_tokens / 1_000_000
    ) * prices["output"]

    return input_cost + output_cost


def percentile(values, percentile_value):
    if not values:
        return 0.0

    return float(
        np.percentile(
            np.array(values),
            percentile_value,
        )
    )


def create_provider(provider):
    model = MODELS[provider]

    if provider == "openai":
        return OpenAIProvider(model)

    if provider == "anthropic":
        return AnthropicProvider(model)

    raise ValueError(
        f"Unsupported provider: {provider}"
    )


def run_experiment(provider):
    workload = load_workload()

    policy = load_policy()
    prompt_template = load_prompt_template()

    llm = create_provider(provider)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        OUTPUT_DIR
        / f" prompt_optimization_{provider}-v2.jsonl"
    )

    latencies = []
    ttfts = []

    total_input_tokens = 0
    total_output_tokens = 0
    total_cost = 0.0

    errors = 0

    print()
    print("=" * 60)
    print("PROMPT OPTIMIZATION — V2")
    print("=" * 60)
    print(f"Provider: {provider}")
    print(f"Model: {MODELS[provider]}")
    print(f"Requests: {len(workload)}")
    print("Prompt version: v2")
    print("Cache: disabled")
    print()

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as output_file:

        for index, record in enumerate(
            workload,
            start=1,
        ):
            case_id = record["case_id"]
            ticket_text = record["ticket_text"]

            user_prompt = build_user_prompt(
                ticket_text,
                prompt_template,
            )

            start = time.perf_counter()

            try:
                result = llm.generate(
                    system_prompt=policy,
                    user_prompt=user_prompt,
                    temperature=0.0,
                    max_tokens=500,
                )

                end = time.perf_counter()

                latency = result.total_latency

                latencies.append(latency)
                ttfts.append(result.ttft)

                total_input_tokens += (
                    result.input_tokens
                )

                total_output_tokens += (
                    result.output_tokens
                )

                cost = calculate_cost(
                    provider,
                    result.input_tokens,
                    result.output_tokens,
                )

                total_cost += cost

                row = {
                    "request_index": record["request_index"],
                    "case_id": case_id,
                    "model": MODELS[provider],
                    "prompt_version": "v2",
                    "ticket_text": ticket_text,
                    "output": result.text,
                    "input_tokens": result.input_tokens,
                    "output_tokens": result.output_tokens,
                    "ttft": result.ttft,
                    "latency": latency,
                    "cost": cost,
                    "error": False,
                    "error_message": None,
                }

            except Exception as e:
                end = time.perf_counter()

                errors += 1

                row = {
                    "request_index": record["request_index"],
                    "case_id": case_id,
                    "model": MODELS[provider],
                    "prompt_version": "v2",
                    "ticket_text": ticket_text,
                    "output": "",
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "ttft": end - start,
                    "latency": end - start,
                    "cost": 0.0,
                    "error": True,
                    "error_message": str(e),
                }

            output_file.write(
                json.dumps(row)
                + "\n"
            )

            output_file.flush()

            if index % 10 == 0:
                print(
                    f"Completed {index}/{len(workload)}"
                )

    avg_latency = (
        sum(latencies) / len(latencies)
        if latencies
        else 0.0
    )

    avg_ttft = (
        sum(ttfts) / len(ttfts)
        if ttfts
        else 0.0
    )

    avg_cost = (
        total_cost / len(workload)
        if workload
        else 0.0
    )

    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)

    print(f"Provider: {provider}")
    print(f"Model: {MODELS[provider]}")
    print(f"Prompt version: v2")
    print(f"Requests: {len(workload)}")
    print(f"Errors: {errors}")

    print()
    print("LATENCY")
    print("-" * 60)
    print(f"Average: {avg_latency:.4f}s")
    print(f"P50:     {percentile(latencies, 50):.4f}s")
    print(f"P95:     {percentile(latencies, 95):.4f}s")
    print(f"P99:     {percentile(latencies, 99):.4f}s")

    print()
    print("TOKENS")
    print("-" * 60)
    print(f"Input:  {total_input_tokens}")
    print(f"Output: {total_output_tokens}")

    print()
    print("COST")
    print("-" * 60)
    print(f"Average/request: ${avg_cost:.8f}")
    print(f"Total:           ${total_cost:.8f}")

    print()
    print("TTFT")
    print("-" * 60)
    print(f"Average: {avg_ttft:.4f}s")

    print()
    print(f"Saved results to:")
    print(output_path)

    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Run LLMForge prompt optimization using V2."
    )

    parser.add_argument(
        "--provider",
        required=True,
        choices=[
            "openai",
            "anthropic",
        ],
        help="LLM provider to test.",
    )

    args = parser.parse_args()

    run_experiment(args.provider)


if __name__ == "__main__":
    main()