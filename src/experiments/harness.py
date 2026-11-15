"""Shared experiment harness.

Every experiment script builds an ExperimentConfig and calls run_experiment().
The harness owns everything that must be identical across experiments:
workload loading, timing, concurrency, error capture, pricing, record layout,
statistics and run metadata. Experiments differ only in their config.

Each run writes two files under data/runs/<experiment>/ with a unique name:
  <stamp>_<provider>_<model>....jsonl      one canonical record per request
  <stamp>_<provider>_<model>....meta.json  config, summary, git commit,
                                           input file hashes, SDK versions
"""

import hashlib
import json
import platform
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from importlib import metadata as importlib_metadata
from pathlib import Path
from typing import Optional

from src.core.cost import PRICING_PATH, calculate_cost, get_model_prices
from src.core.generate import generate, policy_path, prompt_path
from src.core.schema import validate_output
from src.experiments.runs import is_valid_json
from src.experiments.stats import summarize_records


PROJECT_ROOT = Path(__file__).resolve().parents[2]

WORKLOAD_PATH = PROJECT_ROOT / "data" / "workloads" / "workload-300.jsonl"
RUNS_DIR = PROJECT_ROOT / "data" / "runs"

TOTAL_REQUESTS = 300

PROVIDERS = ["fake", "openai", "anthropic"]

DEFAULT_MODELS = {
    "fake": "fake",
    "openai": "gpt-5.6-luna",
    "anthropic": "claude-haiku-4-5",
}

FAKE_RESPONSE = json.dumps({
    "category": "general",
    "urgency": "low",
    "summary": "Fake provider response.",
    "suggested_reply": "This is a fake provider response.",
    "needs_escalation": False,
})


@dataclass
class ExperimentConfig:
    experiment: str
    provider: str
    model: str
    prompt_version: str = "v1"
    concurrency: int = 1
    stream: bool = False
    cache: bool = False
    limit: Optional[int] = None
    unique: bool = False
    temperature: float = 0.0
    max_tokens: int = 500
    fake_latency: float = 0.1
    repeat: int = 1


def load_workload(limit=None, unique=False):
    """Load the frozen workload.

    unique=True keeps only the first request for each of the 100 unique
    tickets. Use it for anything except cache experiments: the 200 duplicate
    requests add API cost but no new information when there is no cache.
    """
    with open(WORKLOAD_PATH, "r", encoding="utf-8") as file:
        workload = [json.loads(line) for line in file if line.strip()]

    if len(workload) != TOTAL_REQUESTS:
        raise ValueError(
            f"Expected {TOTAL_REQUESTS} requests in {WORKLOAD_PATH}, "
            f"found {len(workload)}. The workload must stay frozen."
        )

    if unique:
        seen = set()
        first_only = []

        for request in workload:
            if request["case_id"] not in seen:
                seen.add(request["case_id"])
                first_only.append(request)

        workload = first_only

    if limit is not None:
        if limit <= 0 or limit > len(workload):
            raise ValueError(
                f"--limit must be between 1 and {len(workload)}."
            )

        workload = workload[:limit]

    return workload


def create_provider(provider_name, model, fake_latency=0.1):
    # Imported lazily so fake-only runs don't need API SDKs or keys.
    if provider_name == "fake":
        from src.providers.fake import FakeProvider

        return FakeProvider(
            response=FAKE_RESPONSE,
            input_tokens=100,
            output_tokens=50,
            latency=fake_latency,
        )

    if provider_name == "openai":
        from src.providers.openai import OpenAIProvider

        return OpenAIProvider(model)

    if provider_name == "anthropic":
        from src.providers.anthropic import AnthropicProvider

        return AnthropicProvider(model)

    raise ValueError(f"Unsupported provider: {provider_name}")


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _git_info():
    def git(*args):
        return subprocess.run(
            ["git", *args],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

    try:
        return {
            "commit": git("rev-parse", "HEAD"),
            "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
            "dirty": bool(git("status", "--porcelain")),
        }
    except (OSError, subprocess.CalledProcessError):
        return None


def _package_version(name):
    try:
        return importlib_metadata.version(name)
    except importlib_metadata.PackageNotFoundError:
        return None


def _output_stem(config, started):
    parts = [
        started.strftime("%Y%m%d-%H%M%S"),
        config.provider,
        config.model,
        config.prompt_version,
        f"c{config.concurrency}",
    ]

    if config.stream:
        parts.append("stream")

    if config.unique:
        parts.append("unique")

    if config.limit is not None:
        parts.append(f"limit{config.limit}")

    parts.append(f"r{config.repeat}")

    return "_".join(parts)


def _run_one(provider, request, config, cache, prices):
    start = time.perf_counter()

    record = {
        "request_index": request["request_index"],
        "case_id": request["case_id"],
        "provider": config.provider,
        "model": config.model,
        "prompt_version": config.prompt_version,
        "stream": config.stream,
        "concurrency": config.concurrency,
    }

    try:
        result = generate(
            provider=provider,
            ticket_text=request["ticket_text"],
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            cache=cache,
            prompt_version=config.prompt_version,
            stream=config.stream,
        )
    except Exception as error:  # recorded per request, never kills the run
        record.update({
            "cache_hit": False,
            "input_tokens": 0,
            "output_tokens": 0,
            "ttft": None,
            "total_latency": time.perf_counter() - start,
            "cost": 0.0,
            "raw_output": "",
            "parse_success": False,
            "schema_valid": False,
            "schema_error": "request_error",
            "error": True,
            "error_message": f"{type(error).__name__}: {error}",
        })
        return record

    total_latency = time.perf_counter() - start
    schema_valid, schema_error = validate_output(result.text)

    record.update({
        "cache_hit": result.cache_hit,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
        "ttft": result.ttft if (config.stream or result.cache_hit) else None,
        "total_latency": total_latency,
        "cost": calculate_cost(
            result.input_tokens,
            result.output_tokens,
            *prices,
        ),
        "raw_output": result.text,
        "parse_success": is_valid_json(result.text),
        "schema_valid": schema_valid,
        "schema_error": schema_error,
        "error": False,
        "error_message": None,
    })

    return record


def run_experiment(
    config,
    cache=None,
    provider=None,
    output_dir=None,
    verbose=True,
):
    """Run one configuration over the workload. Returns (path, records, summary)."""
    workload = load_workload(config.limit, config.unique)
    prices = get_model_prices(config.model)

    if provider is None:
        provider = create_provider(
            config.provider,
            config.model,
            config.fake_latency,
        )

    started = datetime.now(timezone.utc)
    output_dir = Path(output_dir or RUNS_DIR / config.experiment)
    output_dir.mkdir(parents=True, exist_ok=True)

    stem = _output_stem(config, started)
    output_path = output_dir / f"{stem}.jsonl"
    counter = 2

    while output_path.exists():
        output_path = output_dir / f"{stem}-{counter}.jsonl"
        counter += 1

    records = []
    lock = threading.Lock()

    if verbose:
        print(
            f"Running {config.experiment}: provider={config.provider} "
            f"model={config.model} prompt={config.prompt_version} "
            f"concurrency={config.concurrency} stream={config.stream} "
            f"requests={len(workload)} repeat={config.repeat}"
        )

    wall_start = time.perf_counter()

    with open(output_path, "w", encoding="utf-8") as output_file:
        with ThreadPoolExecutor(max_workers=config.concurrency) as executor:
            futures = [
                executor.submit(
                    _run_one,
                    provider,
                    request,
                    config,
                    cache,
                    prices,
                )
                for request in workload
            ]

            for future in as_completed(futures):
                record = future.result()

                with lock:
                    records.append(record)
                    output_file.write(json.dumps(record) + "\n")
                    output_file.flush()

                    if verbose and len(records) % 25 == 0:
                        print(f"  {len(records)}/{len(workload)}")

    wall_time = time.perf_counter() - wall_start
    records.sort(key=lambda r: r["request_index"])
    summary = summarize_records(records, wall_time=wall_time)

    meta = {
        "run_file": output_path.name,
        "started_at": started.isoformat(),
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "config": asdict(config),
        "summary": summary,
        "pricing": {
            "input_per_1m_tokens": prices[0],
            "output_per_1m_tokens": prices[1],
        },
        "provider_settings": {
            "timeout_seconds": getattr(provider, "timeout", None),
            "max_retries": getattr(provider, "max_retries", None),
            # Providers do not send temperature; the API default is used.
            "temperature_sent": False,
        },
        "inputs": {
            "workload_sha256": _sha256(WORKLOAD_PATH),
            "policy_file": policy_path(config.prompt_version).name,
            "policy_sha256": _sha256(policy_path(config.prompt_version)),
            "prompt_file": prompt_path(config.prompt_version).name,
            "prompt_sha256": _sha256(prompt_path(config.prompt_version)),
            "pricing_sha256": _sha256(PRICING_PATH),
        },
        "git": _git_info(),
        "environment": {
            "python": platform.python_version(),
            "anthropic": _package_version("anthropic"),
            "openai": _package_version("openai"),
            "argv": sys.argv,
        },
    }

    output_path.with_suffix(".meta.json").write_text(
        json.dumps(meta, indent=2),
        encoding="utf-8",
    )

    if verbose:
        print_summary(summary)
        print(f"Output: {output_path.relative_to(PROJECT_ROOT)}")

    return output_path, records, summary


def _fmt(value, spec, suffix=""):
    return "n/a" if value is None else f"{value:{spec}}{suffix}"


def print_summary(summary):
    print("-" * 60)
    print(
        f"Requests: {summary['requests']}  "
        f"errors: {summary['errors']}  "
        f"cache hits: {summary['cache_hits']}"
    )
    print(
        "Latency  mean "
        f"{_fmt(summary['latency_mean'], '.4f', 's')}  "
        f"P50 {_fmt(summary['latency_p50'], '.4f', 's')}  "
        f"P95 {_fmt(summary['latency_p95'], '.4f', 's')}  "
        f"P99 {_fmt(summary['latency_p99'], '.4f', 's')}"
    )
    print(
        f"TTFT     measured on {summary['ttft_measured']} requests  "
        f"mean {_fmt(summary['ttft_mean'], '.4f', 's')}  "
        f"P95 {_fmt(summary['ttft_p95'], '.4f', 's')}"
    )
    print(
        f"Tokens   in {summary['input_tokens']}  "
        f"out {summary['output_tokens']}"
    )
    print(
        f"Cost     total {_fmt(summary['total_cost'], '.6f')}  "
        f"per request {_fmt(summary['average_cost'], '.8f')}"
    )
    print(
        f"Wall     {_fmt(summary['wall_time'], '.2f', 's')}  "
        f"throughput {_fmt(summary['throughput'], '.2f', ' req/s')}"
    )
    print(
        f"Validity parse failures {summary['parse_failures']}  "
        f"schema failures {summary['schema_failures']}"
    )
    print("-" * 60)


def add_common_args(parser, provider_required=True):
    parser.add_argument(
        "--provider",
        choices=PROVIDERS,
        required=provider_required,
        default=None if provider_required else "openai",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model id (must exist in data/pricing.yaml). "
             "Defaults to the provider's baseline model.",
    )
    parser.add_argument("--prompt-version", default="v1")
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument(
        "--stream",
        action="store_true",
        help="Stream responses so real TTFT is measured.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only the first N requests (sanity checks).",
    )
    parser.add_argument(
        "--unique",
        action="store_true",
        help="Only the 100 unique tickets (skips the 200 duplicates).",
    )
    parser.add_argument(
        "--repeats",
        type=int,
        default=1,
        help="Run the same configuration N times (noise measurement).",
    )
    parser.add_argument(
        "--fake-latency",
        type=float,
        default=0.1,
        help="Artificial latency for the fake provider, in seconds.",
    )


def configs_from_args(experiment, args, **overrides):
    """One ExperimentConfig per requested repeat."""
    base = {
        "experiment": experiment,
        "provider": args.provider,
        "model": args.model or DEFAULT_MODELS[args.provider],
        "prompt_version": args.prompt_version,
        "concurrency": args.concurrency,
        "stream": args.stream,
        "limit": args.limit,
        "unique": args.unique,
        "fake_latency": args.fake_latency,
    }
    base.update(overrides)

    return [
        ExperimentConfig(**base, repeat=repeat)
        for repeat in range(1, args.repeats + 1)
    ]
