# LLMForge Results

## Baseline

| Metric | OpenAI | Anthropic |
|---|---:|---:|
| Model | gpt-5.6-luna | claude-haiku-4-5 |
| Requests | 150 | 150 |
| Avg Latency | 1.9313s | 2.0215s |
| P50 Latency | 1.8688s | 2.0116s |
| P95 Latency | 2.5072s | 2.4814s |
| P99 Latency | 3.0882s | 2.7982s |
| Avg TTFT | 1.9309s | 2.0211s |
| Avg Cost/Request | $0.00033420 | $0.00201940 |
| Total Cost | $0.05012940 | $0.30291000 |
| JSON Parse Failure | 0% | 100% |
| Schema Validity | 100% | 0% |
| Category Accuracy | 86.67% | N/A |
| Urgency Accuracy | 82.67% | N/A |
| Escalation Accuracy | 100% | N/A |
| Category F1 | 81.30% | N/A |
| Urgency F1 | 82.36% | N/A |
| Escalation F1 | 100% | N/A |
| Fact Recall | 43.44% | N/A |
| Forbidden Claim Rate | 0% | N/A |
| Category Consistency | 98.67% | N/A |
| Urgency Consistency | 97.33% | N/A |
| Escalation Consistency | 100% | N/A |

> Anthropic's `N/A` quality values are because the raw Markdown-fenced responses failed the current strict JSON parser.

---

## Optimization 1 — Anthropic JSON Fence Normalization

| Metric | Before | After | Improvement |
|---|---:|---:|---:|
| JSON Parse Failure | 100% | 0% | -100 pp |
| Schema Validity | 0% | 100% | +100 pp |
| Category Accuracy | N/A | 83.33% | — |
| Urgency Accuracy | N/A | 84.00% | — |
| Escalation Accuracy | N/A | 92.00% | — |
| Category F1 | N/A | 82.32% | — |
| Urgency F1 | N/A | 83.76% | — |
| Escalation F1 | N/A | 87.80% | — |
| Fact Recall | N/A | 36.56% | — |
| Forbidden Claim Rate | N/A | 0% | — |
| Category Consistency | N/A | 100% | — |
| Urgency Consistency | N/A | 99.33% | — |
| Escalation Consistency | N/A | 94.00% | — |

---

## Optimization 2 — <name>

| Metric | Before | After | Improvement |
|---|---:|---:|---:|
| JSON Parse Failure | — | — | — |
| Schema Validity | — | — | — |
| Category Accuracy | — | — | — |
| Urgency Accuracy | — | — | — |
| Escalation Accuracy | — | — | — |
| Category F1 | — | — | — |
| Urgency F1 | — | — | — |
| Escalation F1 | — | — | — |
| Fact Recall | — | — | — |
| Forbidden Claim Rate | — | — | — |
| Avg Latency | — | — | — |
| Avg Cost/Request | — | — | — |