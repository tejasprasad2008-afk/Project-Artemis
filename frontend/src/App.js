import { useEffect, useMemo, useRef, useState } from "react";
import "@/App.css";
import axios from "axios";
import { ShieldCheck, Flame, Radar, LockKeyhole, Building2, ArrowUpRight, Terminal, Scan, Shield, Brain, Sparkles, Cpu } from "lucide-react";
import { Toaster, toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const concealedSecureZone = { x: 49.2, y: 47.4, width: 2.7, height: 5.0 };
const initialLogLines = [
  "[GEMINI-FLASH // SYSTEM] Secure quantum proximity vault active.",
  "[GEMINI-FLASH // INTEL] Ready for physical boundary attestation.",
  "[GEMINI-FLASH // ANALYSIS] Proximity scan online. Awaiting coordinate stream..."
];

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

function EnterpriseWorkflow() {
  return (
    <section className="workflow-section reveal" id="workflow" data-testid="workflow-section" style={{ paddingBottom: '6rem' }}>
      <div className="section-intro">
        <p className="eyebrow" data-testid="workflow-eyebrow">Enterprise deployment</p>
        <h2 data-testid="workflow-title" style={{ fontSize: 'clamp(2rem, 5vw, 4.5rem)', lineHeight: '0.94', letterSpacing: '-0.075em', marginBottom: '2rem' }}>
          How Aegis Proximity Vault works.
        </h2>
      </div>
      <div className="workflow-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
        <article className="workflow-card" data-testid="workflow-card-1" style={{ border: '1px solid var(--line)', borderRadius: '1.6rem', padding: '1.5rem', background: 'rgba(255, 255, 255, 0.02)' }}>
          <div className="workflow-icon-wrap" style={{ color: 'var(--green)', marginBottom: '1rem' }}>
            <Terminal size={24} />
          </div>
          <div className="workflow-step" style={{ fontSize: '0.72rem', fontFamily: 'monospace', color: 'var(--green)', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
            Step 01 // Initial Setup
          </div>
          <h3 style={{ fontSize: '1.35rem', marginBottom: '0.5rem', letterSpacing: '-0.03em' }}>Secure Enclave</h3>
          <p style={{ color: 'var(--muted)', fontSize: '0.92rem', lineHeight: '1.6' }}>A multi-family wealth office initializes a terminal session.</p>
        </article>
        <article className="workflow-card" data-testid="workflow-card-2" style={{ border: '1px solid var(--line)', borderRadius: '1.6rem', padding: '1.5rem', background: 'rgba(255, 255, 255, 0.02)' }}>
          <div className="workflow-icon-wrap" style={{ color: 'var(--green)', marginBottom: '1rem' }}>
            <Scan size={24} />
          </div>
          <div className="workflow-step" style={{ fontSize: '0.72rem', fontFamily: 'monospace', color: 'var(--green)', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
            Step 02 // Gemini Audit
          </div>
          <h3 style={{ fontSize: '1.35rem', marginBottom: '0.5rem', letterSpacing: '-0.03em' }}>Spatial Gating</h3>
          <p style={{ color: 'var(--muted)', fontSize: '0.92rem', lineHeight: '1.6' }}>Gemini verifies the operator's physical presence within 10cm using UWB telemetry.</p>
        </article>
        <article className="workflow-card" data-testid="workflow-card-3" style={{ border: '1px solid var(--line)', borderRadius: '1.6rem', padding: '1.5rem', background: 'rgba(255, 255, 255, 0.02)' }}>
          <div className="workflow-icon-wrap" style={{ color: 'var(--green)', marginBottom: '1rem' }}>
            <Shield size={24} />
          </div>
          <div className="workflow-step" style={{ fontSize: '0.72rem', fontFamily: 'monospace', color: 'var(--green)', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
            Step 03 // Key Destruction
          </div>
          <h3 style={{ fontSize: '1.35rem', marginBottom: '0.5rem', letterSpacing: '-0.03em' }}>Quantum Armor</h3>
          <p style={{ color: 'var(--muted)', fontSize: '0.92rem', lineHeight: '1.6' }}>Lattice keys encrypt the transaction, self-destructing the moment the operator walks away.</p>
        </article>
      </div>
    </section>
  );
}

function SimulationWidget() {
  const panelRef = useRef(null);
  const concealedStateRef = useRef(false);
  const [node, setNode] = useState({ x: 50.5, y: 47.5 });
  const [dragging, setDragging] = useState(false);
  const [terminalLines, setTerminalLines] = useState(initialLogLines);
  const [purged, setPurged] = useState(false);

  const lastNode = useRef({ x: 50.5, y: 47.5, t: Date.now() });
  const coordHistory = useRef([]);
  const [metrics, setMetrics] = useState({
    velocity: 0,
    jitter: 0.045,
    entropy: 0.982,
    threatLevel: "LOW",
  });

  const concealedZoneState = useMemo(() => {
    return (
      node.x >= concealedSecureZone.x &&
      node.x <= concealedSecureZone.x + concealedSecureZone.width &&
      node.y >= concealedSecureZone.y &&
      node.y <= concealedSecureZone.y + concealedSecureZone.height
    );
  }, [node]);

  useEffect(() => {
    concealedStateRef.current = concealedZoneState;
  }, [concealedZoneState]);

  // Dynamic metrics evaluation loop
  useEffect(() => {
    const now = Date.now();
    const dt = (now - lastNode.current.t) / 1000;
    const dx = node.x - lastNode.current.x;
    const dy = node.y - lastNode.current.y;
    const dist = Math.sqrt(dx * dx + dy * dy);

    let velocity = 0;
    if (dt > 0) {
      velocity = dist / dt / 8; // scaled
    }
    if (velocity > 12) velocity = 12;

    coordHistory.current = [...coordHistory.current.slice(-19), { x: node.x, y: node.y, t: now }];

    let jitter = 0.035 + Math.random() * 0.02;
    if (coordHistory.current.length > 2) {
      let sum = 0;
      let diffs = [];
      for (let i = 1; i < coordHistory.current.length; i++) {
        const dX = coordHistory.current[i].x - coordHistory.current[i - 1].x;
        const dY = coordHistory.current[i].y - coordHistory.current[i - 1].y;
        const step = Math.sqrt(dX * dX + dY * dY);
        diffs.push(step);
        sum += step;
      }
      const avg = sum / diffs.length;
      if (avg > 0) {
        const variance = diffs.reduce((acc, v) => acc + Math.pow(v - avg, 2), 0) / diffs.length;
        jitter = Math.sqrt(variance);
      }
    }

    const isNearBorder = node.x < 15 || node.x > 85 || node.y < 12 || node.y > 88;
    const isOut = node.x <= 3.5 || node.x >= 96.5 || node.y <= 3.5 || node.y >= 96.5;

    let threatLevel = "LOW";
    if (isOut) {
      threatLevel = "CRITICAL";
      if (!purged) {
        setPurged(true);
        toast.error("[VAULT TTL EXPIRED // LATTICE KEY PURGED]", {
          description: "Drift boundary violation. System collapsed.",
        });
      }
    } else if (isNearBorder) {
      threatLevel = "ELEVATED";
    }

    let entropy = 0.982;
    if (isOut) {
      entropy = 0.000;
    } else if (dist === 0) {
      entropy = Math.max(0.12, 0.98 - (coordHistory.current.length * 0.03));
    } else {
      entropy = Math.min(0.999, 0.82 + (jitter * 3.5) + Math.random() * 0.04);
    }

    setMetrics({
      velocity,
      jitter,
      entropy,
      threatLevel,
    });

    lastNode.current = { x: node.x, y: node.y, t: now };
  }, [node, purged]);

  // Telemetry logs streaming
  useEffect(() => {
    const stream = setInterval(() => {
      if (purged) {
        setTerminalLines((lines) => [
          ...lines.slice(-3),
          `[GEMINI-FLASH // ALERT] Vault perimeter breach at X:${node.x.toFixed(1)}, Y:${node.y.toFixed(1)}`,
          `[GEMINI-FLASH // ALERT] ZERO-TRUST VALIDATION FAILED. Volatile keys purged.`,
        ]);
        return;
      }

      const isNearBorder = node.x < 15 || node.x > 85 || node.y < 12 || node.y > 88;
      const insideSecure =
        node.x >= concealedSecureZone.x &&
        node.x <= concealedSecureZone.x + concealedSecureZone.width &&
        node.y >= concealedSecureZone.y &&
        node.y <= concealedSecureZone.y + concealedSecureZone.height;

      let log = "";
      if (insideSecure) {
        log = `[GEMINI-FLASH // STATUS] Target inside secure vault core. Spatial gating verified. Lattice keys primed.`;
      } else if (isNearBorder) {
        const warnings = [
          `[GEMINI-FLASH // WARNING] Near-boundary drift at X:${node.x.toFixed(1)}, Y:${node.y.toFixed(1)}. Potential perimeter leak.`,
          `[GEMINI-FLASH // WARNING] Behavioral drift anomaly. Key decay timer initialized.`,
          `[GEMINI-FLASH // WARNING] High threat coordinate vector. Zero-trust challenge escalated.`,
        ];
        log = warnings[Math.floor(Math.random() * warnings.length)];
      } else {
        const normals = [
          `[GEMINI-FLASH // ANALYSIS] Real-time tracking at X:${node.x.toFixed(1)}, Y:${node.y.toFixed(1)}. Pattern: GENUINE.`,
          `[GEMINI-FLASH // CONTEXT] Spatial entropy: ${metrics.entropy.toFixed(4)}. Velocity: ${metrics.velocity.toFixed(2)} m/s.`,
          `[GEMINI-FLASH // INTEL] Monitoring jitter metrics (${metrics.jitter.toFixed(4)}). Threat level: LOW.`,
          `[GEMINI-FLASH // ANALYSIS] Safe zone standby. Zero-trust nonces synced.`,
        ];
        log = normals[Math.floor(Math.random() * normals.length)];
      }

      setTerminalLines((lines) => [...lines.slice(-4), log]);
    }, 1450);

    return () => clearInterval(stream);
  }, [node, purged, metrics]);

  const handleResetVault = () => {
    setNode({ x: 50.5, y: 47.5 });
    setPurged(false);
    setTerminalLines([
      "[GEMINI-FLASH // SYSTEM] Re-initializing quantum secure enclave...",
      "[GEMINI-FLASH // INTEL] New session nonce generated.",
      "[GEMINI-FLASH // ANALYSIS] Proximity scan online. Awaiting coordinate stream..."
    ]);
    toast.success("Quantum secure enclave re-initialized.");
  };

  const clampCoordinate = (value) => Math.min(100, Math.max(0, Number.isFinite(value) ? value : 0));

  const setCoordinate = (axis, value) => {
    const nextValue = clampCoordinate(Number.parseFloat(value));
    setNode((current) => ({ ...current, [axis]: nextValue }));
  };

  const updateNode = (event) => {
    if (purged) return; // disable updates when locked
    const bounds = panelRef.current?.getBoundingClientRect();
    if (!bounds) return;
    const clientX = event.clientX ?? event.touches?.[0]?.clientX;
    const clientY = event.clientY ?? event.touches?.[0]?.clientY;
    if (clientX === undefined || clientY === undefined) return;
    const nextX = Math.min(98, Math.max(2, ((clientX - bounds.left) / bounds.width) * 100));
    const nextY = Math.min(96, Math.max(4, ((clientY - bounds.top) / bounds.height) * 100));
    setNode({ x: nextX, y: nextY });
  };

  const isNear = node.x < 15 || node.x > 85 || node.y < 12 || node.y > 88;
  const cardClass = `simulation-card reveal reveal-delay-2 ${purged ? "purged" : isNear ? "warning" : ""}`;
  const pillText = purged
    ? "KEYS PURGED // BREACHED"
    : isNear
    ? "DEGRADED // BOUNDARY THREAT"
    : concealedZoneState
    ? "UWB SECURED // ML-KEM ACTIVE"
    : "STATE SECURED // MASKED";

  const pillClass = `state-pill ${purged ? "purged" : isNear ? "purged" : concealedZoneState ? "verified" : "masked"}`;

  return (
    <section className={cardClass} data-testid="simulation-widget">
      <div className="simulation-head">
        <div>
          <p className="eyebrow" data-testid="simulation-eyebrow">Live proximity simulation</p>
          <h2 data-testid="simulation-title">Drag the access node through the vault grid.</h2>
        </div>
        <div className={pillClass} data-testid="simulation-state-pill" style={{ fontFamily: 'monospace' }}>
          {pillText}
        </div>
      </div>

      <div className="simulation-console-layout" data-testid="simulation-console-layout">
        <div
          ref={panelRef}
          className={`grid-stage ${purged ? "danger" : ""}`}
          data-testid="simulation-grid-canvas"
          onMouseDown={(event) => {
            if (purged) return;
            setDragging(true);
            updateNode(event);
          }}
          onMouseMove={(event) => dragging && updateNode(event)}
          onMouseUp={() => setDragging(false)}
          onMouseLeave={() => setDragging(false)}
          onTouchStart={(event) => {
            if (purged) return;
            setDragging(true);
            updateNode(event);
          }}
          onTouchMove={(event) => updateNode(event)}
          onTouchEnd={() => setDragging(false)}
        >
          <div className="scanline" data-testid="simulation-scanline" />
          <div className="node-trail" style={{ left: `${node.x}%`, top: `${node.y}%` }} data-testid="simulation-node-trail" />
          <button
            className="drag-node masked"
            style={{ left: `${node.x}%`, top: `${node.y}%`, cursor: purged ? 'not-allowed' : 'grab' }}
            data-testid="simulation-draggable-node"
            aria-label="Drag proximity node"
            type="button"
            disabled={purged}
          >
            <span />
          </button>

          {purged && (
            <div className="purged-overlay" style={{
              position: 'absolute',
              inset: 0,
              background: 'rgba(3, 7, 6, 0.94)',
              display: 'grid',
              placeItems: 'center',
              zIndex: 10,
              backdropFilter: 'blur(8px)',
            }}>
              <div className="purged-alert-box" style={{
                textAlign: 'center',
                padding: '2rem',
                border: '1px solid #ff4f57',
                borderRadius: '1.5rem',
                background: 'rgba(15, 2, 4, 0.88)',
                boxShadow: '0 20px 60px rgba(255, 79, 87, 0.2), inset 0 0 30px rgba(255, 79, 87, 0.1)',
                maxWidth: '440px',
                width: 'calc(100% - 2rem)',
              }}>
                <Flame className="purged-icon" size={42} style={{ color: '#ff4f57', marginBottom: '1rem' }} />
                <h3 style={{ color: '#ff4f57', fontFamily: 'monospace', fontSize: '1.1rem', marginBottom: '0.5rem', letterSpacing: '0.05em' }}>
                  [VAULT TTL EXPIRED // LATTICE KEY PURGED]
                </h3>
                <p style={{ color: '#ffb3b7', fontSize: '0.88rem', marginBottom: '1.5rem', lineHeight: '1.5' }}>
                  Proximity credentials burned. Zero-trust cascade collapsed due to boundary drift.
                </p>
                <button className="reset-vault-button" onClick={handleResetVault} data-testid="reset-vault-button" style={{
                  background: '#ff4f57',
                  color: '#030706',
                  border: 'none',
                  borderRadius: '0.8rem',
                  padding: '0.75rem 1.5rem',
                  fontFamily: 'inherit',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}>
                  Reset Vault Core
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="coordinate-panel" data-testid="coordinate-panel" style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
          <div className="coordinate-inputs" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
            <label htmlFor="x-coordinate" data-testid="x-coordinate-label">
              X Coord
              <input
                id="x-coordinate"
                type="number"
                min="0"
                max="100"
                step="0.1"
                value={node.x.toFixed(1)}
                onChange={(event) => setCoordinate("x", event.target.value)}
                data-testid="x-coordinate-input"
                disabled={purged}
              />
            </label>
            <label htmlFor="y-coordinate" data-testid="y-coordinate-label">
              Y Coord
              <input
                id="y-coordinate"
                type="number"
                min="0"
                max="100"
                step="0.1"
                value={node.y.toFixed(1)}
                onChange={(event) => setCoordinate("y", event.target.value)}
                data-testid="y-coordinate-input"
                disabled={purged}
              />
            </label>
          </div>

          {/* Gemini Context Engine Module */}
          <div className="gemini-engine-card" data-testid="gemini-engine-card" style={{
            border: '1px solid rgba(66, 255, 155, 0.12)',
            borderRadius: '1rem',
            padding: '0.9rem',
            background: 'rgba(0, 0, 0, 0.28)',
            boxShadow: 'inset 0 0 16px rgba(66, 255, 155, 0.02)',
          }}>
            <div className="engine-card-header" style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', marginBottom: '0.4rem', borderBottom: '1px solid rgba(66, 255, 155, 0.1)', paddingBottom: '0.4rem' }}>
              <Brain size={14} style={{ color: 'var(--green)' }} />
              <span style={{ fontSize: '0.72rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--white)' }}>Gemini Context Engine</span>
              <span className={`engine-status-dot`} style={{
                marginLeft: 'auto',
                width: '0.42rem',
                height: '0.42rem',
                borderRadius: '50%',
                background: purged ? '#ff4f57' : isNear ? '#ffb84d' : '#42ff9b',
                boxShadow: `0 0 8px ${purged ? '#ff4f57' : isNear ? '#ffb84d' : '#42ff9b'}`
              }} />
            </div>
            <p className="engine-card-desc" style={{ fontSize: '0.72rem', color: 'var(--muted)', lineHeight: '1.45', marginBottom: '0.6rem' }}>
              Lattice cryptography handles key math, but Gemini acts as the **Intelligent Context Engine**—auditing behavior, drift, and session entropy to trigger automatic key purges.
            </p>
            <div className="engine-metrics" style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', fontFamily: 'monospace', fontSize: '0.68rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px dashed rgba(255,255,255,0.04)', paddingBottom: '0.2rem' }}>
                <span style={{ color: 'var(--muted)' }}>Spatial Entropy</span>
                <span style={{ color: 'var(--green)' }}>{metrics.entropy.toFixed(3)}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px dashed rgba(255,255,255,0.04)', paddingBottom: '0.2rem' }}>
                <span style={{ color: 'var(--muted)' }}>Velocity Vector</span>
                <span style={{ color: 'var(--green)' }}>{metrics.velocity.toFixed(2)} m/s</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px dashed rgba(255,255,255,0.04)', paddingBottom: '0.2rem' }}>
                <span style={{ color: 'var(--muted)' }}>Behavior Profile</span>
                <span style={{ color: purged ? '#ff4f57' : isNear ? '#ffb84d' : '#42ff9b' }}>
                  {purged ? "BREACHED" : isNear ? "DEGRADED" : "GENUINE"}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--muted)' }}>Threat Level</span>
                <span style={{ color: purged ? '#ff4f57' : isNear ? '#ffb84d' : '#42ff9b', fontWeight: 'bold' }}>
                  {metrics.threatLevel}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="terminal-log masked" data-testid="simulation-terminal-log">
        {terminalLines.map((line, index) => (
          <div key={`${line}-${index}`} data-testid={`terminal-log-line-${index}`}>
            {line}
          </div>
        ))}
      </div>
    </section>
  );
}

const mockProvisioned = [
  { id: "mock-1", access_tier: "PROVISIONED" },
  { id: "mock-2", access_tier: "PROVISIONED" },
  { id: "mock-3", access_tier: "PROVISIONED" },
  { id: "mock-4", access_tier: "PROVISIONED" },
];

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
          <div className="admin-list-head" style={{ flexDirection: 'column', alignItems: 'flex-start', gap: '0.4rem', marginBottom: '0.9rem' }}>
            <span data-testid="waitlist-admin-title" style={{ fontSize: '0.82rem', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--muted)' }}>
              Sandbox Enrollment Status
            </span>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem', width: '100%' }}>
              <strong data-testid="waitlist-count" style={{ fontSize: '1.6rem', color: 'var(--green)', lineHeight: 1 }}>14/20</strong>
              <span style={{ fontSize: '0.82rem', color: 'var(--muted)', fontWeight: 500 }}>Firms Provisioned (Batch 1)</span>
            </div>
            <div style={{ fontSize: '0.78rem', color: '#ffb84d', fontFamily: 'monospace', marginTop: '0.2rem' }}>
              * Applications open for Batch 2
            </div>
          </div>
          
          <div className="entry-list" data-testid="waitlist-entry-list">
            {/* Provisioned Section */}
            <div style={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.1em', color: 'var(--green)', margin: '0.4rem 0 0.4rem', fontFamily: 'monospace', fontWeight: 600 }}>
              Active Enclaves (Batch 1)
            </div>
            {mockProvisioned.map((entry, idx) => (
              <div className="entry-row" key={entry.id} data-testid={`waitlist-entry-${entry.id}`} style={{ borderLeft: '3px solid var(--green)', paddingLeft: '0.75rem' }}>
                <div>
                  <strong data-testid={`waitlist-entry-name-${entry.id}`} style={{ fontSize: '0.9rem' }}>Provisioned Enclave {idx + 1}</strong>
                  <span className="entry-firm" data-testid={`waitlist-entry-firm-${entry.id}`}><Building2 size={13} /> Confidential Firm</span>
                </div>
                <small data-testid={`waitlist-entry-tier-${entry.id}`} style={{ fontSize: '0.7rem', color: 'var(--green)', textTransform: 'uppercase', background: 'rgba(66, 255, 155, 0.08)', padding: '0.2rem 0.4rem', borderRadius: '4px', border: '1px solid rgba(66, 255, 155, 0.15)' }}>
                  {entry.access_tier}
                </small>
              </div>
            ))}

            {/* Dynamic Section */}
            <div style={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.1em', color: '#ffb84d', margin: '1rem 0 0.4rem', fontFamily: 'monospace', fontWeight: 600 }}>
              Pending Evaluation (Batch 2)
            </div>
            {entries.length === 0 ? (
              <div className="empty-entry" data-testid="waitlist-empty-state" style={{ borderLeft: '3px dashed rgba(255, 184, 77, 0.3)', paddingLeft: '0.75rem' }}>
                No pending applications. Applications open for Batch 2.
              </div>
            ) : (
              entries.map((entry, idx) => (
                <div className="entry-row" key={entry.id} data-testid={`waitlist-entry-${entry.id}`} style={{ borderLeft: '3px solid #ffb84d', paddingLeft: '0.75rem' }}>
                  <div>
                    <strong data-testid={`waitlist-entry-name-${entry.id}`} style={{ fontSize: '0.9rem' }}>Pending Applicant</strong>
                    <span className="entry-firm" data-testid={`waitlist-entry-firm-${entry.id}`}><Building2 size={13} /> Identity Redacted</span>
                  </div>
                  <small data-testid={`waitlist-entry-tier-${entry.id}`} style={{ fontSize: '0.7rem', color: '#ffb84d', textTransform: 'uppercase', background: 'rgba(255, 184, 77, 0.08)', padding: '0.2rem 0.4rem', borderRadius: '4px', border: '1px solid rgba(255, 184, 77, 0.15)' }}>
                    {entry.access_tier || "EVALUATING"}
                  </small>
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
          <a href="#workflow" data-testid="nav-workflow-link">Workflow</a>
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

      <EnterpriseWorkflow />

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