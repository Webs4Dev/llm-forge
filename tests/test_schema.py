import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src.core.schema import validate_output


def test_valid_output():
    output = """
    {
        "category": "billing",
        "urgency": "medium",
        "summary": "Customer was charged twice.",
        "suggested_reply": "We will review the duplicate charge.",
        "needs_escalation": false
    }
    """

    valid, error = validate_output(output)

    assert valid is True
    assert error is None


def test_invalid_json():
    output = "this is not json"

    valid, error = validate_output(output)

    assert valid is False
    assert error == "invalid_json"


def test_missing_field():
    output = """
    {
        "category": "billing",
        "urgency": "medium",
        "summary": "Customer was charged twice.",
        "suggested_reply": "We will review the duplicate charge."
    }
    """

    valid, error = validate_output(output)

    assert valid is False
    assert error == "missing_fields"


def test_invalid_category():
    output = """
    {
        "category": "unknown",
        "urgency": "medium",
        "summary": "Customer was charged twice.",
        "suggested_reply": "We will review the duplicate charge.",
        "needs_escalation": false
    }
    """

    valid, error = validate_output(output)

    assert valid is False
    assert error == "invalid_category"


def test_invalid_urgency():
    output = """
    {
        "category": "billing",
        "urgency": "extreme",
        "summary": "Customer was charged twice.",
        "suggested_reply": "We will review the duplicate charge.",
        "needs_escalation": false
    }
    """

    valid, error = validate_output(output)

    assert valid is False
    assert error == "invalid_urgency"


def test_invalid_escalation_type():
    output = """
    {
        "category": "billing",
        "urgency": "medium",
        "summary": "Customer was charged twice.",
        "suggested_reply": "We will review the duplicate charge.",
        "needs_escalation": "false"
    }
    """

    valid, error = validate_output(output)

    assert valid is False
    assert error == "invalid_needs_escalation"