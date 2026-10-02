import json
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(PROJECT_ROOT / "src")
)

from src.core.schema import validate_output
from src.evaluation.dataset import load_dataset
from src.evaluation.suite import (
    evaluate_dataset,
    calculate_suite_summary,
    calculate_macro_f1,
)
from src.evaluation.optimization.normalize import normalize_json_output
from src.evaluation.semantic import calculate_summary_similarity



DATASET_PATH = (
    PROJECT_ROOT
    / "data"
    / "datasets"
    / "tickets-seed.jsonl"
)


def load_run_outputs(run_path):
    """
    Load every request from a baseline JSONL file.

    Each request remains separate, including repeats.

    Anthropic outputs are normalized before JSON parsing
    so Markdown-fenced JSON can be evaluated.

    Returns:
        List of records.
    """

    outputs = []

    with open(
        run_path,
        "r",
        encoding="utf-8"
    ) as file:

        for line in file:

            line = line.strip()

            if not line:
                continue

            record = json.loads(line)

            raw_output = record["raw_output"]

            normalized_output = normalize_json_output(
                raw_output
            )

            try:

                parsed_output = json.loads(
                    normalized_output
                )

            except json.JSONDecodeError:

                parsed_output = None

            outputs.append(
                {
                    "provider": record["provider"],
                    "model": record["model"],
                    "case_id": record["case_id"],
                    "repeat": record["repeat"],
                    "raw_output": raw_output,
                    "parsed_output": parsed_output,
                    "parse_success": (
                        parsed_output is not None
                    ),
                }
            )

    return outputs


def calculate_parse_failure_rate(
    run_outputs
):
    """
    Calculate JSON parse failure rate
    across all requests.
    """

    if not run_outputs:
        return 0.0

    failures = sum(
        1
        for record in run_outputs
        if not record["parse_success"]
    )

    return failures / len(run_outputs)


def calculate_schema_validity(
    run_outputs
):
    """
    Calculate schema validity across
    all requests.

    Parse failures count as invalid.
    """

    if not run_outputs:
        return 0.0

    valid_count = 0

    for record in run_outputs:

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


def calculate_consistency(
    run_outputs,
    field,
):
    """
    Calculate repeat consistency for a field.

    For each case, find the most common prediction
    across its repeats.

    Consistency =
        matching repeats / total repeats
    """

    grouped = {}

    for record in run_outputs:

        if not record["parse_success"]:
            continue

        case_id = record["case_id"]

        value = record[
            "parsed_output"
        ].get(field)

        if case_id not in grouped:
            grouped[case_id] = []

        grouped[case_id].append(value)

    if not grouped:
        return 0.0

    total = 0
    matching = 0

    for values in grouped.values():

        if not values:
            continue

        counts = {}

        for value in values:

            counts[value] = (
                counts.get(value, 0) + 1
            )

        most_common_count = max(
            counts.values()
        )

        matching += most_common_count
        total += len(values)

    if total == 0:
        return 0.0

    return matching / total


def build_evaluation_inputs(
    cases,
    run_outputs,
):
    """
    Convert repeated run records into the
    format expected by the evaluation engine.

    Every repeat is evaluated separately.
    """

    case_lookup = {
        case["case_id"]: case
        for case in cases
    }

    evaluation_cases = []

    evaluation_outputs = {}

    for record in run_outputs:

        if not record["parse_success"]:
            continue

        case_id = record["case_id"]

        if case_id not in case_lookup:
            continue

        case = case_lookup[case_id]

        repeat = record["repeat"]

        evaluation_id = (
            f"{case_id}_repeat_{repeat}"
        )

        evaluation_case = dict(case)

        evaluation_case["case_id"] = (
            evaluation_id
        )

        evaluation_cases.append(
            evaluation_case
        )

        evaluation_outputs[
            evaluation_id
        ] = record["parsed_output"]

    return (
        evaluation_cases,
        evaluation_outputs,
    )


def calculate_semantic_metrics(
    cases,
    run_outputs,
):
    """
    Calculate semantic similarity between
    each gold summary and generated summary.

    Returns:
        average_similarity,
        p50_similarity,
        p95_similarity
    """

    case_lookup = {
        case["case_id"]: case
        for case in cases
    }

    scores = []

    for record in run_outputs:

        if not record["parse_success"]:
            continue

        case_id = record["case_id"]

        if case_id not in case_lookup:
            continue

        case = case_lookup[case_id]

        reference_summary = (
            case["reference"]["gold_summary"]
        )

        generated_summary = (
            record["parsed_output"].get(
                "summary",
                "",
            )
        )

        score = calculate_summary_similarity(
            reference_summary,
            generated_summary,
        )

        scores.append(score)

    if not scores:
        return 0.0, 0.0, 0.0

    average_similarity = float(
        np.mean(scores)
    )

    p50_similarity = float(
        np.percentile(
            scores,
            50,
        )
    )

    p95_similarity = float(
        np.percentile(
            scores,
            95,
        )
    )

    return (
        average_similarity,
        p50_similarity,
        p95_similarity,
    )


def print_report(
    run_path,
    run_outputs,
    results,
    summary,
    category_f1,
    urgency_f1,
    escalation_f1,
    semantic_average,
    semantic_p50,
    semantic_p95,
):
    """
    Print the complete evaluation report.
    """

    total_requests = len(
        run_outputs
    )

    unique_cases = len(
        {
            record["case_id"]
            for record in run_outputs
        }
    )

    successful_parses = sum(
        1
        for record in run_outputs
        if record["parse_success"]
    )

    parse_failure_rate = (
        calculate_parse_failure_rate(
            run_outputs
        )
    )

    schema_validity = (
        calculate_schema_validity(
            run_outputs
        )
    )

    category_consistency = (
        calculate_consistency(
            run_outputs,
            "category",
        )
    )

    urgency_consistency = (
        calculate_consistency(
            run_outputs,
            "urgency",
        )
    )

    escalation_consistency = (
        calculate_consistency(
            run_outputs,
            "needs_escalation",
        )
    )

    print()

    print("=" * 60)

    print("LLMForge EVALUATION")

    print("=" * 60)

    print()

    print(
        f"Run: {run_path.name}"
    )

    print(
        f"Total requests:        "
        f"{total_requests}"
    )

    print(
        f"Unique cases:          "
        f"{unique_cases}"
    )

    print(
        f"Successfully parsed:   "
        f"{successful_parses}"
    )

    print()

    print("FORMAT / SCHEMA")

    print("-" * 60)

    print(
        f"JSON parse failure rate: "
        f"{parse_failure_rate:.4f}"
    )

    print(
        f"Schema validity:         "
        f"{schema_validity:.4f}"
    )

    print()

    print("DETERMINISTIC QUALITY")

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
            f"Category F1:             "
            f"{category_f1:.4f}"
        )

        print(
            f"Urgency F1:              "
            f"{urgency_f1:.4f}"
        )

        print(
            f"Escalation F1:           "
            f"{escalation_f1:.4f}"
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
            "available for deterministic "
            "evaluation."
        )

    print()

    print("SEMANTIC QUALITY")

    print("-" * 60)

    if successful_parses > 0:

        print(
            f"Average summary similarity: "
            f"{semantic_average:.4f}"
        )

        print(
            f"P50 summary similarity:     "
            f"{semantic_p50:.4f}"
        )

        print(
            f"P95 summary similarity:     "
            f"{semantic_p95:.4f}"
        )

    else:

        print(
            "No successfully parsed outputs "
            "available for semantic evaluation."
        )

    print()

    print("REPEAT CONSISTENCY")

    print("-" * 60)

    print(
        f"Category consistency:    "
        f"{category_consistency:.4f}"
    )

    print(
        f"Urgency consistency:     "
        f"{urgency_consistency:.4f}"
    )

    print(
        f"Escalation consistency:  "
        f"{escalation_consistency:.4f}"
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

        print("Example:")

        print(
            "python -m scripts.evaluate "
            "data/runs/baseline_openai.jsonl"
        )

        return

    run_path = (
        PROJECT_ROOT / sys.argv[1]
    )

    if not run_path.exists():

        print(
            f"Run file not found: "
            f"{run_path}"
        )

        return

    cases = load_dataset(
        DATASET_PATH
    )

    run_outputs = load_run_outputs(
        run_path
    )

    (
        evaluation_cases,
        evaluation_outputs,
    ) = build_evaluation_inputs(
        cases,
        run_outputs,
    )

    results = evaluate_dataset(
        evaluation_cases,
        evaluation_outputs,
    )

    summary = calculate_suite_summary(
        results,
        evaluation_outputs,
    )

    category_f1 = calculate_macro_f1(
        evaluation_cases,
        evaluation_outputs,
        "category",
    )

    urgency_f1 = calculate_macro_f1(
        evaluation_cases,
        evaluation_outputs,
        "urgency",
    )

    escalation_f1 = calculate_macro_f1(
        evaluation_cases,
        evaluation_outputs,
        "needs_escalation",
    )

    (
        semantic_average,
        semantic_p50,
        semantic_p95,
    ) = calculate_semantic_metrics(
        cases,
        run_outputs,
    )

    print_report(
        run_path,
        run_outputs,
        results,
        summary,
        category_f1,
        urgency_f1,
        escalation_f1,
        semantic_average,
        semantic_p50,
        semantic_p95,
    )


if __name__ == "__main__":
    main()