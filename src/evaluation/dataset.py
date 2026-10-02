import json
from pathlib import Path


def load_dataset(path):
    """
    Load a JSONL evaluation dataset.

    Each line must contain one evaluation case.
    """
    path = Path(path)

    cases = []

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                case = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Invalid JSON on line {line_number}"
                ) from error

            cases.append(case)

    return cases