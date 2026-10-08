import { useEffect, useMemo, useRef, useState } from "react";
import type { CSSProperties, ReactNode } from "react";
import { ArrowDown, ArrowUp, Check, Play, RotateCcw } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { Tone } from "./data";
import { raceStages } from "./data";

/* ------------------------------------------------------------------ */
/* Shared bits                                                         */
/* ------------------------------------------------------------------ */

export type Col = { label: string; sub?: string; tone: Tone; ghost?: boolean };

export const OPENAI = "#FFFFFF";
export const ANTHROPIC = "#FF7B1C";
export const toneColor = (t: Tone) => (t === "openai" ? OPENAI : ANTHROPIC);
export const fillFor = (t: Tone, ghost = false) =>
  ghost ? `url(#hatch-${t})` : toneColor(t);

const reduceMotion = () =>
  typeof window !== "undefined" && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

/** Hatch patterns used by every chart for "before / old version" bars. */
export function SvgDefs() {
  return (
    <svg width="0" height="0" style={{ position: "absolute" }} aria-hidden="true" focusable="false">
      <defs>
        {(["openai", "anthropic"] as Tone[]).map((t) => (
          <pattern key={t} id={`hatch-${t}`} width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
            <rect width="6" height="6" fill={toneColor(t)} fillOpacity="0.1" />
            <rect width="2.4" height="6" fill={toneColor(t)} />
          </pattern>
        ))}
        <pattern id="hatch-neutral" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
          <rect width="6" height="6" fill="#9a9a9a" fillOpacity="0.1" />
          <rect width="2.4" height="6" fill="#9a9a9a" />
        </pattern>
      </defs>
    </svg>
  );
}

export function Swatch({ tone, ghost = false, neutral = false }: { tone?: Tone; ghost?: boolean; neutral?: boolean }) {
  return <i className="sw" data-tone={neutral ? "neutral" : tone} data-ghost={ghost ? "1" : "0"} />;
}

export function Key({ items }: { items: { label: string; tone?: Tone; ghost?: boolean; neutral?: boolean }[] }) {
  return (
    <div className="key">
      {items.map((i) => (
        <span key={i.label}>
          <Swatch tone={i.tone} ghost={i.ghost} neutral={i.neutral} />
          {i.label}
        </span>
      ))}
    </div>
  );
}

/** Counts a number up from zero while keeping its prefix, suffix and decimals. */
export function AnimatedValue({ value }: { value: string }) {
  const m = value.match(/(\d[\d,]*\.?\d*)/);
  const [t, setT] = useState(reduceMotion() || !m ? 1 : 0);
  useEffect(() => {
    if (reduceMotion() || !m) return;
    let raf = 0;
    const start = performance.now();
    const tick = (now: number) => {
      const p = Math.min(1, (now - start) / 900);
      setT(1 - Math.pow(1 - p, 3));
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);
  if (!m) return <>{value}</>;
  const raw = m[1];
  const decimals = raw.includes(".") ? raw.split(".")[1].length : 0;
  const target = parseFloat(raw.replace(/,/g, ""));
  let shown = (target * t).toFixed(decimals);
  if (raw.includes(",")) shown = Number(shown).toLocaleString("en-US", { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
  const idx = m.index ?? 0;
  return <>{value.slice(0, idx)}{shown}{value.slice(idx + raw.length)}</>;
}

export function Panel({ title, subtitle, right, children, className = "" }: { title: string; subtitle?: string; right?: ReactNode; children: ReactNode; className?: string }) {
  return (
    <section className={`panel ${className}`}>
      <div className="panel-head">
        <div>
          <h3>{title}</h3>
          {subtitle && <p>{subtitle}</p>}
        </div>
        {right}
      </div>
      {children}
    </section>
  );
}

export type Stat = { label: string; value: string; detail: string; icon: LucideIcon; tone?: Tone };

export function StatStrip({ items }: { items: Stat[] }) {
  return (
    <div className="strip">
      {items.map(({ label, value, detail, icon: Icon, tone }) => (
        <div className="stat" key={label} data-tone={tone ?? "none"}>
          <div className="stat-label"><Icon size={15} />{label}</div>
          <div className="stat-value"><AnimatedValue value={value} /></div>
          <div className="stat-detail">{tone && <Swatch tone={tone} />}{detail}</div>
        </div>
      ))}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Chart tooltip (black, themed)                                       */
/* ------------------------------------------------------------------ */

type TipItem = { name?: string; value?: number | string; dataKey?: string; color?: string; payload?: Record<string, unknown> };

export function ChartTip({
  active,
  payload,
  label,
  fmt = (v: number) => String(v),
  ghostKeys = [],
  toneByName,
}: {
  active?: boolean;
  payload?: TipItem[];
  label?: string | number;
  fmt?: (v: number) => string;
  ghostKeys?: string[];
  toneByName?: Record<string, Tone>;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="tip">
      {label !== undefined && <div className="tip-title">{label}</div>}
      {payload.map((p, i) => {
        const tone = (p.payload?.tone as Tone | undefined) ?? toneByName?.[String(p.name)] ?? (p.color === ANTHROPIC ? "anthropic" : "openai");
        const ghost = ghostKeys.includes(String(p.dataKey));
        return (
          <div className="tip-row" key={i}>
            <Swatch tone={tone} ghost={ghost} />
            <span>{p.name}</span>
            <b>{typeof p.value === "number" ? fmt(p.value) : p.value}</b>
          </div>
        );
      })}
    </div>
  );
}

export const axisProps = {
  stroke: "#2a2a2a",
  tick: { fill: "#8c8c8c", fontSize: 12 },
  tickLine: false,
} as const;

export const gridProps = { stroke: "#1a1a1a", strokeDasharray: "2 4", vertical: false } as const;
export const cursorProps = { fill: "rgba(255,255,255,0.045)" };

/* ------------------------------------------------------------------ */
/* Head-to-head table                                                  */
/* ------------------------------------------------------------------ */

export type Better = "lower" | "higher" | "none";
export type Row = {
  label: string;
  vals: (number | null)[];
  fmt: (n: number) => string;
  better: Better;
  group?: string;
  tag?: string;
};
export type Pair = { cols: [number, number]; title: string };

function ratioText(a: number, b: number) {
  const hi = Math.max(a, b);
  const lo = Math.min(a, b);
  if (lo === 0) return "";
  const r = hi / lo;
  return r >= 10 ? `${r.toFixed(0)}×` : `${r.toFixed(2)}×`;
}

function judge(row: Row, pair: Pair) {
  const [i, j] = pair.cols;
  const a = row.vals[i];
  const b = row.vals[j];
  if (a == null || b == null || row.better === "none") return { winner: null as number | null, comparable: false };
  if (a === b) return { winner: null, comparable: true };
  const aWins = row.better === "lower" ? a < b : a > b;
  return { winner: aWins ? i : j, comparable: true };
}

export function CompareTable({
  cols,
  heads,
  pairs,
  rows,
  edge = false,
  delta = false,
}: {
  cols: Col[];
  heads?: { label: string; span: number; tone: Tone }[];
  pairs?: Pair[];
  rows: Row[];
  edge?: boolean;
  delta?: boolean;
}) {
  const pr: Pair[] = pairs ?? [{ cols: [0, 1], title: `${cols[0].label} vs ${cols[1].label}` }];
  const [on, setOn] = useState(false);
  useEffect(() => {
    const id = requestAnimationFrame(() => setOn(true));
    return () => cancelAnimationFrame(id);
  }, []);

  const verdicts = useMemo(() => rows.map((r) => pr.map((p) => judge(r, p))), [rows, pr]);

  const scores = pr.map((p, pi) => {
    let wa = 0, wb = 0, ties = 0;
    rows.forEach((_, ri) => {
      const v = verdicts[ri][pi];
      if (!v.comparable) return;
      if (v.winner === null) ties++;
      else if (v.winner === p.cols[0]) wa++;
      else wb++;
    });
    return { wa, wb, ties };
  });

  const colspan = cols.length + 1 + (edge ? 1 : 0);
  let lastGroup: string | undefined;

  return (
    <div className="vs">
      <div className="score-wrap">
        {pr.map((p, pi) => {
          const a = cols[p.cols[0]];
          const b = cols[p.cols[1]];
          const s = scores[pi];
          return (
            <div className="score" key={p.title}>
              <div className="score-title">{p.title}</div>
              <div className="score-line">
                <span className="score-side"><Swatch tone={a.tone} ghost={a.ghost} />{a.label}<b>{s.wa}</b></span>
                <div className="score-bar" aria-hidden="true">
                  <i className="sa" data-tone={a.tone} data-ghost={a.ghost ? "1" : "0"} style={{ flexGrow: on ? s.wa : 0 }} />
                  <i className="st" style={{ flexGrow: on ? s.ties : 0 }} />
                  <i className="sb" data-tone={b.tone} data-ghost={b.ghost ? "1" : "0"} style={{ flexGrow: on ? s.wb : 0 }} />
                </div>
                <span className="score-side right"><b>{s.wb}</b>{b.label}<Swatch tone={b.tone} ghost={b.ghost} /></span>
              </div>
              <div className="score-note">
                {s.wa === s.wb ? "Even split" : `${s.wa > s.wb ? a.label : b.label} is better on ${Math.max(s.wa, s.wb)} of ${s.wa + s.wb + s.ties} metrics`}
                {s.ties > 0 && `, ${s.ties} tied`}
              </div>
            </div>
          );
        })}
      </div>

      <div className="table-legend">
        <span><i className="pip"><Check size={11} strokeWidth={3.5} /></i>Better side</span>
        <span><ArrowDown size={13} />Lower wins</span>
        <span><ArrowUp size={13} />Higher wins</span>
        <span>Bars show the size of each value</span>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            {heads && (
              <tr className="head-top">
                <th />
                {heads.map((h) => (
                  <th key={h.label} colSpan={h.span} className="head-group" data-tone={h.tone}>
                    <Swatch tone={h.tone} />{h.label}
                  </th>
                ))}
              </tr>
            )}
            <tr>
              <th>Metric</th>
              {cols.map((c) => (
                <th key={c.label + (c.sub ?? "")} className="col-head">
                  <Swatch tone={c.tone} ghost={c.ghost} />
                  {c.label}
                  {c.sub && <small>{c.sub}</small>}
                </th>
              ))}
              {edge && <th className="edge-head">Edge</th>}
            </tr>
          </thead>
          <tbody>
            {rows.map((r, ri) => {
              const out: ReactNode[] = [];
              if (r.group && r.group !== lastGroup) {
                lastGroup = r.group;
                out.push(
                  <tr className="grp" key={`g-${r.group}`}>
                    <th colSpan={colspan}>{r.group}</th>
                  </tr>
                );
              }
              const winners = new Set<number>();
              const maxByCol: number[] = [];
              pr.forEach((p, pi) => {
                const v = verdicts[ri][pi];
                if (v.winner !== null) winners.add(v.winner);
                const vals = p.cols.map((c) => r.vals[c]).filter((x): x is number => x != null);
                const mx = Math.max(...vals, 0);
                p.cols.forEach((c) => (maxByCol[c] = mx));
              });
              const firstVerdict = verdicts[ri][0];
              out.push(
                <tr key={r.label + ri} className={r.tag ? "is-tagged" : ""} style={{ "--i": ri } as CSSProperties}>
                  <th className="row-label" scope="row">
                    {r.better === "lower" && <ArrowDown size={13} className="dir" aria-label="Lower is better" />}
                    {r.better === "higher" && <ArrowUp size={13} className="dir" aria-label="Higher is better" />}
                    {r.label}
                    {r.tag && <span className="row-tag">{r.tag}</span>}
                  </th>
                  {cols.map((c, ci) => {
                    const v = r.vals[ci];
                    if (v == null) return <td key={ci} className="cell empty">—</td>;
                    const isWin = winners.has(ci);
                    const comparable = pr.some((p, pi) => p.cols.includes(ci as never) && verdicts[ri][pi].comparable);
                    const hasLoser = pr.some((p, pi) => p.cols.includes(ci as never) && verdicts[ri][pi].winner !== null && verdicts[ri][pi].winner !== ci);
                    const w = maxByCol[ci] ? Math.max(3, (v / maxByCol[ci]) * 100) : 0;
                    const pair = pr.find((p) => p.cols[1] === ci);
                    let d: string | null = null;
                    if (delta && pair) {
                      const base = r.vals[pair.cols[0]];
                      if (base != null && base !== 0 && v !== base) {
                        const pct = ((v - base) / base) * 100;
                        d = `${pct > 0 ? "+" : "−"}${Math.abs(pct).toFixed(1)}%`;
                      }
                    }
                    return (
                      <td
                        key={ci}
                        className={`cell ${isWin ? "win" : ""} ${hasLoser ? "lose" : ""} ${comparable && !isWin && !hasLoser ? "tie" : ""}`}
                        data-tone={c.tone}
                      >
                        <i className="bar" data-tone={c.tone} data-ghost={c.ghost ? "1" : "0"} style={{ "--w": `${w}%` } as CSSProperties} />
                        <span className="val">
                          {isWin && <i className="pip"><Check size={11} strokeWidth={3.5} /><span className="sr">better</span></i>}
                          {r.fmt(v)}
                        </span>
                        {d && <small className="delta">{d} vs V1</small>}
                      </td>
                    );
                  })}
                  {edge && (
                    <td className="edge">
                      {firstVerdict.winner !== null && r.vals[0] != null && r.vals[1] != null ? (
                        <>
                          <Swatch tone={cols[firstVerdict.winner].tone} ghost={cols[firstVerdict.winner].ghost} />
                          {cols[firstVerdict.winner].label}
                          <b>{ratioText(r.vals[0], r.vals[1])}</b>
                          {r.better === "lower" ? " lower" : " higher"}
                        </>
                      ) : firstVerdict.comparable ? (
                        <span className="muted">Tie</span>
                      ) : (
                        <span className="muted">—</span>
                      )}
                    </td>
                  )}
                </tr>
              );
              return out;
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Dumbbell: two dots per row on one shared scale                      */
/* ------------------------------------------------------------------ */

export function Dumbbell({
  cols,
  rows,
  max,
  ticks,
  fmt,
  unitNote,
}: {
  cols: [Col, Col];
  rows: { label: string; a: number; b: number }[];
  max: number;
  ticks: number[];
  fmt: (n: number) => string;
  unitNote?: string;
}) {
  const [on, setOn] = useState(false);
  useEffect(() => {
    const id = requestAnimationFrame(() => setOn(true));
    return () => cancelAnimationFrame(id);
  }, []);
  const pct = (v: number) => `${(v / max) * 100}%`;
  return (
    <div className="db">
      <div className="db-grid">
        {rows.map((r, i) => {
          const lo = Math.min(r.a, r.b);
          const hi = Math.max(r.a, r.b);
          const win = r.a === r.b ? null : r.a < r.b ? 0 : 1;
          const gap = hi - lo;
          return (
            <div className="db-row" key={r.label} style={{ "--i": i } as CSSProperties}>
              <div className="db-label">{r.label}</div>
              <div className="db-track">
                {ticks.map((t) => (
                  <span className="db-tick" key={t} style={{ left: pct(t) }}><em>{fmt(t)}</em></span>
                ))}
                <i className="db-link" style={{ left: on ? pct(lo) : "0%", width: on ? `${((hi - lo) / max) * 100}%` : "0%" }} />
                {[r.a, r.b].map((v, k) => (
                  <b
                    key={k}
                    tabIndex={0}
                    className={`db-dot ${k === 0 ? "up" : "down"} ${win === k ? "is-win" : ""}`}
                    data-tone={cols[k].tone}
                    data-ghost={cols[k].ghost ? "1" : "0"}
                    style={{ left: on ? pct(v) : "0%", transitionDelay: `${i * 70}ms` }}
                    aria-label={`${cols[k].label} ${r.label} ${fmt(v)}`}
                  >
                    <span className="db-val">{fmt(v)}</span>
                  </b>
                ))}
              </div>
              <div className="db-gap">
                {win !== null ? (
                  <>
                    <Swatch tone={cols[win].tone} ghost={cols[win].ghost} />
                    <span>{fmt(gap)} ahead</span>
                  </>
                ) : (
                  <span className="muted">Level</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
      <div className="db-foot">
        <Key items={[{ label: cols[0].label, tone: cols[0].tone, ghost: cols[0].ghost }, { label: cols[1].label, tone: cols[1].tone, ghost: cols[1].ghost }]} />
        <span>{unitNote ?? "Dots further left are faster"}</span>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Before / after savings                                              */
/* ------------------------------------------------------------------ */

export function Savings({
  items,
  fmt,
}: {
  items: { name: string; tone: Tone; before: number; after: number }[];
  fmt: (n: number) => string;
}) {
  const [on, setOn] = useState(false);
  useEffect(() => {
    const id = requestAnimationFrame(() => setOn(true));
    return () => cancelAnimationFrame(id);
  }, []);
  const max = Math.max(...items.map((i) => i.before));
  return (
    <div className="sav">
      {items.map((it) => {
        const drop = ((it.before - it.after) / it.before) * 100;
        return (
          <div className="sav-item" key={it.name}>
            <div className="sav-head">
              <span><Swatch tone={it.tone} />{it.name}</span>
              <strong>−{drop.toFixed(1)}%</strong>
            </div>
            <div className="sav-line">
              <small>Before</small>
              <div className="sav-track"><i data-tone={it.tone} data-ghost="1" style={{ width: on ? `${(it.before / max) * 100}%` : "0%" }} /></div>
              <b>{fmt(it.before)}</b>
            </div>
            <div className="sav-line">
              <small>After</small>
              <div className="sav-track"><i data-tone={it.tone} data-ghost="0" style={{ width: on ? `${(it.after / max) * 100}%` : "0%", transitionDelay: ".25s" }} /></div>
              <b>{fmt(it.after)}</b>
            </div>
          </div>
        );
      })}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Latency race: plays at real speed                                   */
/* ------------------------------------------------------------------ */

export function Race() {
  const [stage, setStage] = useState(0);
  const [run, setRun] = useState(0);
  const [t, setT] = useState(0);
  const s = raceStages[stage];
  const AXIS = 3;
  const longest = Math.max(s.openai, s.anthropic);
  const raf = useRef(0);

  useEffect(() => {
    if (reduceMotion()) {
      setT(longest);
      return;
    }
    setT(0);
    const t0 = performance.now() + 350;
    const tick = (now: number) => {
      const el = Math.max(0, (now - t0) / 1000);
      setT(Math.min(el, longest));
      if (el < longest) raf.current = requestAnimationFrame(tick);
    };
    raf.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf.current);
  }, [stage, run, longest]);

  const lanes: { name: string; tone: Tone; lat: number }[] = [
    { name: "OpenAI", tone: "openai", lat: s.openai },
    { name: "Anthropic", tone: "anthropic", lat: s.anthropic },
  ];
  const done = t >= longest;
  const faster = s.openai < s.anthropic ? lanes[0] : lanes[1];
  const gap = Math.abs(s.openai - s.anthropic);

  return (
    <div className="race">
      <div className="race-top">
        <div className="seg" role="tablist" aria-label="Experiment stage">
          {raceStages.map((x, i) => (
            <button key={x.id} role="tab" aria-selected={stage === i} className={stage === i ? "on" : ""} onClick={() => { setStage(i); setRun((r) => r + 1); }}>
              {x.label}
            </button>
          ))}
        </div>
        <button className="ghost-btn" onClick={() => setRun((r) => r + 1)} aria-label="Replay race">
          {done ? <RotateCcw size={14} /> : <Play size={14} />}Replay
        </button>
      </div>
      <p className="race-note">{s.note}. Average time for one request, played at real speed.</p>
      <div className="race-lanes">
        <div className="race-gridwrap" aria-hidden="true">
          {[0, 1, 2, 3].map((g) => (
            <span key={g} className="race-grid" style={{ left: `${(g / AXIS) * 100}%` }}><em>{g}s</em></span>
          ))}
        </div>
        {lanes.map((l) => {
          const v = Math.min(t, l.lat);
          const fin = t >= l.lat - 0.0001;
          const first = fin && l.lat === Math.min(s.openai, s.anthropic);
          return (
            <div className="lane" key={l.name}>
              <div className="lane-name"><Swatch tone={l.tone} />{l.name}</div>
              <div className="lane-track">
                <i className="lane-fill" data-tone={l.tone} style={{ width: `${(v / AXIS) * 100}%` }} />
                <b className="lane-head" data-tone={l.tone} style={{ left: `${(v / AXIS) * 100}%` }} />
              </div>
              <div className={`lane-time ${fin ? "fin" : ""}`}>
                {v.toFixed(2)}s
                {first && <i className="pip" data-tone={l.tone}><Check size={11} strokeWidth={3.5} /></i>}
              </div>
            </div>
          );
        })}
      </div>
      <div className={`race-result ${done ? "show" : ""}`}>
        <Swatch tone={faster.tone} />
        {faster.name} finishes {gap.toFixed(2)}s sooner
      </div>
    </div>
  );
}
