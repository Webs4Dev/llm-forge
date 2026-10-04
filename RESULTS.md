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