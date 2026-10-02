import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

sys.path.insert(
    0,
    str(PROJECT_ROOT)
)

from src.evaluation.semantic import (
    calculate_summary_similarity
)


def test_identical_summaries_have_high_similarity():
    text = (
        "The customer was charged twice "
        "for the same purchase."
    )

    score = calculate_summary_similarity(
        text,
        text,
    )

    assert score > 0.99


def test_similar_summaries_have_high_similarity():
    reference = (
        "The customer reports two charges "
        "for the same purchase."
    )

    generated = (
        "The customer says they were charged twice "
        "for the same purchase."
    )

    score = calculate_summary_similarity(
        reference,
        generated,
    )

    assert score > 0.70