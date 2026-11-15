// All values come from the recorded experiments in RESULTS.md.

export type Tone = "openai" | "anthropic";

export const baseline = [
  { name: "OpenAI", tone: "openai" as Tone, model: "gpt-5.6-luna", latency: 1.8198, p95: 2.5003, cost: 0.1075286 },
  { name: "Anthropic", tone: "anthropic" as Tone, model: "claude-haiku-4-5", latency: 2.1837, p95: 2.9269, cost: 0.651279 },
];

export const cache = [
  { name: "OpenAI", tone: "openai" as Tone, before: 1.8198, after: 0.6564, costBefore: 0.1075286, costAfter: 0.0362238 },
  { name: "Anthropic", tone: "anthropic" as Tone, before: 2.1837, after: 0.6923, costBefore: 0.651279, costAfter: 0.217461 },
];

export const concurrency = {
  levels: ["1", "2", "5", "10"],
  OpenAI: {
    time: [752.532, 374.7101, 154.941, 84.5526],
    throughput: [0.4, 0.8, 1.94, 3.55],
    p95: [3.5338, 3.3754, 3.4949, 3.6163],
    p99: [4.3176, 4.0296, 4.3611, 8.7271],
  },
  Anthropic: {
    time: [852.7475, 394.7488, 141.5359, 74.5153],
    throughput: [0.35, 0.76, 2.12, 4.03],
    p95: [5.0438, 3.3879, 3.1489, 3.2072],
    p99: [12.8613, 11.7462, 3.5373, 3.5555],
  },
};

export const modelQuality = [
  { metric: "Category acc.", gpt56: 90, gpt6: 90.91 },
  { metric: "Category F1", gpt56: 87.24, gpt6: 89.7 },
  { metric: "Urgency acc.", gpt56: 82, gpt6: 80.81 },
  { metric: "Urgency F1", gpt56: 80.85, gpt6: 79.51 },
  { metric: "Escalation acc.", gpt56: 97, gpt6: 96.97 },
  { metric: "Escalation F1", gpt56: 94.56, gpt6: 94.26 },
];

// 100-case golden dataset, V1 vs V2 prompt. Anthropic V1 was added to
// RESULTS.md on 2026-11-14 (first answer per ticket from the baseline run).
export const promptQuality = {
  openai: [
    { metric: "Category acc.", v1: 90, v2: 92 },
    { metric: "Category F1", v1: 87.24, v2: 90.54 },
    { metric: "Urgency acc.", v1: 82, v2: 80 },
    { metric: "Urgency F1", v1: 80.85, v2: 79.17 },
    { metric: "Escalation acc.", v1: 97, v2: 97 },
    { metric: "Escalation F1", v1: 94.56, v2: 94.56 },
  ],
  anthropic: [
    { metric: "Category acc.", v1: 80, v2: 88 },
    { metric: "Category F1", v1: 78.33, v2: 86.64 },
    { metric: "Urgency acc.", v1: 79, v2: 82 },
    { metric: "Urgency F1", v1: 77.66, v2: 81.33 },
    { metric: "Escalation acc.", v1: 97, v2: 85 },
    { metric: "Escalation F1", v1: 94.56, v2: 78.49 },
  ],
};

export const raceStages = [
  { id: "baseline", label: "Baseline", note: "300 requests, nothing optimized", openai: 1.8198, anthropic: 2.1837 },
  { id: "cache", label: "Exact cache", note: "200 of 300 calls served from cache", openai: 0.6564, anthropic: 0.6923 },
  { id: "prompt", label: "Prompt V2", note: "Shorter instructions, cache off", openai: 2.441, anthropic: 2.7975 },
];
