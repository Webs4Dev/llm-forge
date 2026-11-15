import json

from src.experiments.runs import load_run

VALID = json.dumps({
    "category": "billing",
    "urgency": "high",
    "summary": "s",
    "suggested_reply": "r",
    "needs_escalation": True,
})


def write_jsonl(path, rows):
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return path


def test_old_baseline_layout(tmp_path):
    path = write_jsonl(tmp_path / "baseline.jsonl", [
        {"request_index": 1, "case_id": "T1", "provider": "openai",
         "model": "gpt-5.6-luna", "input_tokens": 10, "output_tokens": 5,
         "ttft": 1.2, "total_latency": 1.2, "cost": 0.1,
         "raw_output": VALID, "parse_success": True, "schema_valid": True,
         "schema_error": None},
        {"request_index": 2, "case_id": "T1", "provider": "openai",
         "model": "gpt-5.6-luna", "input_tokens": 10, "output_tokens": 5,
         "ttft": 1.0, "total_latency": 1.0, "cost": 0.1,
         "raw_output": VALID, "parse_success": True, "schema_valid": True,
         "schema_error": None},
    ])

    records = load_run(path)

    assert [r["repeat"] for r in records] == [1, 2]
    # Old runs never streamed, so their "ttft" was really total latency.
    assert all(r["ttft"] is None for r in records)
    assert records[0]["error"] is False


def test_old_model_comparison_layout(tmp_path):
    path = write_jsonl(tmp_path / "gpt.jsonl", [
        {"request_index": 1, "case_id": "T1", "model": "gpt-5.6-luna",
         "ticket_text": "x", "output": VALID, "input_tokens": 1_000_000,
         "output_tokens": 0, "ttft": 2.0, "latency": 2.0, "error": False,
         "error_message": None},
        {"request_index": 2, "case_id": "T2", "model": "gpt-5.6-luna",
         "ticket_text": "y", "output": "", "input_tokens": 0,
         "output_tokens": 0, "ttft": 0.0, "latency": 0.5, "error": True,
         "error_message": "timeout"},
    ])

    first, second = load_run(path)

    assert first["provider"] == "openai"
    assert first["raw_output"] == VALID
    assert first["total_latency"] == 2.0
    # Cost is filled in from pricing.yaml (0.20 per 1M input tokens).
    assert abs(first["cost"] - 0.20) < 1e-9
    assert second["error"] is True
    assert second["schema_valid"] is False


def test_new_layout_keeps_measured_ttft(tmp_path):
    path = write_jsonl(tmp_path / "new.jsonl", [
        {"request_index": 1, "case_id": "T1", "provider": "anthropic",
         "model": "claude-haiku-4-5", "prompt_version": "v2",
         "stream": True, "cache_hit": False, "input_tokens": 10,
         "output_tokens": 5, "ttft": 0.3, "total_latency": 1.5,
         "cost": 0.01, "raw_output": VALID, "parse_success": True,
         "schema_valid": True, "schema_error": None, "error": False,
         "error_message": None},
    ])

    (record,) = load_run(path)

    assert record["ttft"] == 0.3
    assert record["prompt_version"] == "v2"
