import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src.evaluation.dataset import load_dataset
from src.evaluation.deterministic import evaluate_case


DATASET_PATH = (
    PROJECT_ROOT
    / "data"
    / "datasets"
    / "tickets-seed.jsonl"
)


def main():
    cases = load_dataset(DATASET_PATH)

    case = cases[0]

    output = {
        "category": "billing",
        "urgency": "medium",
        "summary": (
            "The customer reports two charges "
            "for the same purchase."
        ),
        "suggested_reply": (
            "We will investigate the duplicate "
            "charges."
        ),
        "needs_escalation": False,
    }

    result = evaluate_case(
        case,
        output,
    )

    print()
    print("=" * 60)
    print("LLMForge EVALUATION DEMO")
    print("=" * 60)

    print()
    print(f"Case: {result['case_id']}")

    print()
    print("FIELD ACCURACY")
    print("-" * 60)

    for field, score in result["accuracy"].items():
        print(
            f"{field}: "
            f"{score:.1f}"
        )

    print()
    print(
        f"Fact recall: "
        f"{result['fact_recall']:.2f}"
    )

    print(
        f"Forbidden claim score: "
        f"{result['forbidden_claim_score']:.2f}"
    )

    print()
    print("=" * 60)


if __name__ == "__main__":
    main()