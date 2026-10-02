import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(PROJECT_ROOT)
)

from src.evaluation.dataset import load_dataset
from src.evaluation.semantic import calculate_summary_similarity


DATASET_PATH = (
    PROJECT_ROOT
    / "data"
    / "datasets"
    / "tickets-seed.jsonl"
)


def main():
    cases = load_dataset(DATASET_PATH)

    case = cases[0]

    reference = case["reference"]["gold_summary"]

    generated = (
        "The customer was charged twice "
        "for the same purchase."
    )

    score = calculate_summary_similarity(
        reference,
        generated,
    )

    print()
    print("=" * 60)
    print("LLMForge SEMANTIC EVALUATION")
    print("=" * 60)
    print()
    print("Reference:")
    print(reference)
    print()
    print("Generated:")
    print(generated)
    print()
    print(f"Cosine similarity: {score:.4f}")
    print()
    print("=" * 60)


if __name__ == "__main__":
    main()