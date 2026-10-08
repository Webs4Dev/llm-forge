# LLMForge --- LLM Production Optimization Lab
LLMForge is a learning-oriented laboratory for understanding and
optimizing production LLM applications.
It focuses on latency, TTFT, throughput, token usage, cost, caching,
concurrency, model selection, prompt efficiency, evaluation,
observability, and experiment methodology.
> Detailed benchmark results are maintained in
> [`RESULTS.md`](RESULTS.md).
## Philosophy
LLMForge follows:
``` text
BASELINE → MEASURE → OPTIMIZE → MEASURE AGAIN → COMPARE → UNDERSTAND TRADE-OFFS
```
The project emphasizes reproducible workloads, controlled variables,
quantitative measurement, paired comparisons, regression testing,
centralized pricing, and latency distributions.
The goal is to understand **why an optimization works, how it works, how
to measure it, and what trade-offs it introduces**.
## Scope
LLMForge focuses on LLM production optimization and intentionally
avoids:
-   RAG
-   AI agents
-   Multi-agent systems
-   Vector databases
-   Tool-calling agents
unless one becomes absolutely necessary for a specific experiment.
## Fixed Workload
The project uses a **Support Ticket Assistant** workload.
A customer ticket is converted into structured JSON:
``` json
{
  "category": "billing",
  "urgency": "high",
  "summary": "...",
  "suggested_reply": "...",
  "needs_escalation": true
}
```
Categories: `billing`, `technical`, `account`, `delivery`, `refund`,
`fraud`, `general`.
Urgency: `low`, `medium`, `high`.
The frozen workload is `data/workloads/workload-300.jsonl`. It contains
300 requests, 100 unique tickets, and 200 duplicate requests.
The workload should remain unchanged during controlled comparisons.
## Evaluation Dataset
The project contains a 100-case evaluation dataset with expected
category, urgency, escalation, gold summaries, required facts, forbidden
claims, source facts, and safety information.
Evaluation includes:
-   category accuracy / macro-F1
-   urgency accuracy / macro-F1
-   escalation accuracy / macro-F1
-   schema validity
-   fact recall
-   forbidden-claim detection
## Architecture
``` text
Client → API → Input Guard → Router → Cache → LLM → Output Validation → Cache Write → Response
                                      ├─ Exact Cache
                                      └─ Semantic Cache
PostgreSQL → observability / evaluation
Redis      → persistent/shared caching
```
Offline evaluation remains separate from the online request path.
## Technology Stack
**Backend:** Python, FastAPI, PostgreSQL, Redis, NumPy, pandas,
scikit-learn.
**Providers:** OpenAI, Anthropic, and FakeProvider for deterministic
local testing.
**Frontend:** React, TypeScript, Vite, Recharts, Lucide React, CSS.
## Repository Structure
``` text
llm-forge/
├── data/
│   ├── datasets/
│   ├── policy/
│   ├── prompts/
│   ├── runs/
│   └── workloads/
├── scripts/
├── src/
│   ├── core/
│   ├── evaluation/
│   ├── optimization/
│   └── providers/
├── tests/
├── frontend/
├── .env
├── docker-compose.yaml
├── pricing.yaml
├── RESULTS.md
├── WORKLOAD.md
└── README.md
```
## Provider Abstraction
LLMForge uses a common provider interface so experiments can run against
different providers without changing application logic.
A generation result contains:
``` text
text
input_tokens
output_tokens
ttft
total_latency
```
### FakeProvider
FakeProvider provides deterministic local behavior with configurable
response, token counts, and artificial latency. It is useful for
infrastructure experiments without API costs and is not a production
model.
## Pricing
Provider pricing is centralized in `pricing.yaml`.
Experiment scripts should load prices from this file instead of
hardcoding them. This keeps cost calculations consistent across
experiments.
## Exact Cache
The exact cache key includes output-changing configuration such as:
``` text
model
temperature
max_tokens
system prompt
user prompt
```
Conceptually:
``` text
hash(model + temperature + max_tokens + system_prompt + user_prompt)
```
Every output-changing factor must be represented in the key.
The cache interface is designed to evolve from:
``` text
in-memory → persistent → Redis
```
without changing generation logic.
## Redis
Redis provides shared/persistent exact caching with GET, SET, TTL,
deletion, clearing, and hit/miss tracking.
Redis enables shared cache state across processes but introduces a
network hop, making in-memory vs Redis an important production
comparison.
## Concurrency
Concurrency experiments evaluate throughput, total execution time,
average latency, P50, P95, and P99.
Tested levels:
``` text
1
2
5
10
```
The goal is not simply maximum throughput; tail latency, provider
saturation, and stability also matter.
Measured results are documented in `RESULTS.md`.
## Model Comparison
Models are compared using the same workload and evaluation methodology.
Comparison dimensions include latency, token usage, cost, schema
validity, classification quality, fact recall, and forbidden claims.
A newer or more capable model is not automatically considered better.
## Evaluation Methodology
Evaluation is layered:
1.  **Format:** JSON validity, required fields, types, schema.
2.  **Deterministic correctness:** category, urgency, escalation,
    required facts, forbidden claims.
3.  **Semantic evaluation:** similarity where exact matching is
    insufficient.
4.  **Judge evaluation:** LLM-as-judge where deterministic evaluation is
    insufficient.
5.  **Hallucination and safety:** unsupported or unsafe output
    detection.
The project avoids relying on a single metric.
## Semantic Cache Learning Experiment
Semantic caching is treated as a separate learning experiment rather
than automatically integrating it into the main generation path.
It explores embeddings, normalized vectors, cosine similarity,
thresholds, precision, recall, false positives, and false negatives.
Key lesson:
> Semantic similarity does not automatically mean two requests are safe
> to serve with the same cached output.
## Prompt Optimization
Prompt optimization compares system policy, user prompt, and output
instructions.
The objective is to reduce unnecessary instruction tokens while
preserving quality.
Metrics include input tokens, output tokens, latency, cost, schema
validity, classification quality, fact recall, and forbidden claims.
Detailed measurements belong in `RESULTS.md`.
## Experiment Discipline
Experiments follow these rules:
-   Treat configurations as immutable.
-   Change one major variable at a time where possible.
-   Use the same workload for paired comparisons.
-   Measure P50, P95, and P99, not only averages.
-   Calculate cost from actual token usage and `pricing.yaml`.
-   Run regression evaluation after optimization.
Typical comparisons:
``` text
Baseline → Cache
Baseline → Concurrency
Model A → Model B
Prompt V1 → Prompt V2
```
## Observability
The observability layer is intended to record:
``` text
request ID
experiment ID
provider
model
latency
TTFT
input tokens
output tokens
cost
cache status
error status
evaluation result
```
This supports analysis of cost, latency, caching, quality, and
reliability.
## Testing
Typical test areas include provider behavior, schema validation, cache
behavior, Redis cache behavior, dataset validation, evaluation, and
concurrency.
Run all tests:
``` bash
pytest
```
Run one test:
``` bash
pytest tests/test_schema.py
```
## Docker
Start supporting services:
``` bash
docker compose up -d
```
Check containers:
``` bash
docker ps
```
Stop services:
``` bash
docker compose down
```
## Backend Setup
Create and activate a Python environment:
``` bash
python -m venv venv
source venv/bin/activate
```
Install dependencies according to the current project configuration.
Set provider credentials in `.env`:
``` text
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
```
Never commit API keys.
## Running Experiments
Typical workflow:
``` bash
python -m scripts.run_baseline
python -m scripts.summarize
```
Then:
1.  Implement one optimization.
2.  Run the same frozen workload.
3.  Compare latency, cost, tokens, quality, and errors.
4.  Record measurements in `RESULTS.md`.
Numerical benchmark results belong in `RESULTS.md`, not this README.
## Frontend
The React dashboard is located at `frontend/`.
Run it:
``` bash
cd frontend
npm install
npm run dev
```
Build it:
``` bash
npm run build
```
Current sections:
``` text
Overview
Baseline
Exact Cache
Concurrency
Model Comparison
Prompt Optimization
```
The frontend is independent of the Python experiment runtime.
## Dashboard Design
The dashboard uses a dark observability-style interface.
Provider colors:
``` text
OpenAI → white
Anthropic → orange
```
It includes interactive charts, KPI cards, hover effects, transitions,
provider legends, experiment navigation, and responsive layout.
## Documentation Structure
`README.md` explains the project, architecture, methodology, setup,
usage, and concepts.
`RESULTS.md` contains measured experiment results, benchmark tables,
observations, and decisions.
`WORKLOAD.md` documents workload structure, assumptions, and generation
details.
`frontend/README.md` documents the dashboard.
This separation prevents benchmark data from being duplicated across
documentation.
## Current Optimization Path
``` text
Baseline
   ↓
Exact Cache
   ↓
Concurrency
   ↓
Model Comparison
   ↓
Prompt Optimization
```
A separate semantic-cache learning experiment has also been performed.
Guardrails were considered but are currently skipped.
Detailed outcomes are maintained in `RESULTS.md`.
## Engineering Lessons
-   **Caching depends on workload duplication.**
-   **Maximum concurrency is not always optimal.**
-   **Cheaper models are not automatically better.**
-   **Prompt compression has trade-offs.**
-   **Semantic similarity is not semantic equivalence.**
-   **Average latency is not enough; tail latency matters.**
-   **Optimization requires evaluation.**
## Future Direction
The broader roadmap covers richer observability, evaluation
infrastructure, experiment frameworks, cache persistence, Redis
experiments, routing, reliability, latency optimization, cost
optimization, final benchmarks, and dashboard improvements.
Every future optimization should follow:
``` text
BASELINE
    ↓
MEASURE
    ↓
CHANGE ONE VARIABLE
    ↓
MEASURE AGAIN
    ↓
COMPARE
    ↓
DOCUMENT
```
## Final Principle
LLMForge is an **experimental framework for learning how LLM
applications behave in production**.
The central question is:
> **How do we make an LLM system better, and how can we prove that it
> actually became better?**
Measure:
``` text
QUALITY
LATENCY
COST
THROUGHPUT
TOKENS
RELIABILITY
```
**Measure first. Optimize deliberately. Measure again. Understand the
trade-offs.**
## Related Documentation
-   [`RESULTS.md`](RESULTS.md) --- experiment results and benchmarks
-   [`WORKLOAD.md`](WORKLOAD.md) --- workload documentation
    documentation
