# LLMForge — Support Ticket Assistant Workload

## Purpose

LLMForge uses one fixed workload so system changes can be measured fairly and reproducibly.

The workload is a **Support Ticket Assistant**. It receives a customer support ticket and returns:

- category
- urgency
- summary
- suggested reply
- escalation decision

The workload is designed for controlled experiments involving caching, concurrency, model selection, prompt optimization, latency, cost, and reliability.

---

## Input

Each request contains one customer support ticket as plain text.

The fixed policy is:

```text
data/policy/policy-v1.txt
```

The evaluation dataset is:

```text
data/datasets/tickets-seed.jsonl
```

The frozen experiment workload is:

```text
data/workloads/workload-300.jsonl
```

---

## Output Contract

The assistant returns JSON with exactly these logical fields:

```json
{
  "category": "billing",
  "urgency": "high",
  "summary": "Concise factual summary of the customer issue.",
  "suggested_reply": "Policy-compliant response to the customer.",
  "needs_escalation": true
}
```

### Categories

```text
billing
technical
account
delivery
refund
fraud
general
```

### Urgency

```text
low
medium
high
```

### Escalation

`needs_escalation` must be either:

```text
true
false
```

The output contract is fixed for the current workload.

---

## Policy

The baseline uses:

```text
data/policy/policy-v1.txt
```

The policy remains fixed during baseline measurements.

Changing the policy or prompt is an explicit experimental configuration change.

---

## Dataset

The evaluation dataset contains **100 stable support-ticket cases**.

```text
data/datasets/tickets-seed.jsonl
```

Each case has a stable `case_id`.

The dataset contains reference information used for offline evaluation, including:

- expected category
- expected urgency
- expected escalation
- gold summary
- important facts
- forbidden claims
- source facts
- safety information

---

## Frozen Workload

The official experiment workload is:

```text
data/workloads/workload-300.jsonl
```

It contains:

```text
300 total requests
100 unique tickets
200 duplicate requests
66.67% duplicate rate
```

Each record contains:

```text
request_index
case_id
ticket_text
```

The `request_index` identifies the request.

The `case_id` identifies the underlying ticket.

The workload sequence and content are frozen for controlled comparisons.

---

## Why Duplicates Exist

The duplicate requests are intentional.

They allow the project to measure the effect of exact caching under a realistic repeated-request workload.

The workload can therefore be used to measure:

- cache hit rate
- avoided LLM calls
- latency reduction
- cost reduction
- cache lookup overhead

The duplicate distribution must not be changed during controlled cache experiments.

---

## Dataset vs Workload

The dataset contains the unique evaluation cases.

The workload defines the exact request sequence used during experiments.

```text
tickets-seed.jsonl
       │
       │ 100 unique cases
       ↓
workload-300.jsonl
       │
       ├── 100 unique requests
       └── 200 duplicate requests
```

This keeps evaluation data and serving workload logically separate.

---

## Workload Rules

1. Use the frozen workload for controlled comparisons.
2. Do not replace it with randomly generated tickets.
3. Do not modify ticket content during an experiment.
4. Do not change the request sequence between configurations.
5. Do not introduce RAG.
6. Do not introduce AI agents or multi-agent systems.
7. Do not introduce vector databases.
8. Do not use tool-calling agents.
9. The policy is supplied directly to the model.
10. Evaluation is performed offline.
11. Evaluation is not part of serving latency.
12. Output-affecting configuration changes must be explicitly recorded.

---

## Baseline Configuration

The baseline uses:

```text
Temperature:       0
Fixed max_tokens
One ticket per request
Fixed policy
Fixed prompt version
No caching
No routing
No retries
No model fallback
```

The baseline establishes initial:

- quality
- latency
- token usage
- cost
- parsing behavior

The same workload can also be executed using `FakeProvider` for controlled infrastructure testing.

---

## Measurements

Generation runs record:

- request index
- case ID
- provider
- model
- input tokens
- output tokens
- TTFT
- total latency
- request cost
- raw output
- parse status
- errors

Cache experiments additionally record:

- cache hit/miss
- hit rate
- LLM calls avoided

### Summary Metrics

```text
Average latency
P50 latency
P95 latency
P99 latency
TTFT
Input tokens
Output tokens
Cost per request
Total cost
Parse/schema failures
Errors
```

The measured results are documented in:

```text
RESULTS.md
```

---

## Reproducibility

Controlled experiments should keep the following constant unless they are the variable being tested:

```text
Workload
Policy version
Dataset version
Prompt version
Output contract
Request sequence
```

Every intentional configuration change should be identified in the experiment.

---

## Frozen Components

For standard comparisons, keep these frozen:

- workload file
- ticket content
- request sequence
- case IDs
- policy version
- dataset version
- output contract

---

## Experimental Components

Experiments may change:

- provider
- model
- prompt version
- generation parameters
- exact cache
- concurrency
- routing
- reliability configuration
- other explicitly defined optimizations

Only change components relevant to the experiment.

---

## Exact Cache Experiment

The frozen workload contains:

```text
300 requests
100 unique requests
200 repeated requests
```

With a correctly functioning exact cache and no errors, the expected behavior is:

```text
100 LLM calls
200 cache hits
```

The experiment compares:

```text
Baseline
    ↓
Exact Cache
```

using the same workload.

Primary measurements:

- hit rate
- avoided LLM calls
- latency
- cost
- lookup overhead

---

## Concurrency Experiment

Concurrency experiments use the same 300-request workload.

Tested levels:

```text
1
2
5
10
```

Measurements include:

- total runtime
- throughput
- average latency
- P50
- P95
- P99
- errors

The goal is to identify a useful operating point rather than simply maximizing concurrency.

---

## Model Comparison

Model comparisons use the same frozen workload.

Models are compared using:

- latency
- token usage
- cost
- schema validity
- output quality
- evaluation metrics

The workload should not be regenerated between model comparisons.

---

## Prompt Optimization

Prompt optimization keeps the workload fixed while changing prompt-related configuration such as:

```text
system policy
user prompt
prompt version
output instructions
```

The objective is to reduce unnecessary token usage and cost while preserving acceptable quality and latency.

---

## Semantic Cache Experiment

Semantic caching is treated as a separate learning experiment.

A dedicated evaluation dataset is used to study:

- embeddings
- cosine similarity
- thresholds
- precision
- recall
- false positives
- false negatives

It does not modify the frozen 300-request workload.

---

## Evaluation

Evaluation is performed offline after generation.

It is not part of serving latency.

Evaluation can include:

```text
Schema validity
Category accuracy
Category macro-F1
Urgency accuracy
Urgency macro-F1
Escalation accuracy
Escalation macro-F1
Fact recall
Forbidden-claim detection
Semantic quality
```

The same evaluation methodology should be used when comparing configurations.

---

## Versioning

Important versions include:

```text
Dataset version
Workload version
Policy version
Prompt version
Output schema version
Experiment configuration
```

Output-affecting changes must be explicitly recorded.

This is especially important for caching because different output configurations must not incorrectly share cache entries.

---

## Core Principle

LLMForge follows:

```text
BASELINE
   ↓
MEASURE
   ↓
OPTIMIZE
   ↓
MEASURE AGAIN
   ↓
COMPARE
   ↓
UNDERSTAND TRADE-OFFS
```

An optimization is not successful merely because it improves latency or cost.

It must also be evaluated for its effect on:

```text
QUALITY
LATENCY
COST
THROUGHPUT
TOKENS
RELIABILITY
```

The frozen workload exists to make these comparisons fair, reproducible, and measurable.
```