from sklearn.metrics import f1_score

from src.evaluation.deterministic import evaluate_case
from src.core.schema import validate_output


def evaluate_dataset(cases, outputs):
    """
    Evaluate all dataset cases.

    Args:
        cases: List of dataset cases.
        outputs: Dictionary mapping case_id -> parsed model output.

    Returns:
        List of per-case evaluation results.
    """

    results = []

    for case in cases:
        case_id = case["case_id"]

        if case_id not in outputs:
            continue

        output = outputs[case_id]

        result = evaluate_case(
            case,
            output,
        )

        results.append(result)

    return results


def calculate_average_metric(results, metric):
    """
    Calculate the average value of a metric
    across evaluation results.
    """

    if not results:
        return 0.0

    values = [
        result[metric]
        for result in results
    ]

    return sum(values) / len(values)


def calculate_field_accuracy_summary(results):
    """
    Calculate average accuracy for each deterministic field.
    """

    if not results:
        return {
            "category": 0.0,
            "urgency": 0.0,
            "needs_escalation": 0.0,
        }

    fields = [
        "category",
        "urgency",
        "needs_escalation",
    ]

    summary = {}

    for field in fields:
        values = [
            result["accuracy"][field]
            for result in results
        ]

        summary[field] = sum(values) / len(values)

    return summary


def calculate_macro_f1(cases, outputs, field):
    """
    Calculate macro-F1 for a categorical field.

    Fields supported:
        - category
        - urgency
        - needs_escalation
    """

    if not cases:
        return 0.0

    expected = []
    actual = []

    for case in cases:
        case_id = case["case_id"]

        if case_id not in outputs:
            continue

        expected.append(
            case["reference"][field]
        )

        actual.append(
            outputs[case_id].get(field)
        )

    if not expected:
        return 0.0

    return f1_score(
        expected,
        actual,
        average="macro",
        zero_division=0,
    )


def calculate_suite_summary(results, outputs=None):
    """
    Calculate the main deterministic evaluation metrics.
    """

    field_accuracy = calculate_field_accuracy_summary(
        results
    )

    fact_recall = calculate_average_metric(
        results,
        "fact_recall",
    )

    forbidden_claim_scores = [
        result["forbidden_claim_score"]
        for result in results
    ]

    forbidden_claim_rate = 0.0

    if forbidden_claim_scores:
        clean_count = sum(
            1
            for score in forbidden_claim_scores
            if score == 1.0
        )

        forbidden_claim_rate = (
            1.0
            - clean_count / len(
                forbidden_claim_scores
            )
        )

    schema_validity = 0.0

    if outputs is not None:
        schema_validity = calculate_schema_validity(
            outputs
        )

    return {
        "cases_evaluated": len(results),
        "category_accuracy": field_accuracy["category"],
        "urgency_accuracy": field_accuracy["urgency"],
        "needs_escalation_accuracy": (
            field_accuracy["needs_escalation"]
        ),
        "fact_recall": fact_recall,
        "forbidden_claim_rate": forbidden_claim_rate,
        "schema_validity": schema_validity,
    }

def calculate_schema_validity(outputs):
    """
    Calculate the percentage of outputs that satisfy
    the required LLMForge output schema.
    """

    if not outputs:
        return 0.0

    valid_count = 0

    for output in outputs.values():
        text = output

        if isinstance(output, dict):
            import json

            text = json.dumps(output)

        valid, _ = validate_output(text)

        if valid:
            valid_count += 1

    return valid_count / len(outputs)