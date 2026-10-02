import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src.evaluation.dataset import load_dataset


DATASET_PATH = (
    PROJECT_ROOT
    / "data"
    / "datasets"
    / "tickets-seed.jsonl"
)


def test_load_dataset():
    cases = load_dataset(DATASET_PATH)

    assert len(cases) == 30


def test_first_case_structure():
    cases = load_dataset(DATASET_PATH)

    case = cases[0]

    assert case["case_id"] == "T001"
    assert case["dataset_version"] == "v1"
    assert case["split"] == "dev"

    assert "input" in case
    assert "reference" in case


def test_reference_fields():
    cases = load_dataset(DATASET_PATH)

    reference = cases[0]["reference"]

    assert "category" in reference
    assert "urgency" in reference
    assert "needs_escalation" in reference
    assert "gold_summary" in reference
    assert "must_include_facts" in reference
    assert "must_not_claim" in reference