"""Fail (exit code 1) if a run's quality regressed against a reference run.

    python -m scripts.check_quality <candidate_run> --reference <reference_run>

Example: did prompt v2 keep the quality of the v1 baseline?
    python -m scripts.check_quality \\
        data/runs/prompt_optimization_openai-v2.jsonl \\
        --reference data/runs/baseline_openai.jsonl

Tolerances are in src/evaluation/regression.py.
"""

import argparse
import sys
from pathlib import Path

from src.evaluation.regression import DEFAULT_TOLERANCES, find_regressions
from src.evaluation.run_metrics import evaluate_run


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _resolve(path):
    path = Path(path)
    return path if path.is_absolute() else PROJECT_ROOT / path


def _fmt(value):
    return "n/a" if value is None else f"{value:.4f}"


def main():
    parser = argparse.ArgumentParser(
        description="Check a run for quality regressions against a reference."
    )
    parser.add_argument("candidate")
    parser.add_argument("--reference", required=True)
    args = parser.parse_args()

    candidate_path = _resolve(args.candidate)
    reference_path = _resolve(args.reference)

    for path in (candidate_path, reference_path):
        if not path.is_file():
            parser.error(f"Run file not found: {path}")

    # Deterministic metrics only: fast and no embedding model needed.
    candidate = evaluate_run(candidate_path, semantic=False)
    reference = evaluate_run(reference_path, semantic=False)

    print(f"Reference: {reference_path.name}")
    print(f"Candidate: {candidate_path.name}")
    print()
    print(f"{'Metric':<24}{'Reference':<12}{'Candidate':<12}{'Tolerance':<10}")

    for metric, (direction, tolerance) in DEFAULT_TOLERANCES.items():
        print(
            f"{metric:<24}{_fmt(reference.get(metric)):<12}"
            f"{_fmt(candidate.get(metric)):<12}"
            f"{('-' if direction == 'higher' else '+')}{tolerance:<9}"
        )

    regressions = find_regressions(candidate, reference)

    print()

    if not regressions:
        print("PASS: no quality regression beyond tolerance.")
        return

    print("FAIL: quality regressed")

    for metric, ref, cand, allowed in regressions:
        print(
            f"  {metric}: {_fmt(cand)} vs reference {_fmt(ref)} "
            f"(allowed {_fmt(allowed)})"
        )

    sys.exit(1)


if __name__ == "__main__":
    main()
