import { useEffect, useMemo, useRef, useState } from "react";
import "@/App.css";
import axios from "axios";
import { ShieldCheck, Flame, Radar, LockKeyhole, Building2, ArrowUpRight } from "lucide-react";
import { Toaster, toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const secureZone = { x: 47, y: 43, width: 7, height: 9 };
const secureLogLine = "[SECURE] NIST ML-KEM Session Active // Streaming Lattice Math...";
const alertLogLine = "[ALERT] Core Boundary Breach // Volatile RAM Purged";

const features = [
  {
    icon: Radar,
    title: "10cm UWB Spatial Gate",
    copy: "Simulated ultra-wideband coordinate checks bind session trust to a live physical perimeter.",
  },
  {
    icon: Flame,
    title: "Automated Key Burning",
    copy: "Volatile lattice keys are purged the instant a device drifts beyond the approved vault envelope.",
  },
  {
    icon: LockKeyhole,
    title: "Zero-Trust Containment",
    copy: "Every decrypt request is challenged by proximity, context, and perimeter state before access opens.",
  },
];

const telemetryRows = ["UWB-PULSE: 6.5GHz", "LATTICE: ML-KEM-768", "VAULT TTL: 004.20s", "PERIMETER: HARDENED"];

function SimulationWidget() {
  const panelRef = useRef(null);
  const wasInsideRef = useRef(true);
  const [node, setNode] = useState({ x: 50.5, y: 47.5 });
  const [dragging, setDragging] = useState(false);
  const [flash, setFlash] = useState(false);
  const [terminalLines, setTerminalLines] = useState([secureLogLine]);

  const isInside = useMemo(() => {
    return (
      node.x >= secureZone.x &&
      node.x <= secureZone.x + secureZone.width &&
      node.y >= secureZone.y &&
      node.y <= secureZone.y + secureZone.height
    );
  }, [node]);

  useEffect(() => {
    if (!isInside) {
      if (wasInsideRef.current) {
        setTerminalLines([alertLogLine]);
        setFlash(true);
        const timer = setTimeout(() => setFlash(false), 520);
        wasInsideRef.current = false;
        return () => clearTimeout(timer);
      }
      return undefined;
    }

    if (!wasInsideRef.current) {
      setTerminalLines([secureLogLine]);
      wasInsideRef.current = true;
    }

    const stream = setInterval(() => {
      setTerminalLines((lines) => [...lines.slice(-3), secureLogLine]);
    }, 1450);

    return () => clearInterval(stream);
  }, [isInside]);

  const clampCoordinate = (value) => Math.min(100, Math.max(0, Number.isFinite(value) ? value : 0));

  const setCoordinate = (axis, value) => {
    const nextValue = clampCoordinate(Number.parseFloat(value));
    setNode((current) => ({ ...current, [axis]: nextValue }));
  };

  const updateNode = (event) => {
    const bounds = panelRef.current?.getBoundingClientRect();
    if (!bounds) return;
    const clientX = event.clientX ?? event.touches?.[0]?.clientX;
    const clientY = event.clientY ?? event.touches?.[0]?.clientY;
    if (clientX === undefined || clientY === undefined) return;
    const nextX = Math.min(98, Math.max(2, ((clientX - bounds.left) / bounds.width) * 100));
    const nextY = Math.min(96, Math.max(4, ((clientY - bounds.top) / bounds.height) * 100));
    setNode({ x: nextX, y: nextY });
  };

  return (
    <section className="simulation-card reveal reveal-delay-2" data-testid="simulation-widget">
      <div className="simulation-head">
        <div>
          <p className="eyebrow" data-testid="simulation-eyebrow">Live proximity simulation</p>
          <h2 data-testid="simulation-title">Drag the access node through the vault grid.</h2>
        </div>
        <div
          className={`state-pill ${isInside ? "verified" : "purged"} ${flash ? "flash" : ""}`}
          data-testid="simulation-state-pill"
        >
          {isInside ? "SECURE" : "PURGED"}
        </div>
      </div>

      <div className="simulation-console-layout" data-testid="simulation-console-layout">
        <div
          ref={panelRef}
          className={`grid-stage ${!isInside ? "danger" : ""}`}
          data-testid="simulation-grid-canvas"
          onMouseDown={(event) => {
            setDragging(true);
            updateNode(event);
          }}
          onMouseMove={(event) => dragging && updateNode(event)}
          onMouseUp={() => setDragging(false)}
          onMouseLeave={() => setDragging(false)}
          onTouchStart={(event) => {
            setDragging(true);
            updateNode(event);
          }}
          onTouchMove={(event) => updateNode(event)}
          onTouchEnd={() => setDragging(false)}
        >
          <div
            className="secure-box"
            style={{ left: `${secureZone.x}%`, top: `${secureZone.y}%`, width: `${secureZone.width}%`, height: `${secureZone.height}%` }}
            data-testid="simulation-secure-zone"
          />
          <div className="scanline" data-testid="simulation-scanline" />
          <div className="node-trail" style={{ left: `${node.x}%`, top: `${node.y}%` }} data-testid="simulation-node-trail" />
          <button
            className={`drag-node ${isInside ? "inside" : "outside"}`}
            style={{ left: `${node.x}%`, top: `${node.y}%` }}
            data-testid="simulation-draggable-node"
            aria-label="Drag proximity node"
            type="button"
          >
            <span />
          </button>
        </div>

        <div className="coordinate-panel" data-testid="coordinate-panel">
          <label htmlFor="x-coordinate" data-testid="x-coordinate-label">
            X Coordinate
            <input
              id="x-coordinate"
              type="number"
              min="0"
              max="100"
              step="0.1"
              value={node.x.toFixed(1)}
              onChange={(event) => setCoordinate("x", event.target.value)}
              data-testid="x-coordinate-input"
            />
          </label>
          <label htmlFor="y-coordinate" data-testid="y-coordinate-label">
            Y Coordinate
            <input
              id="y-coordinate"
              type="number"
              min="0"
              max="100"
              step="0.1"
              value={node.y.toFixed(1)}
              onChange={(event) => setCoordinate("y", event.target.value)}
              data-testid="y-coordinate-input"
            />
          </label>
        </div>
      </div>

      <div className={`terminal-log ${isInside ? "verified" : "breach"} ${flash ? "flash" : ""}`} data-testid="simulation-terminal-log">
        {terminalLines.map((line, index) => (
          <div key={`${line}-${index}`} data-testid={`terminal-log-line-${index}`}>
            {line}
          </div>
        ))}
      </div>
    </section>
  );
}

function WaitlistPanel() {
  const [entries, setEntries] = useState([]);
  const [form, setForm] = useState({ name: "", firm: "", email: "" });
  const [loading, setLoading] = useState(false);

  const fetchEntries = async () => {
    const response = await axios.get(`${API}/waitlist`);
    setEntries(response.data);
  };

  useEffect(() => {
    fetchEntries().catch(() => toast.error("Unable to sync waitlist telemetry."));
  }, []);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    try {
      await axios.post(`${API}/waitlist`, form);
      toast.success("Sandbox access request secured.");
      setForm({ name: "", firm: "", email: "" });
      await fetchEntries();
    } catch (error) {
      const message = error.response?.data?.detail || "Unable to register this access request.";
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="waitlist-section" id="waitlist" data-testid="waitlist-section">
      <div className="waitlist-copy reveal">
        <p className="eyebrow" data-testid="waitlist-eyebrow">Early sandboxed access</p>
        <h2 data-testid="waitlist-title">Built for wealth firms and law offices guarding post-quantum trust.</h2>
        <p data-testid="waitlist-description">
          Register a principal contact for the Project Artemis console preview. The sandbox is optimized for high-value offices with strict perimeter controls.
        </p>
      </div>

      <div className="waitlist-grid reveal reveal-delay-1">
        <form className="access-form" onSubmit={handleSubmit} data-testid="waitlist-form">
          <label htmlFor="name" data-testid="waitlist-name-label">Contact name</label>
          <input
            id="name"
            data-testid="waitlist-name-input"
            value={form.name}
            onChange={(event) => setForm({ ...form, name: event.target.value })}
            placeholder="Avery Sterling"
            required
          />
          <label htmlFor="firm" data-testid="waitlist-firm-label">Firm / company</label>
          <input
            id="firm"
            data-testid="waitlist-firm-input"
            value={form.firm}
            onChange={(event) => setForm({ ...form, firm: event.target.value })}
            placeholder="Sterling Capital Counsel"
            required
          />
          <label htmlFor="email" data-testid="waitlist-email-label">Work email</label>
          <input
            id="email"
            type="email"
            data-testid="waitlist-email-input"
            value={form.email}
            onChange={(event) => setForm({ ...form, email: event.target.value })}
            placeholder="avery@firm.example"
            required
          />
          <button className="primary-button full" disabled={loading} type="submit" data-testid="waitlist-submit-button">
            {loading ? "Securing request..." : "Request sandbox access"}
          </button>
        </form>

        <aside className="admin-list" data-testid="waitlist-admin-panel">
          <div className="admin-list-head">
            <span data-testid="waitlist-admin-title">Access queue</span>
            <strong data-testid="waitlist-count">{entries.length}</strong>
          </div>
          <div className="entry-list" data-testid="waitlist-entry-list">
            {entries.length === 0 ? (
              <div className="empty-entry" data-testid="waitlist-empty-state">No sandbox requests yet.</div>
            ) : (
              entries.map((entry) => (
                <div className="entry-row" key={entry.id} data-testid={`waitlist-entry-${entry.id}`}>
                  <div>
                    <strong data-testid={`waitlist-entry-name-${entry.id}`}>{entry.name}</strong>
                    <span className="entry-firm" data-testid={`waitlist-entry-firm-${entry.id}`}><Building2 size={13} /> {entry.firm}</span>
                    <span data-testid={`waitlist-entry-email-${entry.id}`}>{entry.email}</span>
                  </div>
                  <small data-testid={`waitlist-entry-tier-${entry.id}`}>{entry.access_tier}</small>
                </div>
              ))
            )}
          </div>
        </aside>
      </div>
    </section>
  );
}

function App() {
  return (
    <main className="artemis-shell" data-testid="artemis-landing-page">
      <Toaster richColors position="top-right" />
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />

      <nav className="nav-bar reveal" data-testid="top-navigation">
        <a className="brand-mark" href="#top" data-testid="brand-link">
          <span data-testid="brand-symbol">▲</span>
          <strong data-testid="brand-name">Project Artemis</strong>
        </a>
        <div className="nav-links" data-testid="navigation-links">
          <a href="#simulation" data-testid="nav-simulation-link">Simulation</a>
          <a href="#features" data-testid="nav-features-link">Capabilities</a>
          <a href="#waitlist" data-testid="nav-waitlist-link">Waitlist</a>
        </div>
      </nav>

      <section className="hero-section" id="top" data-testid="hero-section">
        <div className="hero-copy reveal reveal-delay-1">
          <div className="status-strip" data-testid="hero-status-strip">
            <ShieldCheck size={16} /> Secure quantum perimeter online
          </div>
          <p className="eyebrow" data-testid="hero-eyebrow">Aegis Proximity Vault</p>
          <h1 data-testid="hero-title">Aegis Proximity Vault</h1>
          <p className="hero-subtitle" data-testid="hero-subtitle">
            Defend enterprise networks against Harvest-Now, Decrypt-Later quantum threats with spatial-gated lattice cryptography.
          </p>
          <div className="hero-actions" data-testid="hero-actions">
            <a className="primary-button" href="#simulation" data-testid="launch-console-button">
              Launch Console <ArrowUpRight size={18} />
            </a>
            <a className="ghost-button" href="#waitlist" data-testid="join-waitlist-button">Join sandbox waitlist</a>
          </div>
        </div>

        <div className="hero-console reveal reveal-delay-2" data-testid="hero-console-card">
          <div className="console-topline" data-testid="console-topline">
            <span /> ARTEMIS // AE-01
          </div>
          <div className="orbital-vault" data-testid="orbital-vault-visual">
            <div className="vault-ring ring-a" />
            <div className="vault-ring ring-b" />
            <div className="vault-core"><ShieldCheck size={42} /></div>
          </div>
          <div className="telemetry-grid" data-testid="telemetry-grid">
            {telemetryRows.map((row) => (
              <div key={row} data-testid={`telemetry-row-${row.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`}>{row}</div>
            ))}
          </div>
        </div>
      </section>

      <div id="simulation" data-testid="simulation-anchor">
        <SimulationWidget />
      </div>

      <section className="features-section" id="features" data-testid="features-section">
        <div className="section-intro reveal">
          <p className="eyebrow" data-testid="features-eyebrow">Cyber-physical defense layer</p>
          <h2 data-testid="features-title">Quantum-safe access that fails closed.</h2>
        </div>
        <div className="feature-grid" data-testid="features-grid">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <article className={`feature-card reveal reveal-delay-${index + 1}`} key={feature.title} data-testid={`feature-card-${index + 1}`}>
                <Icon className="feature-icon" size={30} />
                <h3 data-testid={`feature-title-${index + 1}`}>{feature.title}</h3>
                <p data-testid={`feature-copy-${index + 1}`}>{feature.copy}</p>
              </article>
            );
          })}
        </div>
      </section>

      <WaitlistPanel />

      <footer className="footer-bar" data-testid="footer-bar">
        <span data-testid="footer-brand">Project Artemis</span>
        <span data-testid="footer-status">Spatial-gated lattice cryptography concept console</span>
      </footer>
    </main>
  );
}

export default App;