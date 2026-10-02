from src.evaluation.suite import (
    evaluate_dataset,
    calculate_field_accuracy_summary,
    calculate_suite_summary,
    calculate_macro_f1,
    calculate_schema_validity
)


def make_case(
    case_id,
    category,
    urgency,
    escalation,
    facts=None,
    forbidden=None,
):
    return {
        "case_id": case_id,
        "dataset_version": "v1",
        "reference": {
            "category": category,
            "urgency": urgency,
            "needs_escalation": escalation,
            "must_include_facts": facts or [],
            "must_not_claim": forbidden or [],
        },
    }


def test_evaluate_dataset():
    cases = [
        make_case(
            "T001",
            "billing",
            "medium",
            False,
        ),
        make_case(
            "T002",
            "technical",
            "high",
            True,
        ),
    ]

    outputs = {
        "T001": {
            "category": "billing",
            "urgency": "medium",
            "needs_escalation": False,
            "summary": "",
            "suggested_reply": "",
        },
        "T002": {
            "category": "billing",
            "urgency": "high",
            "needs_escalation": True,
            "summary": "",
            "suggested_reply": "",
        },
    }

    results = evaluate_dataset(
        cases,
        outputs,
    )

    assert len(results) == 2

    assert results[0]["case_id"] == "T001"
    assert results[1]["case_id"] == "T002"


def test_field_accuracy_summary():
    results = [
        {
            "accuracy": {
                "category": 1.0,
                "urgency": 1.0,
                "needs_escalation": 1.0,
            }
        },
        {
            "accuracy": {
                "category": 0.0,
                "urgency": 1.0,
                "needs_escalation": 0.0,
            }
        },
    ]

    summary = calculate_field_accuracy_summary(
        results
    )

    assert summary["category"] == 0.5
    assert summary["urgency"] == 1.0
    assert summary["needs_escalation"] == 0.5


def test_suite_summary():
    results = [
        {
            "accuracy": {
                "category": 1.0,
                "urgency": 1.0,
                "needs_escalation": 1.0,
            },
            "fact_recall": 1.0,
            "forbidden_claim_score": 1.0,
        },
        {
            "accuracy": {
                "category": 0.0,
                "urgency": 1.0,
                "needs_escalation": 0.0,
            },
            "fact_recall": 0.5,
            "forbidden_claim_score": 0.0,
        },
    ]

    summary = calculate_suite_summary(
        results
    )

    assert summary["cases_evaluated"] == 2
    assert summary["category_accuracy"] == 0.5
    assert summary["urgency_accuracy"] == 1.0
    assert summary["needs_escalation_accuracy"] == 0.5
    assert summary["fact_recall"] == 0.75
    assert summary["forbidden_claim_rate"] == 0.5

def test_macro_f1_perfect_predictions():
    cases = [
        make_case(
            "T001",
            "billing",
            "medium",
            False,
        ),
        make_case(
            "T002",
            "technical",
            "high",
            True,
        ),
        make_case(
            "T003",
            "billing",
            "low",
            False,
        ),
    ]

    outputs = {
        "T001": {
            "category": "billing",
            "urgency": "medium",
            "needs_escalation": False,
        },
        "T002": {
            "category": "technical",
            "urgency": "high",
            "needs_escalation": True,
        },
        "T003": {
            "category": "billing",
            "urgency": "low",
            "needs_escalation": False,
        },
    }

    score = calculate_macro_f1(
        cases,
        outputs,
        "category",
    )

    assert score == 1.0


def test_macro_f1_with_wrong_prediction():
    cases = [
        make_case(
            "T001",
            "billing",
            "medium",
            False,
        ),
        make_case(
            "T002",
            "technical",
            "high",
            True,
        ),
        make_case(
            "T003",
            "billing",
            "low",
            False,
        ),
    ]

    outputs = {
        "T001": {
            "category": "billing",
            "urgency": "medium",
            "needs_escalation": False,
        },
        "T002": {
            "category": "billing",
            "urgency": "high",
            "needs_escalation": True,
        },
        "T003": {
            "category": "billing",
            "urgency": "low",
            "needs_escalation": False,
        },
    }

    score = calculate_macro_f1(
        cases,
        outputs,
        "category",
    )

    assert 0.0 <= score < 1.0


def test_schema_validity():
    outputs = {
        "T001": {
            "category": "billing",
            "urgency": "medium",
            "summary": "Customer reports a billing issue.",
            "suggested_reply": "We will investigate.",
            "needs_escalation": False,
        },
        "T002": {
            "category": "invalid_category",
            "urgency": "high",
            "summary": "Test",
            "suggested_reply": "Test",
            "needs_escalation": False,
        },
    }

    score = calculate_schema_validity(outputs)

    assert score == 0.5