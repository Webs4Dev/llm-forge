import { useState } from "react";
import {
  Activity,
  BarChart3,
  ChevronRight,
  Database,
  Layers3,
  Network,
  Zap,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  baseline,
  cache,
  concurrency,
  modelQuality,
  promptQuality,
} from "./data";
import type { Tone } from "./data";
import {
  ANTHROPIC,
  ChartTip,
  CompareTable,
  Dumbbell,
  Key,
  OPENAI,
  Panel,
  Race,
  Savings,
  StatStrip,
  Swatch,
  axisProps,
  cursorProps,
  fillFor,
  gridProps,
} from "./ui";
import type { Col, Row } from "./ui";

export type Section = "overview" | "baseline" | "cache" | "concurrency" | "models" | "prompt";

/* number formatters ------------------------------------------------- */
const sec4 = (n: number) => `${n.toFixed(4)}s`;
const sec2 = (n: number) => `${n.toFixed(2)}s`;
const int = (n: number) => n.toLocaleString("en-US");
const usd8 = (n: number) => `$${n.toFixed(8)}`;
const usd6 = (n: number) => `$${n.toFixed(6)}`;
const pct = (n: number) => `${+n.toFixed(2)}%`;
const rps = (n: number) => n.toFixed(2);

const OA: Col = { label: "OpenAI", tone: "openai" };
const AN: Col = { label: "Anthropic", tone: "anthropic" };
const barAnim = { animationDuration: 800, animationEasing: "ease-out" as const };

function Intro({ n, title, text }: { n?: string; title: string; text: string }) {
  return (
    <div className="page-intro">
      {n && <span className="intro-n">{n}</span>}
      <h2>{title}</h2>
      <p>{text}</p>
    </div>
  );
}

/* ================================================================== */
/* Overview                                                            */
/* ================================================================== */

export function Overview({ go }: { go: (s: Section) => void }) {
  const journey: { id: Section; n: string; name: string; stat: string; desc: string }[] = [
    { id: "baseline", n: "00", name: "Baseline", stat: "300 requests", desc: "Latency, tokens, cost and reliability, measured on both providers." },
    { id: "cache", n: "01", name: "Exact cache", stat: "200 calls avoided", desc: "A 66.67% hit rate cut both cost and latency sharply." },
    { id: "concurrency", n: "02", name: "Concurrency", stat: "5 at once", desc: "The balanced operating point for real providers." },
    { id: "models", n: "03", name: "Model comparison", stat: "−39% cost", desc: "GPT-6 is cheaper and better at categories, GPT-5.6 is faster." },
    { id: "prompt", n: "04", name: "Prompt optimization", stat: "−46.6% instructions", desc: "V2 lowers tokens and cost, but latency went up." },
  ];
  return (
    <>
      <div className="hero">
        <div className="hero-copy">
          <h2><span>Measure.</span> <span>Optimize.</span> <span>See the trade-offs.</span></h2>
          <p>
            Five experiments on the same 300-request support-ticket workload, run against OpenAI and Anthropic. Every table marks which side wins.
          </p>
        </div>
        <Race />
      </div>

      <StatStrip
        items={[
          { label: "Workload", value: "300", detail: "requests over 100 unique tickets", icon: Activity },
          { label: "Duplicate rate", value: "66.67%", detail: "200 repeated requests", icon: Database },
          { label: "Cache calls avoided", value: "200", detail: "of 300 LLM calls", icon: Zap },
          { label: "Selected concurrency", value: "5", detail: "balanced real-provider point", icon: Network },
        ]}
      />

      <div className="grid-2">
        <Panel title="Baseline latency" subtitle="Average seconds per request, lower is better" right={<Key items={[{ label: "OpenAI", tone: "openai" }, { label: "Anthropic", tone: "anthropic" }]} />}>
          <div className="chart">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={baseline} margin={{ top: 22, right: 8, left: -14, bottom: 0 }} barCategoryGap="32%">
                <CartesianGrid {...gridProps} />
                <XAxis dataKey="name" {...axisProps} />
                <YAxis {...axisProps} axisLine={false} tickFormatter={(v) => `${v}s`} />
                <Tooltip cursor={cursorProps} content={<ChartTip fmt={sec4} />} />
                <Bar dataKey="latency" name="Average latency" radius={[5, 5, 0, 0]} {...barAnim}>
                  {baseline.map((e) => <Cell key={e.name} fill={fillFor(e.tone)} />)}
                  <LabelList dataKey="latency" position="top" formatter={(v: number) => sec2(v)} fill="#f2f2f2" fontSize={12} />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>
        <Panel title="Total baseline cost" subtitle="USD for 300 requests, lower is better" right={<Key items={[{ label: "OpenAI", tone: "openai" }, { label: "Anthropic", tone: "anthropic" }]} />}>
          <div className="chart">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={baseline} margin={{ top: 22, right: 8, left: -4, bottom: 0 }} barCategoryGap="32%">
                <CartesianGrid {...gridProps} />
                <XAxis dataKey="name" {...axisProps} />
                <YAxis {...axisProps} axisLine={false} tickFormatter={(v) => `$${v}`} />
                <Tooltip cursor={cursorProps} content={<ChartTip fmt={usd6} />} />
                <Bar dataKey="cost" name="Total cost" radius={[5, 5, 0, 0]} {...barAnim}>
                  {baseline.map((e) => <Cell key={e.name} fill={fillFor(e.tone)} />)}
                  <LabelList dataKey="cost" position="top" formatter={(v: number) => `$${v.toFixed(3)}`} fill="#f2f2f2" fontSize={12} />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      </div>

      <Panel title="Optimization journey" subtitle="Pick an experiment to open its results">
        <div className="journey">
          {journey.map((j) => (
            <button className="journey-item" key={j.id} onClick={() => go(j.id)}>
              <span className="journey-n">{j.n}</span>
              <strong>{j.name}</strong>
              <em>{j.stat}</em>
              <p>{j.desc}</p>
              <ChevronRight size={17} className="journey-go" />
            </button>
          ))}
        </div>
      </Panel>
    </>
  );
}

/* ================================================================== */
/* Baseline                                                            */
/* ================================================================== */

export function Baseline() {
  const rows: Row[] = [
    { group: "Latency", label: "Average", vals: [1.8198, 2.1837], fmt: sec4, better: "lower" },
    { group: "Latency", label: "P50", vals: [1.7255, 2.09], fmt: sec4, better: "lower" },
    { group: "Latency", label: "P95", vals: [2.5003, 2.9269], fmt: sec4, better: "lower" },
    { group: "Latency", label: "P99", vals: [2.9376, 3.5621], fmt: sec4, better: "lower" },
    { group: "Tokens", label: "Total input tokens", vals: [365293, 473989], fmt: int, better: "lower" },
    { group: "Tokens", label: "Total output tokens", vals: [28725, 35458], fmt: int, better: "lower" },
    { group: "Cost", label: "Average cost per request", vals: [0.00035843, 0.00217093], fmt: usd8, better: "lower" },
    { group: "Cost", label: "Total cost", vals: [0.1075286, 0.651279], fmt: usd8, better: "lower" },
    { group: "Reliability", label: "JSON parse failures", vals: [0, 0], fmt: pct, better: "lower" },
    { group: "Reliability", label: "Schema validity", vals: [100, 100], fmt: pct, better: "higher" },
  ];
  return (
    <>
      <Intro n="00" title="Where the system started." text="300 requests across 100 unique tickets, with 200 duplicate requests." />
      <StatStrip
        items={[
          { label: "OpenAI average latency", value: "1.8198s", detail: "20% faster than Anthropic", icon: Activity, tone: "openai" },
          { label: "OpenAI total cost", value: "$0.107529", detail: "for 300 requests", icon: Zap, tone: "openai" },
          { label: "Anthropic total cost", value: "$0.651279", detail: "6.06× the OpenAI cost", icon: BarChart3, tone: "anthropic" },
          { label: "Schema validity", value: "100%", detail: "both providers", icon: Layers3 },
        ]}
      />
      <Panel title="Latency percentiles" subtitle="How far each provider's slowest requests stretch">
        <Dumbbell
          cols={[OA, AN]}
          max={4}
          ticks={[0, 1, 2, 3, 4]}
          fmt={(n) => `${n % 1 === 0 ? n : n.toFixed(2)}s`}
          rows={[
            { label: "Average", a: 1.8198, b: 2.1837 },
            { label: "P50", a: 1.7255, b: 2.09 },
            { label: "P95", a: 2.5003, b: 2.9269 },
            { label: "P99", a: 2.9376, b: 3.5621 },
          ]}
        />
      </Panel>
      <Panel title="Provider comparison" subtitle="Recorded baseline results">
        <CompareTable cols={[OA, AN]} edge rows={rows} />
      </Panel>
    </>
  );
}

/* ================================================================== */
/* Exact cache                                                         */
/* ================================================================== */

export function Cache() {
  const rows: Row[] = [
    { label: "Cache hits", vals: [200, 200], fmt: int, better: "higher" },
    { label: "Cache misses", vals: [100, 100], fmt: int, better: "lower" },
    { label: "Cache hit rate", vals: [66.67, 66.67], fmt: pct, better: "higher" },
    { label: "LLM calls", vals: [100, 100], fmt: int, better: "lower" },
    { label: "LLM calls avoided", vals: [200, 200], fmt: int, better: "higher" },
    { label: "Average latency", vals: [0.6564, 0.6923], fmt: sec4, better: "lower" },
    { label: "Total cost", vals: [0.0362238, 0.217461], fmt: usd8, better: "lower" },
  ];
  return (
    <>
      <Intro n="01" title="Reuse what already exists." text="Exact caching was evaluated against the frozen 300-request workload." />
      <StatStrip
        items={[
          { label: "Hit rate", value: "66.67%", detail: "200 hits, 100 misses", icon: Database },
          { label: "Calls avoided", value: "200", detail: "66.67% of the workload", icon: Zap },
          { label: "OpenAI latency", value: "−63.9%", detail: "1.8198s → 0.6564s", icon: Activity, tone: "openai" },
          { label: "Anthropic cost", value: "−66.6%", detail: "$0.651279 → $0.217461", icon: BarChart3, tone: "anthropic" },
        ]}
      />
      <div className="grid-2">
        <Panel title="Average latency" subtitle="Seconds per request, lower is better" right={<Key items={[{ label: "Before cache", tone: "openai", ghost: true, neutral: true }, { label: "After cache", neutral: true }]} />}>
          <div className="chart">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={cache} margin={{ top: 22, right: 8, left: -14, bottom: 0 }} barCategoryGap="28%" barGap={4}>
                <CartesianGrid {...gridProps} />
                <XAxis dataKey="name" {...axisProps} />
                <YAxis {...axisProps} axisLine={false} tickFormatter={(v) => `${v}s`} />
                <Tooltip cursor={cursorProps} content={<ChartTip fmt={sec4} ghostKeys={["before"]} />} />
                <Bar dataKey="before" name="Before cache" radius={[5, 5, 0, 0]} {...barAnim}>
                  {cache.map((e) => <Cell key={e.name} fill={fillFor(e.tone, true)} stroke={e.tone === "openai" ? OPENAI : ANTHROPIC} strokeWidth={1} />)}
                  <LabelList dataKey="before" position="top" formatter={(v: number) => sec2(v)} fill="#8c8c8c" fontSize={12} />
                </Bar>
                <Bar dataKey="after" name="After cache" radius={[5, 5, 0, 0]} {...barAnim}>
                  {cache.map((e) => <Cell key={e.name} fill={fillFor(e.tone)} />)}
                  <LabelList dataKey="after" position="top" formatter={(v: number) => sec2(v)} fill="#f2f2f2" fontSize={12} />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>
        <Panel title="Cache economics" subtitle="Total cost on one shared scale">
          <Savings items={cache.map((c) => ({ name: c.name, tone: c.tone, before: c.costBefore, after: c.costAfter }))} fmt={usd6} />
        </Panel>
      </div>
      <Panel title="Cache behavior" subtitle="Where one provider beats the other, and where they match">
        <CompareTable cols={[OA, AN]} edge rows={rows} />
      </Panel>
    </>
  );
}

/* ================================================================== */
/* Concurrency                                                         */
/* ================================================================== */

export function Concurrency() {
  const [level, setLevel] = useState("5");
  const li = concurrency.levels.indexOf(level);
  const oa = concurrency.OpenAI;
  const an = concurrency.Anthropic;

  const trend = concurrency.levels.map((l, i) => ({
    level: l,
    OpenAI: oa.throughput[i],
    Anthropic: an.throughput[i],
    OpenAIp99: oa.p99[i],
    Anthropicp99: an.p99[i],
  }));

  const atLevel: Row[] = [
    { label: "Throughput (req/s)", vals: [oa.throughput[li], an.throughput[li]], fmt: rps, better: "higher" },
    { label: "Total time", vals: [oa.time[li], an.time[li]], fmt: sec4, better: "lower" },
    { label: "P95 latency", vals: [oa.p95[li], an.p95[li]], fmt: sec4, better: "lower" },
    { label: "P99 latency", vals: [oa.p99[li], an.p99[li]], fmt: sec4, better: "lower" },
  ];

  const matrix: Row[] = [];
  const metrics: { g: string; key: "throughput" | "time" | "p95" | "p99"; fmt: (n: number) => string; better: "lower" | "higher" }[] = [
    { g: "Throughput (req/s)", key: "throughput", fmt: rps, better: "higher" },
    { g: "Total time", key: "time", fmt: sec4, better: "lower" },
    { g: "P95 latency", key: "p95", fmt: sec4, better: "lower" },
    { g: "P99 latency", key: "p99", fmt: sec4, better: "lower" },
  ];
  metrics.forEach((m) =>
    concurrency.levels.forEach((l, i) =>
      matrix.push({
        group: m.g,
        label: `Concurrency ${l}`,
        vals: [oa[m.key][i], an[m.key][i]],
        fmt: m.fmt,
        better: m.better,
        tag: l === "5" ? "selected" : undefined,
      })
    )
  );

  const lineTip = (fmt: (v: number) => string) => (
    <Tooltip cursor={{ stroke: "#3a3a3a" }} content={<ChartTip fmt={fmt} toneByName={{ OpenAI: "openai", Anthropic: "anthropic" }} />} />
  );

  return (
    <>
      <Intro n="02" title="More throughput, not magic latency." text="Concurrency levels 1, 2, 5 and 10 were tested without changing generation parameters." />

      <div className="picker">
        <div>
          <div className="picker-title">Compare at concurrency</div>
          <div className="picker-sub">{level === "5" ? "This is the selected operating point: balanced throughput and tail latency." : "Pick 5 to see the operating point that was selected."}</div>
        </div>
        <div className="seg" role="tablist" aria-label="Concurrency level">
          {concurrency.levels.map((l) => (
            <button key={l} role="tab" aria-selected={level === l} className={level === l ? "on" : ""} onClick={() => setLevel(l)}>
              {l}{l === "5" && <i className="seg-dot" title="Selected operating point" />}
            </button>
          ))}
        </div>
      </div>

      <Panel title={`Head to head at concurrency ${level}`} subtitle="Updates when you change the level above">
        <CompareTable cols={[OA, AN]} edge rows={atLevel} />
      </Panel>

      <div className="grid-2">
        <Panel title="Throughput" subtitle="Requests per second, higher is better" right={<Key items={[{ label: "OpenAI", tone: "openai" }, { label: "Anthropic", tone: "anthropic" }]} />}>
          <div className="chart">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trend} margin={{ top: 16, right: 14, left: -14, bottom: 0 }}>
                <CartesianGrid {...gridProps} />
                <XAxis dataKey="level" {...axisProps} tickFormatter={(v) => `C${v}`} />
                <YAxis {...axisProps} axisLine={false} />
                {lineTip((v) => `${v.toFixed(2)} req/s`)}
                <ReferenceLine x={level} stroke="#4a4a4a" strokeDasharray="3 3" />
                <Line type="monotone" dataKey="OpenAI" stroke={OPENAI} strokeWidth={2.5} dot={{ r: 4, fill: "#000", stroke: OPENAI, strokeWidth: 2 }} activeDot={{ r: 6 }} animationDuration={900} />
                <Line type="monotone" dataKey="Anthropic" stroke={ANTHROPIC} strokeWidth={2.5} dot={{ r: 4, fill: "#000", stroke: ANTHROPIC, strokeWidth: 2 }} activeDot={{ r: 6 }} animationDuration={900} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Panel>
        <Panel title="Tail latency (P99)" subtitle="Seconds, lower is better" right={<Key items={[{ label: "OpenAI", tone: "openai" }, { label: "Anthropic", tone: "anthropic" }]} />}>
          <div className="chart">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trend} margin={{ top: 16, right: 14, left: -14, bottom: 0 }}>
                <CartesianGrid {...gridProps} />
                <XAxis dataKey="level" {...axisProps} tickFormatter={(v) => `C${v}`} />
                <YAxis {...axisProps} axisLine={false} tickFormatter={(v) => `${v}s`} />
                {lineTip(sec2)}
                <ReferenceLine x={level} stroke="#4a4a4a" strokeDasharray="3 3" />
                <Line type="monotone" name="OpenAI" dataKey="OpenAIp99" stroke={OPENAI} strokeWidth={2.5} dot={{ r: 4, fill: "#000", stroke: OPENAI, strokeWidth: 2 }} activeDot={{ r: 6 }} animationDuration={900} />
                <Line type="monotone" name="Anthropic" dataKey="Anthropicp99" stroke={ANTHROPIC} strokeWidth={2.5} dot={{ r: 4, fill: "#000", stroke: ANTHROPIC, strokeWidth: 2 }} activeDot={{ r: 6 }} animationDuration={900} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      </div>

      <Panel title="Full concurrency matrix" subtitle="Every level, grouped by metric">
        <CompareTable cols={[OA, AN]} edge rows={matrix} />
      </Panel>
    </>
  );
}

/* ================================================================== */
/* Model comparison (GPT-5.6 vs GPT-6, both OpenAI)                    */
/* ================================================================== */

const G56: Col = { label: "GPT-5.6", tone: "openai", ghost: true };
const G6: Col = { label: "GPT-6", tone: "openai" };

export function Models() {
  const q = (label: string, a: number, b: number): Row => ({ group: "Quality", label, vals: [a, b], fmt: pct, better: "higher" });
  const rows: Row[] = [
    { group: "Latency", label: "Average latency", vals: [2.3335, 3.3485], fmt: sec4, better: "lower" },
    { group: "Latency", label: "P50", vals: [2.0024, 3.0684], fmt: sec4, better: "lower" },
    { group: "Latency", label: "P95", vals: [3.4796, 5.0854], fmt: sec4, better: "lower" },
    { group: "Latency", label: "P99", vals: [9.0354, 8.2999], fmt: sec4, better: "lower" },
    { group: "Tokens and cost", label: "Input tokens", vals: [365293, 365293], fmt: int, better: "lower" },
    { group: "Tokens and cost", label: "Output tokens", vals: [29046, 58233], fmt: int, better: "lower" },
    { group: "Tokens and cost", label: "Total cost", vals: [0.1079138, 0.0656458], fmt: usd8, better: "lower" },
    { group: "Reliability", label: "Schema validity", vals: [100, 99], fmt: pct, better: "higher" },
    ...modelQuality.map((m) => q(m.metric, m.gpt56, m.gpt6)),
  ];
  return (
    <>
      <Intro n="03" title="Cost vs quality vs latency." text="GPT-5.6 Luna and GPT-6 Luna were run independently on the same 300-request workload." />
      <StatStrip
        items={[
          { label: "GPT-6 cost", value: "−39%", detail: "$0.065646 total", icon: Zap, tone: "openai" },
          { label: "GPT-6 latency", value: "+43.5%", detail: "3.3485s average", icon: Activity, tone: "openai" },
          { label: "Category F1", value: "89.70%", detail: "GPT-6 vs 87.24% for GPT-5.6", icon: BarChart3, tone: "openai" },
          { label: "Forbidden claims", value: "0%", detail: "GPT-6 on 100 cases", icon: Layers3, tone: "openai" },
        ]}
      />
      <div className="grid-2">
        <Panel title="Quality metrics" subtitle="100-case golden dataset, higher is better" right={<Key items={[{ label: "GPT-5.6", tone: "openai", ghost: true }, { label: "GPT-6", tone: "openai" }]} />}>
          <div className="chart tall">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={modelQuality} margin={{ top: 8, right: 8, left: -14, bottom: 0 }} barGap={3}>
                <CartesianGrid {...gridProps} />
                <XAxis dataKey="metric" {...axisProps} tick={{ fill: "#8c8c8c", fontSize: 11 }} interval={0} angle={-30} textAnchor="end" height={56} />
                <YAxis {...axisProps} axisLine={false} domain={[0, 100]} />
                <Tooltip cursor={cursorProps} content={<ChartTip fmt={pct} ghostKeys={["gpt56"]} />} />
                <Bar dataKey="gpt56" name="GPT-5.6" fill={fillFor("openai", true)} stroke={OPENAI} strokeWidth={1} radius={[4, 4, 0, 0]} {...barAnim} />
                <Bar dataKey="gpt6" name="GPT-6" fill={OPENAI} radius={[4, 4, 0, 0]} {...barAnim} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>
        <Panel title="Latency percentiles" subtitle="GPT-6 is slower almost everywhere, except the P99 tail">
          <Dumbbell
            cols={[G56, G6]}
            max={10}
            ticks={[0, 2, 4, 6, 8, 10]}
            fmt={(n) => `${n % 1 === 0 ? n : n.toFixed(2)}s`}
            rows={[
              { label: "Average", a: 2.3335, b: 3.3485 },
              { label: "P50", a: 2.0024, b: 3.0684 },
              { label: "P95", a: 3.4796, b: 5.0854 },
              { label: "P99", a: 9.0354, b: 8.2999 },
            ]}
          />
        </Panel>
      </div>
      <Panel title="Every metric, side by side" subtitle="The check marks the better model for each row">
        <CompareTable cols={[G56, G6]} edge rows={rows} />
      </Panel>
      <Panel title="Decision" className="decision-card">
        <div className="decision-grid">
          <div>
            <span className="tag"><Swatch tone="openai" />Cost-efficient</span>
            <h3>GPT-6 Luna</h3>
            <p>About 39% cheaper, higher category F1, slightly higher fact recall, and a 0% forbidden-claim rate.</p>
          </div>
          <div>
            <span className="tag"><Swatch tone="openai" ghost />Latency-sensitive</span>
            <h3>GPT-5.6 Luna</h3>
            <p>Substantially faster, perfect parsing, and stronger urgency metrics.</p>
          </div>
        </div>
      </Panel>
    </>
  );
}

/* ================================================================== */
/* Prompt optimization                                                 */
/* ================================================================== */

export function Prompt() {
  const P: Col[] = [
    { label: "V1", tone: "openai", ghost: true },
    { label: "V2", tone: "openai" },
    { label: "V1", tone: "anthropic", ghost: true },
    { label: "V2", tone: "anthropic" },
  ];
  const r = (group: string, label: string, vals: (number | null)[], fmt: (n: number) => string, better: "lower" | "higher"): Row => ({ group, label, vals, fmt, better });
  const rows: Row[] = [
    r("Latency", "Average latency", [1.8198, 2.441, 2.1837, 2.7975], sec4, "lower"),
    r("Latency", "P95 latency", [2.5003, 3.2986, 2.9269, 3.1757], sec4, "lower"),
    r("Latency", "P99 latency", [2.9376, 6.2628, 3.5621, 3.3878], sec4, "lower"),
    r("Tokens and cost", "Input tokens", [365293, 210193, 473989, 298489], int, "lower"),
    r("Tokens and cost", "Output tokens", [28725, 33720, 35458, 32360], int, "lower"),
    r("Tokens and cost", "Total cost", [0.1075286, 0.0825026, 0.651279, 0.460289], usd8, "lower"),
    r("Reliability", "Schema validity", [100, 100, null, 100], pct, "higher"),
  ];
  return (
    <>
      <Intro n="04" title="Less instruction. Lower cost." text="V1 was already established by the baseline. V2 was tested on the same 300-request workload with the cache disabled." />
      <StatStrip
        items={[
          { label: "Static instruction reduction", value: "46.63%", detail: "1,126 → 601 tokens", icon: Layers3 },
          { label: "OpenAI input tokens", value: "−42.46%", detail: "365,293 → 210,193", icon: BarChart3, tone: "openai" },
          { label: "OpenAI cost", value: "−23.27%", detail: "$0.107529 → $0.082503", icon: Zap, tone: "openai" },
          { label: "Anthropic cost", value: "−29.33%", detail: "$0.651279 → $0.460289", icon: Zap, tone: "anthropic" },
        ]}
      />
      <div className="grid-2">
        <Panel title="Prompt size" subtitle="Estimated static instruction tokens" right={<Key items={[{ label: "V1", neutral: true, ghost: true }, { label: "V2", neutral: true }]} />}>
          <div className="size-bars">
            <div className="size-row"><span>V1</span><div className="size-track"><i data-ghost="1" style={{ width: "100%" }} /></div><strong>1,126</strong></div>
            <div className="size-row"><span>V2</span><div className="size-track"><i data-ghost="0" style={{ width: "53.37%" }} /></div><strong>601</strong></div>
          </div>
          <div className="size-big">−46.63%<span>shorter static instructions</span></div>
          <div className="size-note">Policy text 810 → 492 tokens. Prompt text 316 → 109 tokens.</div>
        </Panel>
        <Panel title="OpenAI quality" subtitle="100-case golden dataset, higher is better" right={<Key items={[{ label: "V1", tone: "openai", ghost: true }, { label: "V2", tone: "openai" }]} />}>
          <div className="chart">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={promptQuality} margin={{ top: 8, right: 8, left: -14, bottom: 0 }} barGap={3}>
                <CartesianGrid {...gridProps} />
                <XAxis dataKey="metric" {...axisProps} tick={{ fill: "#8c8c8c", fontSize: 11 }} interval={0} angle={-30} textAnchor="end" height={56} />
                <YAxis {...axisProps} axisLine={false} domain={[0, 100]} />
                <Tooltip cursor={cursorProps} content={<ChartTip fmt={pct} ghostKeys={["v1"]} />} />
                <Bar dataKey="v1" name="V1" fill={fillFor("openai", true)} stroke={OPENAI} strokeWidth={1} radius={[4, 4, 0, 0]} {...barAnim} />
                <Bar dataKey="v2" name="V2" fill={OPENAI} radius={[4, 4, 0, 0]} {...barAnim} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      </div>
      <Panel title="V1 to V2, by provider" subtitle="Each provider is scored against its own V1. Percentages show the change.">
        <CompareTable
          cols={P}
          heads={[
            { label: "OpenAI", span: 2, tone: "openai" },
            { label: "Anthropic", span: 2, tone: "anthropic" },
          ]}
          pairs={[
            { cols: [0, 1], title: "OpenAI: V1 vs V2" },
            { cols: [2, 3], title: "Anthropic: V1 vs V2" },
          ]}
          delta
          rows={rows}
        />
      </Panel>
      <Panel title="Prompt optimization decision" className="decision-card">
        <p className="lead">V2 is selected for cost-efficiency experiments. It reduced token usage and cost for both providers, but average latency increased.</p>
        <div className="decision-grid">
          <div>
            <span className="tag"><Swatch tone="openai" />OpenAI V2</span>
            <h3>Better category quality</h3>
            <p>Category accuracy 90% → 92%. Category F1 87.24% → 90.54%. Fact recall also improved and the forbidden-claim rate reached 0%.</p>
          </div>
          <div>
            <span className="tag"><Swatch neutral />Trade-off</span>
            <h3>Latency increased</h3>
            <p>Average latency rose for both providers, so fewer tokens do not automatically mean a faster response.</p>
          </div>
        </div>
      </Panel>
    </>
  );
}

export type { Tone };
