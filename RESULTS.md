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
| Avg Summary Similarity | 92.24% | N/A |
| P50 Summary Similarity | 94.17% | N/A |
| P95 Summary Similarity | 99.81% | N/A |
| Category Consistency | 98.67% | N/A |
| Urgency Consistency | 97.33% | N/A |
| Escalation Consistency | 100% | N/A |

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
| Avg Summary Similarity | N/A | 87.41% | — |
| P50 Summary Similarity | N/A | 89.27% | — |
| P95 Summary Similarity | N/A | 96.54% | — |
| Category Consistency | N/A | 100% | — |
| Urgency Consistency | N/A | 99.33% | — |
| Escalation Consistency | N/A | 94.00% | — |

## Optimization 2 — Native Structured Output

### OpenAI

| Metric | Before | After | Improvement |
|---|---:|---:|---:|
| JSON Parse Failure | 0% | 0% | 0 pp |
| Schema Validity | 100% | 100% | 0 pp |
| Category Accuracy | 86.67% | 86.67% | 0 pp |
| Urgency Accuracy | 82.67% | 83.33% | +0.66 pp |
| Escalation Accuracy | 100% | 100% | 0 pp |
| Category F1 | 81.30% | 80.48% | -0.82 pp |
| Urgency F1 | 82.36% | 83.19% | +0.83 pp |
| Escalation F1 | 100% | 100% | 0 pp |
| Fact Recall | 43.44% | 43.89% | +0.45 pp |
| Forbidden Claim Rate | 0% | 2.00% | +2 pp |
| Avg Summary Similarity | 92.24% | 91.89% | -0.35 pp |
| P50 Summary Similarity | 94.17% | 93.82% | -0.35 pp |
| P95 Summary Similarity | 99.81% | 99.56% | -0.25 pp |
| Category Consistency | 98.67% | 100% | +1.33 pp |
| Urgency Consistency | 97.33% | 100% | +2.67 pp |
| Escalation Consistency | 100% | 100% | 0 pp |

### Anthropic

| Metric | Before | After | Improvement |
|---|---:|---:|---:|
| JSON Parse Failure | 100% | 0% | -100 pp |
| Schema Validity | 0% | 100% | +100 pp |
| Category Accuracy | 83.33% | 80.67% | -2.66 pp |
| Urgency Accuracy | 84.00% | 83.33% | -0.67 pp |
| Escalation Accuracy | 92.00% | 97.33% | +5.33 pp |
| Category F1 | 82.32% | 78.32% | -4.00 pp |
| Urgency F1 | 83.76% | 83.19% | -0.57 pp |
| Escalation F1 | 87.80% | 95.48% | +7.68 pp |
| Fact Recall | 36.56% | 35.33% | -1.23 pp |
| Forbidden Claim Rate | 0% | 0% | 0 pp |
| Avg Summary Similarity | 87.41% | 87.98% | +0.57 pp |
| P50 Summary Similarity | 89.27% | 89.76% | +0.49 pp |
| P95 Summary Similarity | 96.54% | 96.54% | 0 pp |
| Category Consistency | 100% | 99.33% | -0.67 pp |
| Urgency Consistency | 99.33% | 100% | +0.67 pp |
| Escalation Consistency | 94.00% | 97.33% | +3.33 pp |