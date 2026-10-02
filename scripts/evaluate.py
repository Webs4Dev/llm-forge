import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src.core.schema import validate_output
from src.evaluation.dataset import load_dataset
from src.evaluation.suite import (
    evaluate_dataset,
    calculate_suite_summary,
)


DATASET_PATH = (
    PROJECT_ROOT
    / "data"
    / "datasets"
    / "tickets-seed.jsonl"
)


def load_run_outputs(run_path):
    """
    Load stored model outputs from a baseline JSONL file.

    Returns:
        Dictionary mapping case_id -> parsed model output.

    Invalid JSON outputs are stored as None so that
    parse failures are not silently discarded.
    """

    outputs = {}

    with open(
        run_path,
        "r",
        encoding="utf-8",
    ) as file:

        for line in file:
            line = line.strip()

            if not line:
                continue

            record = json.loads(line)

            case_id = record["case_id"]
            raw_output = record["raw_output"]

            try:
                parsed_output = json.loads(
                    raw_output
                )
            except json.JSONDecodeError:
                parsed_output = None

            outputs[case_id] = {
                "raw_output": raw_output,
                "parsed_output": parsed_output,
                "parse_success": parsed_output is not None,
            }

    return outputs


def build_valid_outputs(run_outputs):
    """
    Extract only successfully parsed outputs.

    These are the outputs that can be passed to the
    deterministic evaluator.
    """

    outputs = {}

    for case_id, record in run_outputs.items():

        if record["parse_success"]:
            outputs[case_id] = record["parsed_output"]

    return outputs


def calculate_parse_failure_rate(run_outputs):
    """
    Calculate the percentage of outputs that failed
    JSON parsing.
    """

    if not run_outputs:
        return 0.0

    failures = sum(
        1
        for record in run_outputs.values()
        if not record["parse_success"]
    )

    return failures / len(run_outputs)


def calculate_schema_validity_all(run_outputs):
    """
    Calculate schema validity across ALL outputs.

    Parse failures count as schema failures.
    """

    if not run_outputs:
        return 0.0

    valid_count = 0

    for record in run_outputs.values():

        if not record["parse_success"]:
            continue

        valid, _ = validate_output(
            json.dumps(
                record["parsed_output"]
            )
        )

        if valid:
            valid_count += 1

    return valid_count / len(run_outputs)


def print_report(
    run_path,
    run_outputs,
    results,
    summary,
):
    """
    Print evaluation results to the terminal.
    """

    print()
    print("=" * 60)
    print("LLMForge EVALUATION")
    print("=" * 60)

    print()
    print(f"Run: {run_path.name}")

    print(
        f"Model outputs: "
        f"{len(run_outputs)}"
    )

    print(
        f"Successfully parsed: "
        f"{len(results)}"
    )

    print()
    print("FORMAT / SCHEMA")
    print("-" * 60)

    parse_failure_rate = calculate_parse_failure_rate(
        run_outputs
    )

    schema_validity = calculate_schema_validity_all(
        run_outputs
    )

    print(
        f"JSON parse failure rate: "
        f"{parse_failure_rate:.4f}"
    )

    print(
        f"Schema validity:         "
        f"{schema_validity:.4f}"
    )

    print()
    print("DETERMINISTIC METRICS")
    print("-" * 60)

    if results:

        print(
            f"Category accuracy:       "
            f"{summary['category_accuracy']:.4f}"
        )

        print(
            f"Urgency accuracy:        "
            f"{summary['urgency_accuracy']:.4f}"
        )

        print(
            f"Escalation accuracy:     "
            f"{summary['needs_escalation_accuracy']:.4f}"
        )

        print(
            f"Fact recall:             "
            f"{summary['fact_recall']:.4f}"
        )

        print(
            f"Forbidden claim rate:    "
            f"{summary['forbidden_claim_rate']:.4f}"
        )

    else:

        print(
            "No successfully parsed outputs "
            "available for deterministic evaluation."
        )

    print()
    print("PER-CASE FORMAT RESULTS")
    print("-" * 60)

    for case_id, record in run_outputs.items():

        if record["parse_success"]:
            status = "PARSED"
        else:
            status = "PARSE FAILED"

        print(
            f"{case_id} | {status}"
        )

    print()
    print("=" * 60)


def main():

    if len(sys.argv) != 2:
        print(
            "Usage: "
            "python -m scripts.evaluate "
            "<run_file>"
        )

        print()

        print(
            "Example:"
        )

        print(
            "python -m scripts.evaluate "
            "data/runs/baseline_anthropic.jsonl"
        )

        return

    run_path = PROJECT_ROOT / sys.argv[1]

    if not run_path.exists():
        print(
            f"Run file not found: {run_path}"
        )
        return

    cases = load_dataset(
        DATASET_PATH
    )

    run_outputs = load_run_outputs(
        run_path
    )

    valid_outputs = build_valid_outputs(
        run_outputs
    )

    results = evaluate_dataset(
        cases,
        valid_outputs
    )

    summary = calculate_suite_summary(
        results,
        valid_outputs,
    )

    print_report(
        run_path,
        run_outputs,
        results,
        summary,
    )


if __name__ == "__main__":
    main()