import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src.evaluation.deterministic import (
    evaluate_case,
    evaluate_required_facts,
    calculate_fact_recall,
    evaluate_forbidden_claims,
    calculate_forbidden_claim_score,
)


def test_evaluate_case_all_correct():
    case = {
        "case_id": "T001",
        "dataset_version": "v1",
        "reference": {
            "category": "billing",
            "urgency": "medium",
            "needs_escalation": False,
            "must_include_facts": [
                "two charges",
                "same purchase",
            ],
            "must_not_claim": [
                "refund issued",
            ],
        },
    }

    output = {
        "category": "billing",
        "urgency": "medium",
        "needs_escalation": False,
        "summary": (
            "The customer reports two charges "
            "for the same purchase."
        ),
        "suggested_reply": (
            "We will investigate the two charges."
        ),
    }

    result = evaluate_case(case, output)

    assert result["accuracy"]["category"] == 1.0
    assert result["accuracy"]["urgency"] == 1.0
    assert result["accuracy"]["needs_escalation"] == 1.0

    assert result["fact_recall"] == 1.0
    assert result["forbidden_claim_score"] == 1.0


def test_evaluate_case_with_error():
    case = {
        "case_id": "T001",
        "dataset_version": "v1",
        "reference": {
            "category": "billing",
            "urgency": "medium",
            "needs_escalation": False,
            "must_include_facts": [
                "two charges",
                "same purchase",
            ],
            "must_not_claim": [
                "refund issued",
            ],
        },
    }

    output = {
        "category": "technical",
        "urgency": "high",
        "needs_escalation": False,
        "summary": "The customer has a billing issue.",
        "suggested_reply": "We will investigate.",
    }

    result = evaluate_case(case, output)

    assert result["accuracy"]["category"] == 0.0
    assert result["accuracy"]["urgency"] == 0.0
    assert result["accuracy"]["needs_escalation"] == 1.0

    assert result["fact_recall"] == 0.0
    assert result["forbidden_claim_score"] == 1.0


def test_required_facts_partial_match():
    reference = {
        "must_include_facts": [
            "two charges",
            "same purchase",
        ]
    }

    output = {
        "summary": "The customer reports two charges.",
        "suggested_reply": "We will investigate.",
    }

    results = evaluate_required_facts(
        reference,
        output,
    )

    assert results[0]["found"] is True
    assert results[1]["found"] is False

    assert calculate_fact_recall(results) == 0.5


def test_forbidden_claim_detected():
    reference = {
        "must_not_claim": [
            "refund issued",
        ]
    }

    output = {
        "summary": "A refund issued yesterday.",
        "suggested_reply": "",
    }

    results = evaluate_forbidden_claims(
        reference,
        output,
    )

    assert results[0]["found"] is True

    assert (
        calculate_forbidden_claim_score(results)
        == 0.0
    )


def test_no_forbidden_claim():
    reference = {
        "must_not_claim": [
            "refund issued",
        ]
    }

    output = {
        "summary": "The customer reports a duplicate charge.",
        "suggested_reply": "We will investigate.",
    }

    results = evaluate_forbidden_claims(
        reference,
        output,
    )

    assert results[0]["found"] is False

    assert (
        calculate_forbidden_claim_score(results)
        == 1.0
    )