import { useEffect, useState } from "react";
import {
  Activity,
  BrainCircuit,
  Database,
  Gauge,
  Layers3,
  Menu,
  Network,
  PanelLeftClose,
  PanelLeftOpen,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Baseline, Cache, Concurrency, Models, Overview, Prompt } from "./pages";
import type { Section } from "./pages";
import { Key, SvgDefs } from "./ui";

const navItems: { id: Section; label: string; icon: LucideIcon; number?: string }[] = [
  { id: "overview", label: "Overview", icon: Gauge },
  { id: "baseline", label: "Baseline", icon: Activity, number: "00" },
  { id: "cache", label: "Exact cache", icon: Database, number: "01" },
  { id: "concurrency", label: "Concurrency", icon: Network, number: "02" },
  { id: "models", label: "Model comparison", icon: BrainCircuit, number: "03" },
  { id: "prompt", label: "Prompt optimization", icon: Layers3, number: "04" },
];

const ids = navItems.map((n) => n.id);
const fromHash = (): Section => {
  const h = window.location.hash.replace("#", "") as Section;
  return ids.includes(h) ? h : "overview";
};

export default function App() {
  const [section, setSection] = useState<Section>(fromHash);
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const onHash = () => setSection(fromHash());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  const go = (s: Section) => {
    window.location.hash = s === "overview" ? "" : s;
    setSection(s);
    setMobileOpen(false);
    window.scrollTo({ top: 0 });
  };

  const title = navItems.find((x) => x.id === section)?.label ?? "Overview";

  const content = {
    overview: <Overview go={go} />,
    baseline: <Baseline />,
    cache: <Cache />,
    concurrency: <Concurrency />,
    models: <Models />,
    prompt: <Prompt />,
  }[section];

  return (
    <div className={`app ${collapsed ? "sidebar-collapsed" : ""}`}>
      <SvgDefs />
      <aside className={`sidebar ${mobileOpen ? "mobile-open" : ""}`}>
        <div className="brand">
          <div className="brand-mark" aria-hidden="true"><span>L</span><i /></div>
          {!collapsed && <div><strong>LLMForge</strong><small>Experiment lab</small></div>}
          <button className="collapse" onClick={() => setCollapsed(!collapsed)} aria-label="Collapse sidebar">
            {collapsed ? <PanelLeftOpen size={18} /> : <PanelLeftClose size={18} />}
          </button>
        </div>
        <nav aria-label="Experiments">
          {navItems.map(({ id, label, icon: Icon, number }) => (
            <button key={id} className={section === id ? "active" : ""} onClick={() => go(id)} title={label}>
              <Icon size={18} />
              {!collapsed && <><span>{label}</span>{number && <em>{number}</em>}</>}
            </button>
          ))}
        </nav>
        {!collapsed && (
          <div className="sidebar-footer">
            <strong>Scope locked</strong>
            <span>No RAG, no agents</span>
          </div>
        )}
      </aside>
      {mobileOpen && <div className="scrim" onClick={() => setMobileOpen(false)} />}

      <main className="main">
        <header className="topbar">
          <button className="mobile-menu" onClick={() => setMobileOpen(!mobileOpen)} aria-label="Open menu"><Menu size={20} /></button>
          <h1>{title}</h1>
          <div className="topbar-right">
            <Key items={[{ label: "OpenAI", tone: "openai" }, { label: "Anthropic", tone: "anthropic" }]} />
            <div className="status-pill"><span className="status-dot" />Experiments recorded</div>
          </div>
        </header>
        <div className="content" key={section}>{content}</div>
        <footer>LLMForge results dashboard. Values are the recorded experiments in RESULTS.md.</footer>
      </main>
    </div>
  );
}
