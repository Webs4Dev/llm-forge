# LLMForge — Support Ticket Assistant Workload

## Purpose

LLMForge uses one fixed workload throughout the project so that system changes can be measured fairly.

The workload is a Support Ticket Assistant. The assistant receives a customer support ticket and returns a structured response containing a category, urgency, concise summary, suggested reply, and escalation decision.

The workload is intentionally controlled so that later experiments can isolate the effects of caching, latency optimization, cost optimization, routing, reliability, guardrails, and other LLM engineering changes.

## Input

Each request contains one customer support ticket as plain text.

The request is evaluated together with the fixed policy:

`data/policy/policy-v1.txt`

The initial seed dataset is:

`data/datasets/tickets-seed.jsonl`

## Output Contract

The assistant should return JSON with exactly these logical fields:

```json
{
  "category": "billing",
  "urgency": "high",
  "summary": "Concise factual summary of the customer issue.",
  "suggested_reply": "Policy-compliant response to the customer.",
  "needs_escalation": true
}
```

### Allowed category values

- `billing`
- `technical`
- `account`
- `delivery`
- `refund`
- `fraud`
- `general`

### Allowed urgency values

- `low`
- `medium`
- `high`

### `needs_escalation`

Must be a boolean:

- `true`
- `false`

## Fixed Policy

The baseline workload uses:

`data/policy/policy-v1.txt`

The policy is fixed during baseline measurement.

A different policy version must be treated as an explicit experimental configuration change.

## Dataset

The initial workload contains 30 hand-written seed tickets.

Dataset file:

`data/datasets/tickets-seed.jsonl`

Each case has a stable `case_id`.

The dataset also contains reference information that will later support offline evaluation, including expected category, urgency, escalation, gold summary, important facts, forbidden claims, source facts, and safety information.

## Dataset Splits

The initial seed dataset contains development and test cases.

The `case_id` is the primary identifier used to match repeated observations of the same workload case.

Later evaluation datasets may be expanded, but changes to the dataset must be versioned and recorded.

## Workload Rules

1. Use the same underlying tickets when comparing system configurations.
2. Do not replace the workload with randomly generated tickets during baseline experiments.
3. Do not introduce RAG.
4. Do not introduce AI agents or multi-agent systems.
5. Do not introduce vector databases.
6. Do not use tool-calling agents.
7. The policy is context supplied directly to the model; it is not retrieved dynamically.
8. Changes to prompts, models, policies, generation parameters, caching, routing, reliability, or guardrails must be represented as configuration changes.
9. Evaluation is performed offline and is not part of the serving latency path.
10. The workload should remain stable while measuring the effect of an optimization.

## Baseline Generation Configuration

The first baseline will use:

- Temperature: `0`
- Fixed `max_tokens`
- One ticket per generation request
- Fixed policy
- Fixed prompt version
- No caching
- No routing
- No retries
- No guardrail layer
- No model fallback

The baseline exists to establish the initial quality, latency, token usage, cost, and parsing behavior before optimization.

## Measurements

For each generation request, the baseline should eventually record:

- Input token count
- Output token count
- Time to first token (TTFT)
- Total latency
- Request cost
- Raw model output
- JSON parse success/failure

The initial summary should report:

- p50 latency
- p95 latency
- p99 latency
- TTFT statistics
- cost per request
- parse failure rate

## Repetition

The first baseline experiment will run the 30 seed tickets five times sequentially:

`30 tickets × 5 repeats = 150 requests`

The same workload will also be runnable with the controlled `FakeProvider`.

## Frozen-vs-Experimental Components

### Frozen for baseline comparisons

- Seed ticket content
- Case IDs
- Policy version
- Dataset version
- Output contract

### Allowed to change in later experiments

- Model
- Prompt version
- Generation parameters
- Exact cache
- Semantic cache
- Routing
- Reliability configuration
- Guardrails
- Parallelization
- Other explicitly defined system optimizations

Every intentional change should be represented by a versioned experiment configuration.

## Core Experimental Principle

LLMForge follows:

**BASELINE → MEASURE → OPTIMIZE → MEASURE AGAIN → COMPARE → UNDERSTAND TRADE-OFFS**

An optimization is not considered successful merely because it improves latency or cost. Later experiments must also examine its effect on output quality and reliability.
