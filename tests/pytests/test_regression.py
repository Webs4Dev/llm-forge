from src.evaluation.regression import find_regressions


REFERENCE = {
    "schema_validity": 1.0,
    "category_f1": 0.85,
    "urgency_f1": 0.75,
    "escalation_f1": 0.94,
    "fact_recall": 0.42,
    "forbidden_claim_rate": 0.0,
}


def test_small_changes_within_tolerance_pass():
    candidate = dict(REFERENCE, category_f1=0.84, forbidden_claim_rate=0.005)

    assert find_regressions(candidate, REFERENCE) == []


def test_large_drop_fails():
    candidate = dict(REFERENCE, escalation_f1=0.78)

    (regression,) = find_regressions(candidate, REFERENCE)

    assert regression[0] == "escalation_f1"


def test_rate_where_lower_is_better():
    candidate = dict(REFERENCE, forbidden_claim_rate=0.05)

    (regression,) = find_regressions(candidate, REFERENCE)

    assert regression[0] == "forbidden_claim_rate"


def test_any_schema_validity_drop_fails():
    candidate = dict(REFERENCE, schema_validity=0.99)

    assert find_regressions(candidate, REFERENCE)[0][0] == "schema_validity"
