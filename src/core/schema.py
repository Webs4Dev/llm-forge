import json


ALLOWED_CATEGORIES = {
    "billing",
    "technical",
    "account",
    "delivery",
    "refund",
    "fraud",
    "general",
}

ALLOWED_URGENCY = {
    "low",
    "medium",
    "high",
}

REQUIRED_FIELDS = {
    "category",
    "urgency",
    "summary",
    "suggested_reply",
    "needs_escalation",
}


def validate_output(text):
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return False, "invalid_json"

    if not isinstance(data, dict):
        return False, "not_object"

    missing_fields = REQUIRED_FIELDS - set(data.keys())

    if missing_fields:
        return False, "missing_fields"

    if data["category"] not in ALLOWED_CATEGORIES:
        return False, "invalid_category"

    if data["urgency"] not in ALLOWED_URGENCY:
        return False, "invalid_urgency"

    if not isinstance(data["summary"], str):
        return False, "invalid_summary"

    if not isinstance(data["suggested_reply"], str):
        return False, "invalid_suggested_reply"

    if not isinstance(data["needs_escalation"], bool):
        return False, "invalid_needs_escalation"

    return True, None