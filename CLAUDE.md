# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

LLMForge is a learning lab for measuring LLM production optimizations (caching, concurrency, model choice, prompt compression) on one fixed workload: a "Support Ticket Assistant" that turns a ticket into structured JSON (`category`, `urgency`, `summary`, `suggested_reply`, `needs_escalation`). Method: baseline → change one variable → re-run the same frozen workload → compare latency (P50/P95/P99), tokens, cost and quality, and check that differences exceed noise.

Out of scope unless an experiment truly needs it: RAG, agents, vector DBs, tool calling. FastAPI/PostgreSQL in the README are planned and not built yet. Everything runs as offline scripts.

## Commands

```bash
source venv/bin/activate          # Python 3.14; deps pinned in requirements.txt

pytest                            # all tests; free (no API, no Redis)
pytest tests/pytests/test_harness.py::test_errors_are_recorded_and_do_not_stop_the_run

docker compose up -d              # Redis for exact-cache runs (host port 6380)

# Experiments (always run as modules from the repo root). Shared flags:
# --provider fake|openai|anthropic --model --prompt-version --concurrency
# --stream --unique --limit --repeats --fake-latency
python -m scripts.run_baseline --provider fake --limit 10
python -m scripts.run_exact_cache --provider ...        # full workload only
python -m scripts.run_concurrency --provider ... [--levels 1 5]
python -m scripts.run_model_comparison --provider openai --model gpt-6-luna
python -m scripts.run_prompt_optimization --provider ...  # default v2

python -m scripts.summarize <run> | --provider openai | --compare <a> <b>
python -m scripts.evaluate <run> [--no-semantic]
python -m scripts.check_quality <candidate> --reference <run>   # exit 1 on regression

cd frontend && npm install && npm run dev   # static dashboard, http://localhost:5173
```

## API cost rule

Any command with `--provider openai|anthropic`, and `scripts/smoke/{openai,anthropic}_provider.py`, spends the user's API money. Never run one without the user's explicit approval for that specific run, and state the expected number of calls and estimated cost first. Recorded full 300-request runs cost about $0.11 (gpt-5.6-luna) and $0.65 (claude-haiku-4-5); `--unique` is one third of that. `--provider fake` and all tests are free.

## Architecture

- **Harness** (`src/experiments/harness.py`): every experiment script builds `ExperimentConfig`s and calls `run_experiment()`. The harness owns workload loading (300 frozen requests; `unique=True` gives the 100 unique tickets), a thread pool for concurrency, per-request error capture (errors are recorded and never abort a run), cost from `data/pricing.yaml`, and output. Each run writes `data/runs/<experiment>/<stamp>_<provider>_<model>_<prompt>_c<N>[...]_r<repeat>.jsonl` and a `.meta.json` sidecar (config, summary, git commit/dirty, input SHA-256s, SDK versions). New experiments should be new configs, not new loops.
- **Run loader** (`src/experiments/runs.py`): `load_run()` normalizes all record layouts (old baseline/cache files, old model-comparison/prompt-optimization files that use `output`/`latency`, new harness files) into one canonical record. `evaluate`, `summarize` and `check_quality` read only through it. Legacy records get `ttft=None` because old runs never streamed.
- **Stats** (`src/experiments/stats.py`): the single percentile definition (numpy linear interpolation), bootstrap CI and difference CI, and `summarize_records()`. Within-run CIs do not capture day-to-day drift; repeats do.
- **Providers** (`src/providers/`): `generate(system_prompt, user_prompt, temperature, max_tokens, stream) -> GenerationResult(text, input_tokens, output_tokens, ttft, total_latency, cache_hit)`. `ttft` is `None` unless streamed. Both real providers share `TICKET_OUTPUT_SCHEMA` from `src/core/schema.py` (kept byte-identical to the original requests), set an explicit `timeout=60` and `max_retries=2` (the SDK default), and **do not send `temperature`**, matching every recorded run. Sending it would change outputs vs. history, so it is the user's decision.
- **Generation** (`src/core/generate.py`): `prompt_version` selects `data/policy/policy-<v>.txt` and `data/prompts/tickets-<v>.txt`. With a cache (any `get`/`set` object), a hit returns zero tokens with the real lookup time and `cache_hit=True`. The cache key (`src/optimization/cache/key.py`) is SHA-256 of model, temperature, max_tokens and the full prompts. Add any new output-changing parameter to it.
- **Redis cache** (`src/optimization/cache/redis_cache.py`): keys are namespaced. `clear()` deletes only its own namespace (never FLUSHDB), so parallel runs don't interfere.
- **Evaluation** (`src/evaluation/`): `run_metrics.evaluate_run()` scores every request in a run (duplicates included) against `data/datasets/tickets-seed.jsonl`. `regression.find_regressions()` holds the tolerances. Semantic similarity loads sentence-transformers lazily, which is slow.
- **Frontend** (`frontend/`): a static React/Vite/Recharts dashboard. Its numbers are hand-copied from `RESULTS.md` into `src/data.ts` and `src/pages.tsx`. White = OpenAI, orange = Anthropic; hatched fill = before/old, solid fill = after/new.

## Conventions and pitfalls

- Frozen inputs in `data/` (workload, dataset, prompts, policies, `pricing.yaml`) are tracked in git. Never edit or regenerate them during comparisons (`scripts/create_workload.py`). `data/runs/` is gitignored and holds the only copy of past results, so don't delete it.
- Any model you run must have an entry in `data/pricing.yaml`. The harness refuses to run otherwise.
- `scripts/smoke/` holds manual scripts, not tests.
- Numerical results go in `RESULTS.md` (see its Measurement Notes), workload details in `WORKLOAD.md`, concepts in `README.md`.
