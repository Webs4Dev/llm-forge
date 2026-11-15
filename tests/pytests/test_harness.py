import json

import pytest

from src.experiments.harness import (
    ExperimentConfig,
    load_workload,
    run_experiment,
)
from src.experiments.runs import load_run
from src.providers.fake import FakeProvider


def config(**overrides):
    values = {
        "experiment": "test",
        "provider": "fake",
        "model": "fake",
        "fake_latency": 0.0,
        "limit": 10,
    }
    values.update(overrides)
    return ExperimentConfig(**values)


def test_workload_unique_keeps_one_request_per_ticket():
    workload = load_workload(unique=True)

    assert len(workload) == 100
    assert len({r["case_id"] for r in workload}) == 100


def test_workload_limit_validation():
    with pytest.raises(ValueError):
        load_workload(limit=0)


def test_run_writes_records_and_metadata(tmp_path):
    path, records, summary = run_experiment(
        config(concurrency=3),
        output_dir=tmp_path,
        verbose=False,
    )

    assert len(records) == 10
    assert summary["errors"] == 0
    assert [r["request_index"] for r in records] == sorted(
        r["request_index"] for r in records
    )

    meta = json.loads(path.with_suffix(".meta.json").read_text())
    assert meta["config"]["concurrency"] == 3
    assert meta["inputs"]["workload_sha256"]
    assert meta["provider_settings"]["temperature_sent"] is False

    # Harness output reads back through the shared loader unchanged.
    assert len(load_run(path)) == 10


def test_runs_never_overwrite_each_other(tmp_path):
    first, _, _ = run_experiment(config(), output_dir=tmp_path, verbose=False)
    second, _, _ = run_experiment(config(), output_dir=tmp_path, verbose=False)

    assert first != second


def test_non_streamed_runs_do_not_report_ttft(tmp_path):
    _, records, _ = run_experiment(config(), output_dir=tmp_path, verbose=False)
    assert all(r["ttft"] is None for r in records)

    _, records, _ = run_experiment(
        config(stream=True),
        output_dir=tmp_path,
        verbose=False,
    )
    assert all(r["ttft"] is not None for r in records)


class FlakyProvider(FakeProvider):
    """Fails every third call."""

    def __init__(self):
        super().__init__(response="{}")
        self.calls = 0

    def generate(self, *args, **kwargs):
        self.calls += 1

        if self.calls % 3 == 0:
            raise TimeoutError("simulated timeout")

        return super().generate(*args, **kwargs)


def test_errors_are_recorded_and_do_not_stop_the_run(tmp_path):
    _, records, summary = run_experiment(
        config(limit=9),
        provider=FlakyProvider(),
        output_dir=tmp_path,
        verbose=False,
    )

    assert len(records) == 9
    assert summary["errors"] == 3
    failed = [r for r in records if r["error"]]
    assert all("TimeoutError" in r["error_message"] for r in failed)
    assert all(r["cost"] == 0.0 for r in failed)
