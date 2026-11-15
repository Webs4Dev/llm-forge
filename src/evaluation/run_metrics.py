"""Quality metrics for a whole run file.

Moved out of scripts/evaluate.py so the regression check can reuse it.
Runs are loaded with src.experiments.runs.load_run, which accepts every
run-file layout the project has produced (the old loader required fields
that only some scripts wrote and crashed on the rest).
"""

import json
from pathlib import Path

import numpy as np

from src.core.schema import validate_output
from src.evaluation.dataset import load_dataset
from src.evaluation.suite import (
    calculate_macro_f1,
    calculate_suite_summary,
    evaluate_dataset,
)
from src.experiments.runs import load_run, parse_output


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_PATH = PROJECT_ROOT / "data" / "datasets" / "tickets-seed.jsonl"


def load_run_outputs(run_path):
    """Every request in the run, with its output parsed (fences tolerated)."""
    outputs = []

    for record in load_run(run_path):
        parsed = parse_output(record)

        outputs.append({
            "provider": record["provider"],
            "model": record["model"],
            "case_id": record["case_id"],
            "repeat": record["repeat"],
            "raw_output": record["raw_output"],
            "parsed_output": parsed,
            "parse_success": parsed is not None,
        })

    return outputs


def calculate_parse_failure_rate(run_outputs):
    if not run_outputs:
        return 0.0

    failures = sum(1 for r in run_outputs if not r["parse_success"])

    return failures / len(run_outputs)


def calculate_run_schema_validity(run_outputs):
    """Share of all requests with schema-valid output (parse failures count as invalid)."""
    if not run_outputs:
        return 0.0

    valid = sum(
        1
        for r in run_outputs
        if r["parse_success"]
        and validate_output(json.dumps(r["parsed_output"]))[0]
    )

    return valid / len(run_outputs)


def calculate_consistency(run_outputs, field):
    """Share of repeats that agree with their case's most common prediction."""
    grouped = {}

    for r in run_outputs:
        if r["parse_success"] and isinstance(r["parsed_output"], dict):
            grouped.setdefault(r["case_id"], []).append(
                r["parsed_output"].get(field)
            )

    total = 0
    matching = 0

    for values in grouped.values():
        counts = {}

        for value in values:
            counts[value] = counts.get(value, 0) + 1

        matching += max(counts.values())
        total += len(values)

    return matching / total if total else 0.0


def build_evaluation_inputs(cases, run_outputs):
    """Evaluate every repeat separately against its reference case."""
    case_lookup = {case["case_id"]: case for case in cases}

    evaluation_cases = []
    evaluation_outputs = {}

    for r in run_outputs:
        if not r["parse_success"] or r["case_id"] not in case_lookup:
            continue

        if not isinstance(r["parsed_output"], dict):
            continue

        evaluation_id = f"{r['case_id']}_repeat_{r['repeat']}"

        evaluation_case = dict(case_lookup[r["case_id"]])
        evaluation_case["case_id"] = evaluation_id

        evaluation_cases.append(evaluation_case)
        evaluation_outputs[evaluation_id] = r["parsed_output"]

    return evaluation_cases, evaluation_outputs


def calculate_semantic_metrics(cases, run_outputs):
    """Average, P50, P95 similarity of generated vs gold summaries."""
    # Imported here: loading sentence-transformers is slow.
    from src.evaluation.semantic import calculate_summary_similarity

    case_lookup = {case["case_id"]: case for case in cases}
    scores = []

    for r in run_outputs:
        if not r["parse_success"] or r["case_id"] not in case_lookup:
            continue

        if not isinstance(r["parsed_output"], dict):
            continue

        scores.append(
            calculate_summary_similarity(
                case_lookup[r["case_id"]]["reference"]["gold_summary"],
                r["parsed_output"].get("summary", ""),
            )
        )

    if not scores:
        return None, None, None

    return (
        float(np.mean(scores)),
        float(np.percentile(scores, 50)),
        float(np.percentile(scores, 95)),
    )


def evaluate_run(run_path, semantic=True, dataset_path=DATASET_PATH):
    """All quality metrics for one run file, as a flat dict."""
    cases = load_dataset(dataset_path)
    run_outputs = load_run_outputs(run_path)

    evaluation_cases, evaluation_outputs = build_evaluation_inputs(
        cases,
        run_outputs,
    )

    results = evaluate_dataset(evaluation_cases, evaluation_outputs)
    summary = calculate_suite_summary(results, evaluation_outputs)

    metrics = {
        "run": Path(run_path).name,
        "total_requests": len(run_outputs),
        "unique_cases": len({r["case_id"] for r in run_outputs}),
        "successfully_parsed": sum(
            1 for r in run_outputs if r["parse_success"]
        ),
        "parse_failure_rate": calculate_parse_failure_rate(run_outputs),
        "schema_validity": calculate_run_schema_validity(run_outputs),
        "cases_evaluated": len(results),
        "category_accuracy": summary["category_accuracy"] if results else None,
        "urgency_accuracy": summary["urgency_accuracy"] if results else None,
        "escalation_accuracy": (
            summary["needs_escalation_accuracy"] if results else None
        ),
        "category_f1": None,
        "urgency_f1": None,
        "escalation_f1": None,
        "fact_recall": summary["fact_recall"] if results else None,
        "forbidden_claim_rate": (
            summary["forbidden_claim_rate"] if results else None
        ),
        "category_consistency": calculate_consistency(run_outputs, "category"),
        "urgency_consistency": calculate_consistency(run_outputs, "urgency"),
        "escalation_consistency": calculate_consistency(
            run_outputs,
            "needs_escalation",
        ),
        "semantic_average": None,
        "semantic_p50": None,
        "semantic_p95": None,
    }

    if results:
        for field, key in [
            ("category", "category_f1"),
            ("urgency", "urgency_f1"),
            ("needs_escalation", "escalation_f1"),
        ]:
            metrics[key] = calculate_macro_f1(
                evaluation_cases,
                evaluation_outputs,
                field,
            )

    if semantic and metrics["successfully_parsed"]:
        (
            metrics["semantic_average"],
            metrics["semantic_p50"],
            metrics["semantic_p95"],
        ) = calculate_semantic_metrics(cases, run_outputs)

    return metrics
