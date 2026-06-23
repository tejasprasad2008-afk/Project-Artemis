# Website Polishes and Copywriting Improvements

This plan outlines the design and implementation of the four website polishes requested by the team to elevate Project Artemis from a concept console into a finals-worthy Gemini XPRIZE submission.

We will focus on making the **Gemini integration explicit**, showing **market traction and exclusivity**, adding **interactive warning feedback loops to the proximity grid**, and bridging the gap with an **enterprise-grade "How It Works" workflow**.

---

## User Review Required

> [!IMPORTANT]
> **Concealed Secure Zone & Masking**: In previous iterations, we masked all visual cues of the secure zone. With these changes, we are introducing warning states (amber) when the user approaches the boundaries, and a critical lock-down state (red overlay) when they hit the border. The concealed secure zone itself remains a hidden hitbox (no visual bounds), but the feedback loop will now feel highly reactive and gamified.

---

## Open Questions

None at this stage. All requirements from the team's feedback PDF are clear and actionable.

---

## Proposed Changes

### Frontend Components & Styling

We will modify `App.js` and add/modify CSS styling in `artemis-simulation.css` and `artemis-base.css` to accommodate the new sections and state transitions.

---

#### [MODIFY] [App.js](file:///Users/tejasprasad/Project-Artemis/frontend/src/App.js)

1. **Enterprise Workflow Section (How It Works)**:
   - Add a new section `EnterpriseWorkflow` between the `hero-section` and the `simulation` anchor.
   - Implement the 3-step sequence:
     1. **Secure Enclave**: A multi-family wealth office initializes a terminal session.
     2. **Spatial Gating**: Gemini verifies the operator's physical presence within 10cm using UWB telemetry.
     3. **Quantum Armor**: Lattice keys encrypt the transaction, self-destructing the moment the operator walks away.

2. **AI Architecture Module**:
   - Add a new block `GeminiContextEngineCard` in the right column of the `SimulationWidget` (inside the `.coordinate-panel` layout).
   - Display a visual breakdown explaining standard math vs. Gemini's role as the Intelligent Context Engine.
   - Show live analysis metrics driven by the simulation coordinates (e.g., rolling Shannon entropy score, velocity indicators, threat status: `LOW` / `ELEVATED` / `CRITICAL`, and behavior profile: `GENUINE` / `DEGRADED` / `BREACHED`).

3. **Dynamic Gemini-Flash Telemetry Logs**:
   - Replace the static `[TRACE] Lattice telemetry sampling...` lines with dynamic logs showing Gemini analyzing the coordinate stream.
   - Include real-time coordinates, velocity, threat evaluations, and anomaly classifications in the log lines.
   - Print warning logs when approaching borders, and critical purge alerts when out of bounds.

4. **Exclusivity and Sandbox Status (Traction)**:
   - Update `WaitlistPanel` header to show:
     - Title: **Sandbox Enrollment Status**
     - Subheader: `Batch 1 Sandbox Status: 14/20 High-Value Firms Provisioned.`
     - Notice: `Applications open for Batch 2.`
   - Pre-populate the queue with 4 premium provisioned mock firms (Sterling Capital Counsel, Vanguard Trust Group, Hale & Dorr LLP, Apex Legal Advisors) in a `Provisioned` tier.
   - Render user-submitted entries under a `New Applications (Pending Evaluation)` section to keep it fully dynamic.

5. **Elevated Proximity Grid States**:
   - Calculate states:
     - `warning`: when node is near the border (`x < 15 || x > 85 || y < 15 || y > 85`).
     - `purged`: when node touches or goes beyond the border (`x <= 3 || x >= 97 || y <= 3 || y >= 97`).
   - Add conditional class names to the simulation grid container based on these states.
   - For `purged` state, render a red overlay on the grid: `[VAULT TTL EXPIRED // LATTICE KEY PURGED]` with a `[RESET VAULT CORE]` button.
   - Trigger a toast notification on key purge.

---

#### [MODIFY] [artemis-simulation.css](file:///Users/tejasprasad/Project-Artemis/frontend/src/styles/artemis-simulation.css)

- Add CSS classes to support the warning and purged states:
  - `.simulation-card.warning` (redefines theme variables `--green` and `--green-soft` to `--amber` and `--amber-soft`).
  - `.simulation-card.purged` (redefines theme variables `--green` to red `#ff4f57`).
  - Redefine `.grid-stage` grid variables (`--grid-line`, `--grid-border`, `--grid-glow`) to allow smooth theme transitions on state change.
  - Style the `purged` overlay with a retro-cyber alarm flashing effect.
  - Style the `AI Architecture` / `Gemini Context Engine` sub-panel inside the coordinate panel.

---

#### [MODIFY] [artemis-base.css](file:///Users/tejasprasad/Project-Artemis/frontend/src/styles/artemis-base.css)

- Add styling variables and helper animations for the flashing alarm state.
- Add styles for the new 3-step enterprise workflow section (`how-it-works`).

---

## Verification Plan

### Automated Tests
- Run `yarn build` inside `/Users/tejasprasad/Project-Artemis/frontend` to ensure the compilation succeeds with no syntax or packaging errors.
- Run backend tests `pytest backend/tests/` to verify backend functionality remains fully intact.

### Manual Verification
- Launch the development server (`yarn start`) and visually inspect the following:
  1. The new 3-step **Enterprise Workflow** section below the Hero.
  2. The **Gemini Context Engine** module in the simulation area.
  3. Dragging the node close to the border changes the entire simulation widget color palette to amber.
  4. Dragging the node to the absolute border locks the grid, triggers a red warning overlay `[VAULT TTL EXPIRED // LATTICE KEY PURGED]`, and shows the `[RESET VAULT CORE]` button.
  5. The Access Queue panel shows the "Batch 1 Status" header and pre-provisioned firms alongside new waitlist entries.
