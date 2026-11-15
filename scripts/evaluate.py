"""Evaluate the quality of one run file against the golden dataset.

Works on run files of every layout (old baseline / cache / model comparison /
prompt optimization files and new harness runs).

    python -m scripts.evaluate data/runs/baseline_openai.jsonl
    python -m scripts.evaluate <run_file> --no-semantic   # skip the slow model
"""

import argparse
from pathlib import Path

from src.evaluation.run_metrics import evaluate_run


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _fmt(value):
    return "n/a" if value is None else f"{value:.4f}"


def print_report(m):
    print()
    print("=" * 60)
    print("LLMForge EVALUATION")
    print("=" * 60)
    print()
    print(f"Run: {m['run']}")
    print(f"Total requests:        {m['total_requests']}")
    print(f"Unique cases:          {m['unique_cases']}")
    print(f"Successfully parsed:   {m['successfully_parsed']}")

    print()
    print("FORMAT / SCHEMA")
    print("-" * 60)
    print(f"JSON parse failure rate: {_fmt(m['parse_failure_rate'])}")
    print(f"Schema validity:         {_fmt(m['schema_validity'])}")

    print()
    print("DETERMINISTIC QUALITY")
    print("-" * 60)

    if m["cases_evaluated"]:
        print(f"Category accuracy:       {_fmt(m['category_accuracy'])}")
        print(f"Urgency accuracy:        {_fmt(m['urgency_accuracy'])}")
        print(f"Escalation accuracy:     {_fmt(m['escalation_accuracy'])}")
        print(f"Category F1:             {_fmt(m['category_f1'])}")
        print(f"Urgency F1:              {_fmt(m['urgency_f1'])}")
        print(f"Escalation F1:           {_fmt(m['escalation_f1'])}")
        print(f"Fact recall:             {_fmt(m['fact_recall'])}")
        print(f"Forbidden claim rate:    {_fmt(m['forbidden_claim_rate'])}")
    else:
        print(
            "No successfully parsed outputs available for "
            "deterministic evaluation."
        )

    print()
    print("SEMANTIC QUALITY")
    print("-" * 60)

    if m["semantic_average"] is not None:
        print(f"Average summary similarity: {_fmt(m['semantic_average'])}")
        print(f"P50 summary similarity:     {_fmt(m['semantic_p50'])}")
        print(f"P95 summary similarity:     {_fmt(m['semantic_p95'])}")
    else:
        print("Skipped or no parsed outputs.")

    print()
    print("REPEAT CONSISTENCY")
    print("-" * 60)
    print(f"Category consistency:    {_fmt(m['category_consistency'])}")
    print(f"Urgency consistency:     {_fmt(m['urgency_consistency'])}")
    print(f"Escalation consistency:  {_fmt(m['escalation_consistency'])}")
    print()
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate a run file against the golden dataset."
    )
    parser.add_argument("run_file")
    parser.add_argument(
        "--no-semantic",
        action="store_true",
        help="Skip summary similarity (avoids loading the embedding model).",
    )
    args = parser.parse_args()

    run_path = Path(args.run_file)

    if not run_path.is_absolute():
        run_path = PROJECT_ROOT / run_path

    if not run_path.is_file():
        parser.error(f"Run file not found: {run_path}")

    print_report(evaluate_run(run_path, semantic=not args.no_semantic))


if __name__ == "__main__":
    main()
