import json
from pathlib import Path
from collections import Counter


PROJECT_ROOT = Path(__file__).resolve().parents[1]

WORKLOAD_PATH = (
    PROJECT_ROOT
    / "data"
    / "workloads"
    / "workload-300.jsonl"
)


def load_workload():
    records = []

    with open(
        WORKLOAD_PATH,
        "r",
        encoding="utf-8",
    ) as file:

        for line in file:
            if line.strip():
                records.append(
                    json.loads(line)
                )

    return records


def main():
    records = load_workload()

    print("Workload verification")
    print("---------------------")

    # 1. Total requests
    print(f"Total requests: {len(records)}")

    if len(records) != 300:
        raise ValueError(
            f"Expected 300 requests, "
            f"found {len(records)}"
        )

    # 2. Request indices
    indices = [
        record["request_index"]
        for record in records
    ]

    if indices != list(range(1, 301)):
        raise ValueError(
            "Request indices are invalid."
        )

    print("Request indices: OK")

    # 3. Case IDs
    case_ids = [
        record["case_id"]
        for record in records
    ]

    unique_case_ids = set(case_ids)

    print(
        f"Unique case IDs: "
        f"{len(unique_case_ids)}"
    )

    if len(unique_case_ids) != 100:
        raise ValueError(
            f"Expected 100 unique case IDs, "
            f"found {len(unique_case_ids)}"
        )

    print("Case ID coverage: OK")

    # 4. Ticket text
    missing_text = [
        record["case_id"]
        for record in records
        if not record.get("ticket_text")
    ]

    if missing_text:
        raise ValueError(
            f"Missing ticket text for: "
            f"{missing_text}"
        )

    print("Ticket text: OK")

    # 5. Duplicate rate
    counts = Counter(case_ids)

    duplicate_requests = sum(
        count - 1
        for count in counts.values()
        if count > 1
    )

    duplicate_rate = (
        duplicate_requests
        / len(records)
    )

    print(
        f"Duplicate requests: "
        f"{duplicate_requests}"
    )

    print(
        f"Duplicate rate: "
        f"{duplicate_rate:.2%}"
    )

    # 6. Most frequent tickets
    print("\nMost frequent tickets:")

    for case_id, count in counts.most_common(10):
        print(
            f"  {case_id}: {count}"
        )

    print("\nWorkload verification PASSED.")


if __name__ == "__main__":
    main()