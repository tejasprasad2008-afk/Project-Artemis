# Project Artemis PRD

## Original Problem Statement
Build a premium, high-tech SaaS landing page for a project called ‘Project Artemis'. Use an elite, dark-mode cyberpunk design system with deep obsidian backgrounds, clean white typography, and vibrant green accents for secure elements.

1. Hero Section: Title: 'Aegis Proximity Vault'. Subtitle: 'Defend enterprise networks against Harvest-Now, Decrypt-Later quantum threats with spatial-gated lattice cryptography.' Include a prominent 'Launch Console' Call-to-Action button.

2. Interactive Simulation Widget: A visual 2D grid canvas where users can drag a node point. If the node is inside a designated box, display a green active state reading 'UWB Position Verified // NIST ML-KEM Decrypted'. If dragged outside, flash amber reading 'Out of Bounds // Volatile Keys Purged'.

3. Features Grid: Detail 10cm UWB spatial tracking simulation, automated key-burning mechanisms, and zero-trust perimeter containment.

4. Waitlist Form: A clean input form for local wealth firms and law offices to register for early sandboxed access, capturing names and emails.

5. Follow-up enhancement: Add firm/company field to the waitlist flow.

6. Follow-up enhancement: Redesign simulation with a larger radar grid, smaller secure zone, synced X/Y coordinate inputs, and compact terminal feedback.

7. Follow-up enhancement: Mask simulation state labels and visual color changes so visitors must infer whether the node is secured.

8. Follow-up enhancement: Make the secure zone a concealed one-grid-unit internal hitbox with no visible boundary or terminal state reveal.

## User Choices
- Waitlist signups are stored in MongoDB and displayed in an admin-style access queue on the page.
- Simulation node starts inside the secure zone with green verified state.
- Build as a single polished landing page.

## Architecture Decisions
- React frontend uses `REACT_APP_BACKEND_URL` from `/app/frontend/.env` for all API calls.
- FastAPI backend exposes `/api/waitlist` create/list endpoints and uses MongoDB via existing `MONGO_URL`.
- Waitlist records use UUID string IDs and exclude MongoDB `_id` from responses.
- Styling is split into focused Artemis CSS modules imported from `App.css`.

## Implemented
- Premium dark cyberpunk SaaS landing page for Project Artemis.
- Hero with Aegis Proximity Vault messaging and Launch Console CTA.
- Interactive enlarged draggable radar grid with a concealed one-grid-unit secure zone, synced X/Y coordinate inputs, masked node styling, and terminal telemetry that does not reveal secure/purged state or zone location.
- Features grid covering UWB spatial tracking, automated key burning, and zero-trust containment.
- Waitlist form with name, firm/company, email, database persistence, duplicate email handling, toasts, and admin-style list.
- Backend regression tests added for waitlist API.

## Testing Summary
- Python lint passed for backend.
- JavaScript lint passed for frontend.
- Backend API tested via external app URL: root, create waitlist, list waitlist, duplicate handling.
- Browser flow tested: hero load, CTA navigation, simulation state, waitlist update.
- Testing agent completed backend + frontend validation with 100% pass rate.
- Firm/company field self-tested through API and browser form submission; queue shows submitted company.
- Simulation redesign self-tested in browser: coordinate typing moves the node, dragging updates coordinates, and the zone remains visually concealed with masked telemetry.

## Backlog
### P0
- None currently; required MVP flows are working.

### P1
- Add lightweight admin filtering/search for the access queue.
- Add firm type/category selection for wealth firm vs law office segmentation.

### P2
- Add animated security proof metrics or customer-segment trust badges.
- Add downloadable sandbox briefing PDF capture flow.
