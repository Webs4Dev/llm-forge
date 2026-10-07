# LLMForge Results

## Baseline

| Metric | Fake | OpenAI | Anthropic |
|---|---:|---:|---:|
| Model | fake | gpt-5.6-luna | claude-haiku-4-5 |
| Requests | 300 | 300 | 300 |
| Avg Latency | 0.1046s | 1.8198s | 2.1837s |
| P50 Latency | 0.1054s | 1.7255s | 2.0900s |
| P95 Latency | 0.1055s | 2.5003s | 2.9269s |
| P99 Latency | 0.1055s | 2.9376s | 3.5621s |
| Avg TTFT | 0.1042s | 1.8194s | 2.1833s |
| Total Input Tokens | 30,000 | 365,293 | 473,989 |
| Total Output Tokens | 15,000 | 28,725 | 35,458 |
| Avg Input Tokens/Request | 100.00 | 1,217.64 | 1,579.96 |
| Avg Output Tokens/Request | 50.00 | 95.75 | 118.19 |
| Avg Cost/Request | $0.00000000 | $0.00035843 | $0.00217093 |
| Total Cost | $0.00000000 | $0.10752860 | $0.65127900 |
| JSON Parse Failure | 0% | 0% | 0% |
| Schema Validity | 100% | 100% | 100% |

**Workload:** 300 requests across 100 unique tickets, with 200 duplicate requests (66.67% duplicate rate).

### Baseline Observations

- OpenAI had lower average latency than Anthropic: **1.8198s vs 2.1837s**.
- OpenAI was approximately **20% faster** on average latency.
- OpenAI cost **$0.10752860** for 300 requests.
- Anthropic cost **$0.65127900** for 300 requests.
- Anthropic was approximately **6.06× more expensive** per request than OpenAI.
- Both real providers achieved **0% JSON parse failures** and **100% schema validity**.
- FakeProvider is used as the deterministic local baseline with zero API cost.

## Optimization 1 — Exact Cache

| Metric | Fake | OpenAI | Anthropic |
|---|---:|---:|---:|
| Requests | 300 | 300 | 300 |
| Cache Hits | 200 | 200 | 200 |
| Cache Misses | 100 | 100 | 100 |
| Cache Hit Rate | 66.67% | 66.67% | 66.67% |
| LLM Calls | 100 | 100 | 100 |
| LLM Calls Avoided | 200 | 200 | 200 |
| Average Latency | 0.0359s | 0.6564s | 0.6923s |
| P50 Latency | 0.0010s | 0.0010s | 0.0009s |
| P95 Latency | 0.1076s | 2.2906s | 2.4540s |
| P99 Latency | 0.1079s | 3.1861s | 2.7327s |
| Average TTFT | — | 0.6552s | 0.6911s |
| Total Input Tokens | 10,000 | 121,755 | 157,986 |
| Total Output Tokens | 5,000 | 9,894 | 11,895 |
| Average Cost/Request | $0.00000000 | $0.00012075 | $0.00072487 |
| Total Cost | $0.00000000 | $0.03622380 | $0.21746100 |
| JSON Parse Failures | 0% | 0% | 0% |
| Schema Failures | 0% | 0% | 0% |

### Exact Cache Observations

- The frozen 300-request workload produced exactly **200 cache hits and 100 misses**, matching the expected 66.67% duplicate rate.
- Exact caching reduced OpenAI average latency from **1.8198s to 0.6564s**, a reduction of approximately **63.9%**.
- OpenAI total cost decreased from **$0.10752860 to $0.03622380**, a reduction of approximately **66.3%**.
- Exact caching reduced Anthropic average latency from **2.1837s to 0.6923s**, a reduction of approximately **68.3%**.
- Anthropic total cost decreased from **$0.65127900 to $0.21746100**, a reduction of approximately **66.6%**.
- The cache avoided **200 of 300 LLM calls**.
- All cache experiments produced **0 JSON parse failures**.
- The earlier OpenAI result of 169 hits / 131 misses was discarded because OpenAI and Anthropic were run concurrently against the same Redis database, while both experiments clear the cache at startup.
- The sequential OpenAI run produced the expected **200 hits / 100 misses** and is the official result.

## Optimization 2 — Concurrency

Concurrency was evaluated on the frozen 300-request workload using the Fake, OpenAI, and Anthropic providers.

The experiment compared concurrency levels of 1, 2, 5, and 10 while keeping the workload and generation parameters unchanged.

### Fake Provider

| Metric | Concurrency 1 | Concurrency 2 | Concurrency 5 | Concurrency 10 |
|---|---:|---:|---:|---:|
| Total Time | 31.2191s | 15.5961s | 6.2366s | **3.1370s** |
| Throughput | 9.61 req/s | 19.24 req/s | 48.10 req/s | **95.63 req/s** |
| Average Latency | 0.1040s | 0.1038s | 0.1035s | 0.1042s |
| P50 Latency | 0.1050s | 0.1049s | 0.1041s | 0.1050s |
| P95 Latency | 0.1051s | 0.1051s | 0.1051s | 0.1052s |
| P99 Latency | 0.1051s | 0.1051s | 0.1051s | 0.1052s |
| Errors | 0 | 0 | 0 | 0 |

### OpenAI — gpt-5.6-luna

| Metric | Concurrency 1 | Concurrency 2 | Concurrency 5 | Concurrency 10 |
|---|---:|---:|---:|---:|
| Total Time | 752.5320s | 374.7101s | 154.9410s | **84.5526s** |
| Throughput | 0.40 req/s | 0.80 req/s | 1.94 req/s | **3.55 req/s** |
| Average Latency | 2.5084s | **2.4886s** | 2.5458s | 2.7500s |
| P50 Latency | 2.3878s | 2.3980s | 2.4295s | 2.5462s |
| P95 Latency | **3.5338s** | **3.3754s** | 3.4949s | 3.6163s |
| P99 Latency | 4.3176s | 4.0296s | 4.3611s | **8.7271s** |
| Errors | 0 | 0 | 0 | 0 |

### Anthropic — claude-haiku-4-5

| Metric | Concurrency 1 | Concurrency 2 | Concurrency 5 | Concurrency 10 |
|---|---:|---:|---:|---:|
| Total Time | 852.7475s | 394.7488s | 141.5359s | **74.5153s** |
| Throughput | 0.35 req/s | 0.76 req/s | 2.12 req/s | **4.03 req/s** |
| Average Latency | 2.8424s | 2.6283s | **2.3372s** | 2.4140s |
| P50 Latency | 2.4858s | 2.4466s | **2.2605s** | 2.5214s |
| P95 Latency | 5.0438s | 3.3879s | **3.1489s** | 3.2072s |
| P99 Latency | 12.8613s | 11.7462s | **3.5373s** | 3.5555s |
| Errors | 0 | 0 | 0 | 0 |

### Concurrency Observations

- Concurrency substantially improved **total workload completion time and throughput** without materially changing individual request latency for the FakeProvider.
- FakeProvider total execution time decreased from **31.2191s at concurrency 1 to 3.1370s at concurrency 10**, approximately a 90% reduction.
- FakeProvider throughput increased from **9.61 req/s to 95.63 req/s**, approximately 10x.
- OpenAI total execution time decreased from **752.5320s to 84.5526s** at concurrency 10, an approximately 88.8% reduction.
- OpenAI throughput increased from **0.40 req/s to 3.55 req/s**.
- OpenAI concurrency 10 increased P99 latency from **4.3176s to 8.7271s**, indicating increased tail-latency variability at higher concurrency.
- Anthropic total execution time decreased from **852.7475s to 74.5153s** at concurrency 10.
- Anthropic throughput increased from **0.35 req/s to 4.03 req/s**.
- Anthropic achieved its lowest average latency and P95 latency at **concurrency 5**.
- All OpenAI and Anthropic experiments completed with **0 errors**.
- Concurrency improves **throughput and total workload completion time**, rather than directly reducing the underlying latency of an individual LLM request.

### Concurrency Decision

For the current LLMForge workload, **concurrency = 5** is selected as the balanced operating point for real LLM providers.

Concurrency 10 provides the highest throughput, but it introduces worse tail latency for OpenAI, particularly at P99. Concurrency 5 provides a substantial throughput improvement while maintaining better latency behavior.

Therefore:
```text
Selected concurrency = 5
```

## Optimization 3 — Model Comparison

Model comparison was performed using the same frozen 300-request workload, policy, prompt, temperature, and maximum token configuration.

The experiment compared:

- `gpt-5.6-luna`
- `gpt-6-luna`

Each model processed all 300 requests independently, and the raw outputs were saved for offline evaluation.

### Performance and Cost

| Metric | GPT-5.6 Luna | GPT-6 Luna |
|---|---:|---:|
| Requests | 300 | 300 |
| Errors | 0 | 0 |
| Average Latency | 2.3335s | 3.3485s |
| P50 Latency | 2.0024s | 3.0684s |
| P95 Latency | 3.4796s | 5.0854s |
| P99 Latency | 9.0354s | 8.2999s |
| Average TTFT | 2.3335s | 3.3485s |
| Total Input Tokens | 365,293 | 365,293 |
| Total Output Tokens | 29,046 | 58,233 |
| Average Cost/Request | $0.00035971 | $0.00021882 |
| Total Cost | $0.10791380 | $0.06564580 |

### Quality Evaluation

The saved outputs were evaluated against the full **100-case golden dataset**.

GPT-5.6 Luna successfully produced parseable outputs for all 100 cases. GPT-6 Luna had one empty output for case `T043`, resulting in 99 successfully parsed outputs.

| Metric | GPT-5.6 Luna | GPT-6 Luna |
|---|---:|---:|
| Cases | 100 | 100 |
| Successfully Parsed | 100 | 99 |
| Schema Validity | 100% | 99% |
| Category Accuracy | 90.00% | 90.91% |
| Category Macro-F1 | 87.24% | 89.70% |
| Urgency Accuracy | 82.00% | 80.81% |
| Urgency Macro-F1 | 80.85% | 79.51% |
| Escalation Accuracy | 97.00% | 96.97% |
| Escalation Macro-F1 | 94.56% | 94.26% |
| Fact Recall | 41.87% | 42.29% |
| Forbidden-Claim Rate | 1.00% | 0% |

Classification metrics are calculated over successfully parsed outputs.

### Model Comparison Observations

- Both models completed all 300 generation requests without provider-level errors.
- GPT-6 Luna reduced total cost from `$0.10791380` to `$0.06564580`, approximately a **39% reduction**.
- GPT-6 Luna was approximately **43.5% slower** in average latency.
- GPT-6 Luna generated approximately twice as many output tokens.
- GPT-6 Luna achieved higher category accuracy and category macro-F1.
- GPT-5.6 Luna achieved better urgency accuracy and urgency macro-F1.
- Escalation performance was effectively tied, with GPT-5.6 Luna slightly higher.
- GPT-6 Luna achieved slightly higher fact recall.
- GPT-6 Luna had a **0% forbidden-claim rate**, compared with 1.00% for GPT-5.6 Luna.
- GPT-5.6 Luna had perfect parsing/schema validity, while GPT-6 Luna had one empty output.
- The results demonstrate a clear trade-off between latency, cost, classification quality, factual coverage, and output reliability.

### Decision

GPT-6 Luna is the stronger **cost-efficient candidate** because it is approximately 39% cheaper while achieving slightly better category performance, slightly better fact recall, and zero forbidden-claim violations in the 100-case evaluation.

However, GPT-5.6 Luna remains preferable for latency-sensitive workloads because it is substantially faster and had perfect parsing with stronger urgency performance.

Therefore, **model routing will not be implemented yet**.

The next optimization is **Prompt Optimization**. The goal is to determine whether the prompt can be reduced while preserving or improving quality and reducing input-token usage.

After prompt optimization, model routing can be evaluated again using the optimized configuration.

**Selected model for routing experiment: TBD**

## Optimization 4 — Prompt Optimization

The prompt optimization experiment evaluated a compressed version of the original policy and prompt.

The original V1 prompt was already evaluated during the baseline experiment, so V1 was not rerun. The existing baseline results are used as the control group.

The optimized V2 prompt reduced the static instruction size from 1,126 tokens to 601 tokens:

- Policy: 810 → 492 tokens (**39.26% reduction**)
- Prompt: 316 → 109 tokens (**65.51% reduction**)
- Total static instructions: 1,126 → 601 tokens (**46.63% reduction**)
- Estimated savings over 300 requests: **157,500 tokens**

The same frozen 300-request workload was then executed using V2 with caching disabled.

### OpenAI — GPT-5.6 Luna

| Metric | V1 Baseline | V2 | Change |
|---|---:|---:|---:|
| Requests | 300 | 300 | — |
| Errors | 0 | 0 | — |
| Average Latency | 1.8198s | 2.4410s | +34.1% |
| P50 Latency | 1.7255s | 2.2986s | +33.2% |
| P95 Latency | 2.5003s | 3.2986s | +31.9% |
| P99 Latency | 2.9376s | 6.2628s | +113.2% |
| Average TTFT | 1.8194s | 2.4410s | +34.2% |
| Input Tokens | 365,293 | 210,193 | **−42.46%** |
| Output Tokens | 28,725 | 33,720 | +17.39% |
| Average Cost/Request | $0.00035843 | $0.00027501 | **−23.28%** |
| Total Cost | $0.10752860 | $0.08250260 | **−23.27%** |

### Anthropic — Claude Haiku 4.5

| Metric | V1 Baseline | V2 | Change |
|---|---:|---:|---:|
| Requests | 300 | 300 | — |
| Errors | 0 | 0 | — |
| Average Latency | 2.1837s | 2.7975s | +28.1% |
| P50 Latency | 2.0900s | 2.7562s | +31.9% |
| P95 Latency | 2.9269s | 3.1757s | +8.5% |
| P99 Latency | 3.5621s | 3.3878s | **−4.9%** |
| Average TTFT | 2.1833s | 2.7975s | +28.1% |
| Input Tokens | 473,989 | 298,489 | **−37.03%** |
| Output Tokens | 35,458 | 32,360 | **−8.74%** |
| Average Cost/Request | $0.00217093 | $0.00153430 | **−29.33%** |
| Total Cost | $0.65127900 | $0.46028900 | **−29.33%** |

> V2 Anthropic cost is calculated using the project's pricing configuration rather than the incorrect hardcoded pricing used by the initial experiment script. The generation run itself was not repeated because the pricing calculation does not affect the generated outputs.

### Quality Evaluation — OpenAI

The V2 outputs were evaluated against the full 100-case golden dataset.

| Metric | V1 | V2 |
|---|---:|---:|
| Schema Validity | 100% | 100% |
| Category Accuracy | 90.00% | **92.00%** |
| Category Macro-F1 | 87.24% | **90.54%** |
| Urgency Accuracy | 82.00% | 80.00% |
| Urgency Macro-F1 | 80.85% | 79.17% |
| Escalation Accuracy | 97.00% | 97.00% |
| Escalation Macro-F1 | 94.56% | 94.56% |
| Fact Recall | 41.87% | **42.86%** |
| Forbidden-Claim Rate | 1.00% | **0%** |

### Quality Evaluation — Anthropic V2

| Metric | V2 |
|---|---:|
| Schema Validity | 100% |
| Category Accuracy | 88.00% |
| Category Macro-F1 | 86.64% |
| Urgency Accuracy | 82.00% |
| Urgency Macro-F1 | 81.33% |
| Escalation Accuracy | 85.00% |
| Escalation Macro-F1 | 78.49% |
| Fact Recall | 36.95% |
| Forbidden-Claim Rate | 0% |

### Prompt Optimization Observations

- V2 reduced estimated static instruction tokens by **46.63%**.
- OpenAI actual input tokens decreased by **42.46%**.
- Anthropic actual input tokens decreased by **37.03%**.
- OpenAI total cost decreased by approximately **23.27%**.
- Anthropic total cost decreased by approximately **29.33%**.
- Output tokens also decreased for Anthropic by approximately **8.74%**.
- Despite the reduction in input tokens, average latency increased for both providers.
- OpenAI P99 latency increased substantially, while Anthropic P99 latency improved slightly.
- For OpenAI, category accuracy and category macro-F1 improved, while urgency performance decreased slightly.
- OpenAI fact recall improved and forbidden-claim rate decreased from 1% to 0%.
- Both V2 runs maintained 100% schema validity.

### Decision

Prompt optimization successfully reduced token usage and cost for both providers, but it did **not** produce a latency improvement.

The optimized V2 prompt is therefore preferable when the primary objective is **reducing token usage and LLM cost**, while the latency trade-off must be considered.

For OpenAI, V2 also improved category classification and factual coverage while maintaining schema reliability.

For Anthropic, V2 reduced token usage and cost, but the complete V1-versus-V2 quality comparison should be interpreted separately from the OpenAI quality comparison.

**Selected prompt: V2 for cost-efficiency experiments**

The next optimization can investigate **LLM reliability, output guardrails, and structured-output failure handling**, while keeping the optimized prompt as the current configuration.