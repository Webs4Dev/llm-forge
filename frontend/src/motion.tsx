import { useEffect, useMemo, useRef, useState } from "react";
import type { CSSProperties, ReactNode, RefObject } from "react";
import { ChevronDown, Play, RotateCcw } from "lucide-react";
import type { Tone } from "./data";
import { concurrency } from "./data";
import { anthropicBaseline, anthropicTrace, openaiBaseline, openaiTrace } from "./traces";
import { Swatch } from "./ui";

/* ------------------------------------------------------------------ */
/* Helpers                                                             */
/* ------------------------------------------------------------------ */

export const reduceMotion = () =>
  typeof window !== "undefined" && !!window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

/** True once the element has been on screen (stays true). */
export function useInView<T extends Element>(threshold = 0.35) {
  const ref = useRef<T>(null);
  const [seen, setSeen] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el || seen) return;
    if (typeof IntersectionObserver === "undefined") { setSeen(true); return; }
    const io = new IntersectionObserver(([e]) => { if (e.isIntersecting) { setSeen(true); io.disconnect(); } }, { threshold });
    io.observe(el);
    return () => io.disconnect();
  }, [seen, threshold]);
  return [ref, seen] as const;
}

/** Plays 0 → 1 over `ms` once `active`; restarts when `key` changes. */
function useProgress(active: boolean, ms: number, key: unknown) {
  const [p, setP] = useState(0);
  useEffect(() => {
    if (!active) return;
    if (reduceMotion()) { setP(1); return; }
    setP(0);
    let raf = 0;
    const t0 = performance.now();
    const tick = (now: number) => {
      const x = Math.min(1, (now - t0) / ms);
      setP(x);
      if (x < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [active, ms, key]);
  return p;
}

function ToneSeg({ tone, set }: { tone: Tone; set: (t: Tone) => void }) {
  return (
    <div className="seg" role="tablist" aria-label="Provider">
      {(["openai", "anthropic"] as Tone[]).map((t) => (
        <button key={t} role="tab" aria-selected={tone === t} className={tone === t ? "on" : ""} data-tone={t} onClick={() => set(t)}>
          <Swatch tone={t} />{t === "openai" ? "OpenAI" : "Anthropic"}
        </button>
      ))}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Cache replay: all 300 requests in their recorded order              */
/* ------------------------------------------------------------------ */

const BASE_AVG = { openai: 1.8198, anthropic: 2.1837 };
const PLAY_MS = 9000;

export function CacheReplay() {
  const [tone, setTone] = useState<Tone>("openai");
  const [run, setRun] = useState(0);
  const [hover, setHover] = useState<number | null>(null);
  const [ref, seen] = useInView<HTMLDivElement>(0.3);
  const trace = tone === "openai" ? openaiTrace : anthropicTrace;

  // cumulative recorded time at which each request finishes
  const ends = useMemo(() => {
    let t = 0;
    return trace.map(([, , ms]) => (t += ms / 1000));
  }, [trace]);
  const total = ends[ends.length - 1];

  const p = useProgress(seen, PLAY_MS, `${tone}-${run}`);
  const now = p * total;
  // number of finished requests (binary search on ends)
  let lo = 0, hi = ends.length;
  while (lo < hi) { const m = (lo + hi) >> 1; if (ends[m] <= now) lo = m + 1; else hi = m; }
  const done = p >= 1 ? 300 : lo;

  let hits = 0;
  for (let i = 0; i < done; i++) hits += trace[i][1];
  const calls = done - hits;
  const without = done * BASE_AVG[tone];
  const fin = done === 300;
  const hoverInfo = hover !== null ? trace[hover] : null;

  return (
    <div className="replay" ref={ref} data-tone={tone}>
      <div className="replay-top">
        <ToneSeg tone={tone} set={(t) => { setTone(t); setRun((r) => r + 1); }} />
        <button className="ghost-btn" onClick={() => setRun((r) => r + 1)} aria-label="Replay the 300 requests">
          {fin ? <RotateCcw size={14} /> : <Play size={14} />}Replay
        </button>
      </div>

      <div className="replay-body">
        <div className="cells" role="img" aria-label={`${hits} cache hits and ${calls} LLM calls out of ${done} requests`} onMouseLeave={() => setHover(null)}>
          {trace.map(([caseNo, hit], i) => {
            const state = i < done ? (hit ? "hit" : "miss") : i === done ? "live" : "wait";
            const same = hover !== null && trace[hover][0] === caseNo;
            return (
              <i
                key={i}
                className={`cell-r ${state} ${same ? "same" : ""}`}
                onMouseEnter={() => setHover(i)}
              />
            );
          })}
        </div>

        <div className="replay-side">
          <div className="clock">
            <span>With cache</span>
            <b>{(Math.min(now, total)).toFixed(1)}s</b>
          </div>
          <div className="clock ghost">
            <span>Without cache</span>
            <b>{without.toFixed(1)}s</b>
          </div>
          <div className="counts">
            <div><i className="cell-r miss" /><span>LLM calls</span><b>{calls}</b></div>
            <div><i className="cell-r hit" /><span>Cache hits</span><b>{hits}</b></div>
          </div>
          <p className="replay-hint" aria-live="polite">
            {hoverInfo
              ? <>Request {hover! + 1} · ticket T{String(hoverInfo[0]).padStart(3, "0")} · {hoverInfo[1] ? "cache hit" : "LLM call"} · {hoverInfo[2] < 10 ? `${hoverInfo[2]}ms` : `${(hoverInfo[2] / 1000).toFixed(2)}s`}</>
              : fin
                ? <>Done: {(without / total).toFixed(1)}× less waiting. Hover a cell to see the same ticket's other visits.</>
                : <>Each square is one request, in the order the workload sent them.</>}
          </p>
        </div>
      </div>
      <p className="fine">Recorded trace from the exact-cache run, replayed about {Math.round(total / (PLAY_MS / 1000))}× faster than real time. The "without cache" clock uses the baseline average of {BASE_AVG[tone]}s per request.</p>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Concurrency: N workers draining the same 300 requests               */
/* ------------------------------------------------------------------ */

type Block = { lane: number; start: number; end: number };

function schedule(lat: number[], n: number, target: number): Block[] {
  // A thread pool: each request goes to whichever worker frees up first.
  const free = new Array(n).fill(0);
  const raw: Block[] = lat.map((ms) => {
    let lane = 0;
    for (let k = 1; k < n; k++) if (free[k] < free[lane]) lane = k;
    const start = free[lane];
    free[lane] = start + ms / 1000;
    return { lane, start, end: free[lane] };
  });
  // Scale the shape so the run ends at the recorded total time.
  const s = target / Math.max(...free);
  return raw.map((b) => ({ lane: b.lane, start: b.start * s, end: b.end * s }));
}

const SWEEP_MS = 6000;

export function WorkerLanes({ level }: { level: string }) {
  const [tone, setTone] = useState<Tone>("openai");
  const [run, setRun] = useState(0);
  const [ref, seen] = useInView<HTMLDivElement>(0.3);
  const n = Number(level);
  const li = concurrency.levels.indexOf(level);
  const data = tone === "openai" ? concurrency.OpenAI : concurrency.Anthropic;
  const axis = Math.max(...concurrency.OpenAI.time, ...concurrency.Anthropic.time);
  const target = data.time[li];
  const blocks = useMemo(() => schedule(tone === "openai" ? openaiBaseline : anthropicBaseline, n, target), [tone, n, target]);

  const p = useProgress(seen, SWEEP_MS, `${tone}-${level}-${run}`);
  const t = p * axis;
  const fin = t >= target;
  const shown = Math.min(t, target);
  const doneCount = fin ? 300 : blocks.filter((b) => b.end <= t).length;

  return (
    <div className="lanes" ref={ref} data-tone={tone} style={{ "--play": `${(shown / axis) * 100}%` } as CSSProperties}>
      <div className="replay-top">
        <ToneSeg tone={tone} set={(x) => { setTone(x); setRun((r) => r + 1); }} />
        <div className="lanes-read" aria-live="polite">
          <span><b>{doneCount}</b>/300 done</span>
          <span><b>{shown.toFixed(0)}s</b>{fin ? " total" : " elapsed"}</span>
          <button className="ghost-btn" onClick={() => setRun((r) => r + 1)} aria-label="Replay workers">
            {fin ? <RotateCcw size={14} /> : <Play size={14} />}Replay
          </button>
        </div>
      </div>

      <div className="lanes-grid" data-n={n}>
        {Array.from({ length: n }, (_, k) => (
          <div className="worker" key={k}>
            <span className="worker-n">W{k + 1}</span>
            <div className="worker-track">
              <div className="worker-fill">
                <b className="busy" style={{ width: `${(Math.max(...blocks.filter((b) => b.lane === k).map((b) => b.end)) / axis) * 100}%` }} />
                {blocks.filter((b) => b.lane === k).map((b, j) => (
                  <i key={j} style={{ left: `${(b.start / axis) * 100}%`, width: `${((b.end - b.start) / axis) * 100}%` }} />
                ))}
              </div>
            </div>
          </div>
        ))}
        <div className="lanes-axis" aria-hidden="true">
          {[0, 0.25, 0.5, 0.75, 1].map((f) => <em key={f} style={{ left: `${f * 100}%` }}>{Math.round(f * axis)}s</em>)}
          <b className="lanes-head" />
          <b className="lanes-c1" style={{ left: `${(data.time[0] / axis) * 100}%` }}><span>1 worker</span></b>
        </div>
      </div>

      <p className="fine">
        {fin
          ? <>{n} worker{n > 1 ? "s" : ""} finished in {target.toFixed(1)}s, {(data.time[0] / target).toFixed(1)}× sooner than one worker, at {data.throughput[li]} req/s.</>
          : <>Each block is one request. Same work, spread over {n} worker{n > 1 ? "s" : ""}.</>}
        {" "}Total times are recorded. The block pattern is modeled from baseline per-request latencies.
      </p>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Prompt token tape: one square = 10 tokens                           */
/* ------------------------------------------------------------------ */

const TAPE = [
  { name: "Policy", v1: 810, v2: 492 },
  { name: "Prompt", v1: 316, v2: 109 },
];

/** Which of the V1 squares survive into V2, spread evenly so the cut reads as trimming, not truncation. */
function keepMask(n1: number, n2: number) {
  const keep = new Array(n1).fill(false);
  for (let k = 0; k < n2; k++) keep[Math.floor((k * n1) / n2)] = true;
  return keep;
}

export function TokenTape() {
  const [v2, setV2] = useState(false);
  const [ref, seen] = useInView<HTMLDivElement>(0.4);
  useEffect(() => {
    if (!seen) return;
    if (reduceMotion()) { setV2(true); return; }
    const id = setTimeout(() => setV2(true), 700);
    return () => clearTimeout(id);
  }, [seen]);

  const total = v2 ? 601 : 1126;
  return (
    <div className="tape" ref={ref}>
      <div className="replay-top">
        <div className="seg" role="tablist" aria-label="Prompt version">
          {[false, true].map((x) => (
            <button key={String(x)} role="tab" aria-selected={v2 === x} className={v2 === x ? "on" : ""} onClick={() => setV2(x)}>
              {x ? "V2" : "V1"}
            </button>
          ))}
        </div>
        <div className="tape-total"><b>{total.toLocaleString("en-US")}</b> tokens</div>
      </div>
      {TAPE.map((row) => {
        const n1 = Math.round(row.v1 / 10);
        const mask = keepMask(n1, Math.round(row.v2 / 10));
        return (
          <div className="tape-row" key={row.name}>
            <div className="tape-label"><span>{row.name}</span><b>{v2 ? row.v2 : row.v1}</b></div>
            <div className="tape-cells" aria-label={`${row.name}: ${row.v1} tokens in V1, ${row.v2} in V2`}>
              {mask.map((keep, i) => (
                <i key={i} className={!keep && v2 ? "gone" : keep ? "" : "cut"} style={{ transitionDelay: `${(i % 40) * 12}ms` }} />
              ))}
            </div>
          </div>
        );
      })}
      <p className="fine">One square is 10 static instruction tokens. Hatched squares are the ones V2 removes.</p>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Fold: hide long tables behind a button                              */
/* ------------------------------------------------------------------ */

export function Fold({ label, children }: { label: string; children: ReactNode }) {
  const [open, setOpen] = useState(false);
  return (
    <div className={`fold ${open ? "open" : ""}`}>
      <button className="ghost-btn fold-btn" aria-expanded={open} onClick={() => setOpen(!open)}>
        <ChevronDown size={15} />{open ? "Hide" : label}
      </button>
      <div className="fold-body"><div>{open && children}</div></div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Scroll reveal for page sections                                     */
/* ------------------------------------------------------------------ */

/** Adds `.in` to each direct child of `root` as it scrolls into view. */
export function useReveal(root: RefObject<HTMLElement>, key: unknown) {
  useEffect(() => {
    const el = root.current;
    if (!el) return;
    const kids = Array.from(el.children) as HTMLElement[];
    if (reduceMotion() || typeof IntersectionObserver === "undefined") {
      kids.forEach((k) => k.classList.add("in"));
      return;
    }
    kids.forEach((k) => k.classList.add("rv"));
    const io = new IntersectionObserver(
      (es) => es.forEach((e) => { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } }),
      { threshold: 0.08, rootMargin: "0px 0px -6% 0px" }
    );
    kids.forEach((k) => io.observe(k));
    return () => io.disconnect();
  }, [root, key]);
}
