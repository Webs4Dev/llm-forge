import json


def parse_output(text):
    """
    Parse a model's raw output as JSON.

    Returns:
        (parsed_output, None) on success
        (None, "invalid_json") on failure
    """
    try:
        return json.loads(text), None
    except json.JSONDecodeError:
        return None, "invalid_json"


def evaluate_fields(reference, output):
    """
    Compare deterministic fields against the golden reference.

    Fields:
        - category
        - urgency
        - needs_escalation
    """
    results = {}

    fields = [
        "category",
        "urgency",
        "needs_escalation",
    ]

    for field in fields:
        expected = reference[field]
        actual = output.get(field)

        results[field] = {
            "expected": expected,
            "actual": actual,
            "correct": actual == expected,
        }

    return results


def calculate_field_accuracy(field_results):
    """
    Calculate 0/1 accuracy for each deterministic field.
    """
    accuracy = {}

    for field, result in field_results.items():
        accuracy[field] = (
            1.0 if result["correct"] else 0.0
        )

    return accuracy


def evaluate_required_facts(reference, output):
    """
    Check whether required facts appear in the model output.

    The check is case-insensitive and searches the model's
    summary and suggested reply.
    """

    text = " ".join(
        [
            output.get("summary", ""),
            output.get("suggested_reply", ""),
        ]
    ).lower()

    facts = reference.get("must_include_facts", [])

    results = []

    for fact in facts:
        found = fact.lower() in text

        results.append(
            {
                "fact": fact,
                "found": found,
            }
        )

    return results


def calculate_fact_recall(fact_results):
    """
    Calculate the percentage of required facts found.
    """

    if not fact_results:
        return 1.0

    found_count = sum(
        1
        for result in fact_results
        if result["found"]
    )

    return found_count / len(fact_results)


def evaluate_forbidden_claims(reference, output):
    """
    Check whether the model made any forbidden claims.

    The check is case-insensitive and searches the model's
    summary and suggested reply.
    """

    text = " ".join(
        [
            output.get("summary", ""),
            output.get("suggested_reply", ""),
        ]
    ).lower()

    forbidden_claims = reference.get(
        "must_not_claim",
        [],
    )

    results = []

    for claim in forbidden_claims:
        found = claim.lower() in text

        results.append(
            {
                "claim": claim,
                "found": found,
            }
        )

    return results


def calculate_forbidden_claim_score(claim_results):
    """
    Return 1.0 when no forbidden claims were detected.

    Return 0.0 if at least one forbidden claim was detected.
    """

    if not claim_results:
        return 1.0

    for result in claim_results:
        if result["found"]:
            return 0.0

    return 1.0


def evaluate_case(case, output):
    """
    Evaluate one dataset case against one model output.
    """

    reference = case["reference"]

    field_results = evaluate_fields(
        reference,
        output,
    )

    accuracy = calculate_field_accuracy(
        field_results
    )

    fact_results = evaluate_required_facts(
        reference,
        output,
    )

    fact_recall = calculate_fact_recall(
        fact_results
    )

    forbidden_claim_results = evaluate_forbidden_claims(
        reference,
        output,
    )

    forbidden_claim_score = (
        calculate_forbidden_claim_score(
            forbidden_claim_results
        )
    )

    return {
        "case_id": case["case_id"],
        "dataset_version": case["dataset_version"],
        "field_results": field_results,
        "accuracy": accuracy,
        "fact_results": fact_results,
        "fact_recall": fact_recall,
        "forbidden_claim_results": forbidden_claim_results,
        "forbidden_claim_score": forbidden_claim_score,
    }