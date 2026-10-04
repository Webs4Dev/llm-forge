import json
import random
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATASET_PATH = (
    PROJECT_ROOT
    / "data"
    / "datasets"
    / "tickets-seed.jsonl"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "workloads"
    / "workload-300.jsonl"
)

TOTAL_REQUESTS = 300
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


def create_workload(tickets):
    if len(tickets) < 100:
        raise ValueError(
            f"Expected at least 100 tickets, "
            f"found {len(tickets)}."
        )

    rng = random.Random(SEED)

    workload = []

    # Every ticket appears at least once.
    for ticket in tickets:
        workload.append(ticket)

    # Add remaining requests.
    remaining = (
        TOTAL_REQUESTS
        - len(tickets)
    )

    for _ in range(remaining):
        ticket = rng.choice(tickets)
        workload.append(ticket)

    # Shuffle the complete workload.
    rng.shuffle(workload)

    return workload


def main():
    tickets = load_tickets()

    workload = create_workload(
        tickets
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        OUTPUT_PATH,
        "w",
        encoding="utf-8",
    ) as file:

        for index, ticket in enumerate(
            workload,
            start=1,
        ):

            record = {
                "request_index": index,
                "case_id": ticket["case_id"],
                "ticket_text": ticket["input"]["ticket_text"],
            }

            file.write(
                json.dumps(record)
                + "\n"
            )

    print("Workload created.")
    print(f"Tickets: {len(tickets)}")
    print(f"Requests: {len(workload)}")
    print(f"Seed: {SEED}")
    print(f"Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()