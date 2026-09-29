import json
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(PROJECT_ROOT / "src"))

from core.generate import generate
from core.cost import calculate_cost
from providers.fake import FakeProvider


DATASET_PATH = PROJECT_ROOT / "data" / "datasets" / "tickets-seed.jsonl"
OUTPUT_DIR = PROJECT_ROOT / "data" / "runs"
OUTPUT_PATH = OUTPUT_DIR / "baseline.jsonl"


REPEATS = 5

INPUT_PRICE_PER_1M = 0.0
OUTPUT_PRICE_PER_1M = 0.0


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


def run_baseline():

    tickets = load_tickets()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    provider = FakeProvider(
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

    total_requests = 0

    with open(OUTPUT_PATH, "w", encoding="utf-8") as output_file:

        for ticket in tickets:

            case_id = ticket["case_id"]
            ticket_text = ticket["input"]["ticket_text"]

            for repeat in range(1, REPEATS + 1):

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
                    input_price_per_1m=INPUT_PRICE_PER_1M,
                    output_price_per_1m=OUTPUT_PRICE_PER_1M,
                )

                parse_success = is_valid_json(result.text)

                record = {
                    "case_id": case_id,
                    "repeat": repeat,
                    "input_tokens": result.input_tokens,
                    "output_tokens": result.output_tokens,
                    "ttft": result.ttft,
                    "total_latency": total_latency,
                    "cost": cost,
                    "raw_output": result.text,
                    "parse_success": parse_success,
                }

                output_file.write(
                    json.dumps(record) + "\n"
                )

                total_requests += 1

                print(
                    f"{case_id} | "
                    f"repeat={repeat} | "
                    f"latency={total_latency:.4f}s"
                )

    print()
    print("Baseline complete.")
    print(f"Total requests: {total_requests}")
    print(f"Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    run_baseline()  