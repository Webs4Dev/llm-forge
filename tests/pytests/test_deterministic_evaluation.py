import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src.evaluation.deterministic import (
    parse_output,
    evaluate_fields,
    calculate_field_accuracy,
)


def test_parse_valid_json():
    text = """
    {
        "category": "billing",
        "urgency": "medium",
        "needs_escalation": false
    }
    """

    output, error = parse_output(text)

    assert error is None
    assert output["category"] == "billing"
    assert output["urgency"] == "medium"
    assert output["needs_escalation"] is False


def test_parse_invalid_json():
    text = "this is not json"

    output, error = parse_output(text)

    assert output is None
    assert error == "invalid_json"


def test_all_fields_correct():
    reference = {
        "category": "billing",
        "urgency": "medium",
        "needs_escalation": False,
    }

    output = {
        "category": "billing",
        "urgency": "medium",
        "needs_escalation": False,
    }

    results = evaluate_fields(reference, output)

    assert results["category"]["correct"] is True
    assert results["urgency"]["correct"] is True
    assert results["needs_escalation"]["correct"] is True


def test_one_field_incorrect():
    reference = {
        "category": "billing",
        "urgency": "medium",
        "needs_escalation": False,
    }

    output = {
        "category": "billing",
        "urgency": "high",
        "needs_escalation": False,
    }

    results = evaluate_fields(reference, output)

    assert results["category"]["correct"] is True
    assert results["urgency"]["correct"] is False
    assert results["needs_escalation"]["correct"] is True


def test_field_accuracy():
    field_results = {
        "category": {
            "correct": True,
        },
        "urgency": {
            "correct": False,
        },
        "needs_escalation": {
            "correct": True,
        },
    }

    accuracy = calculate_field_accuracy(field_results)

    assert accuracy["category"] == 1.0
    assert accuracy["urgency"] == 0.0
    assert accuracy["needs_escalation"] == 1.0