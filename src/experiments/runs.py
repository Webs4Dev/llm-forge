"""Read run files of any vintage into one canonical record format.

Earlier scripts wrote three different layouts:
- baseline / exact cache: raw_output, total_latency, provider, no repeat
- model comparison:       output, latency, error, no provider, no cost
- prompt optimization:    output, latency, error, cost, prompt_version

Current runs (src.experiments.harness) write the canonical layout directly.
Every consumer (evaluate, summarize, check_quality) reads through load_run()
so old and new files can be compared side by side.
"""

import json
from pathlib import Path

from src.core.cost import calculate_cost, get_model_prices
from src.core.schema import validate_output
from src.optimization.normalize import normalize_json_output


def is_valid_json(text):
    try:
        json.loads(text)
        return True
    except (json.JSONDecodeError, TypeError):
        return False


def infer_provider(model):
    if model.startswith("claude"):
        return "anthropic"
    if model.startswith("gpt"):
        return "openai"
    return model


def _legacy_cost(raw, model):
    if raw.get("cost") is not None:
        return raw["cost"]

    try:
        input_price, output_price = get_model_prices(model)
    except ValueError:
        return None

    return calculate_cost(
        raw.get("input_tokens", 0),
        raw.get("output_tokens", 0),
        input_price,
        output_price,
    )


def normalize_record(raw):
    """Map one raw JSONL record to the canonical layout."""
    model = raw.get("model", "unknown")
    text = raw.get("raw_output", raw.get("output", "")) or ""
    error = bool(raw.get("error", False))

    # Older runs never streamed: their "ttft" was total latency, not TTFT.
    measured_ttft = "stream" in raw

    schema_valid, schema_error = validate_output(text)

    record = {
        "request_index": raw.get("request_index"),
        "case_id": raw["case_id"],
        "repeat": raw.get("repeat"),
        "provider": raw.get("provider") or infer_provider(model),
        "model": model,
        "prompt_version": raw.get("prompt_version", "v1"),
        "stream": bool(raw.get("stream", False)),
        "cache_hit": bool(raw.get("cache_hit", False)),
        "input_tokens": raw.get("input_tokens", 0),
        "output_tokens": raw.get("output_tokens", 0),
        "ttft": raw.get("ttft") if measured_ttft else None,
        "total_latency": raw.get("total_latency", raw.get("latency")),
        "cost": _legacy_cost(raw, model),
        "raw_output": text,
        "parse_success": raw.get("parse_success", is_valid_json(text)),
        "schema_valid": raw.get("schema_valid", schema_valid),
        "schema_error": raw.get("schema_error", schema_error),
        "error": error,
        "error_message": raw.get("error_message"),
    }

    return record


def load_run(path):
    """Load a run file as canonical records, numbering repeats per case."""
    path = Path(path)
    records = []

    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                records.append(normalize_record(json.loads(line)))

    seen = {}

    for record in records:
        seen[record["case_id"]] = seen.get(record["case_id"], 0) + 1

        if record["repeat"] is None:
            record["repeat"] = seen[record["case_id"]]

    return records


def parse_output(record):
    """Parse a record's output as JSON, tolerating Markdown code fences."""
    try:
        return json.loads(normalize_json_output(record["raw_output"]))
    except json.JSONDecodeError:
        return None


def load_metadata(run_path):
    """Return the run's metadata sidecar, or None for older runs."""
    meta_path = Path(run_path).with_suffix(".meta.json")

    if not meta_path.exists():
        return None

    return json.loads(meta_path.read_text(encoding="utf-8"))
