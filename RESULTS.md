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