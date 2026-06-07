---
artifact: CLAUDECODE_BRIEF_L0FR_STREAM_G_v1_0.md
stream: G — PyHora Integration
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavL0FR-G
branch: feature/l0fr-stream-g-pyhora
budget_cap_usd: 150
---

# Stream G — PyHora Integration

## §1 — Mission
Wire PyHora into python-sidecar (or new pyhora-sidecar) using shared `.se1` infrastructure. Validate L1 Gaṇita pipeline works end-to-end with PyHora as engine.

## §2 — Dependencies
Blocks on `state.yaml: gates.vimarsaka_a.status = pass` (needs `.se1` bundled).

## §3 — Scope
1. Per source data §6: install PyJHora into python-sidecar (or new pyhora-sidecar) Dockerfile
2. Configure `SWE_EPHE_PATH=/app/ephe` env var; verify PyHora reads it
3. Smoke test inside container:
   - Native chart: birth 1984-02-05 10:43 IST Bhubaneswar
   - Compute Sun position via PyHora; verify Capricorn ~21°48'
   - Compute Moon nakshatra; verify Purva Bhadrapada Pada 1
4. Wire PyHora into existing L1 writers for `ganita.graha_sthana`, `ganita.varga`, `ganita.dasakrama`:
   - Per memory `pyjhora-is-the-engine`: PyJHora IS the JH logic; no separate JH parity check
   - Existing l1_*.py writers refactored to call PyHora rather than direct pyswisseph
5. End-to-end integration test:
   - Trigger from cockpit: per-chart build for native, scope=asset, asset=ganita.graha_sthana
   - Orchestrator picks up build_run; invokes python-sidecar (or pyhora-sidecar)
   - Writer calls PyHora; ganita_positions populated for native
   - Cockpit shows ganita.graha_sthana state=lit
6. Cross-check PyHora vs `marsys://tool/L0/query_planet_position` (from Stream B):
   - Native chart same date; both compute Sun position
   - Difference ≤ 0.01° (proves shared ephemeris layer consistency)
   - This is NOT a JH parity check (per memory feedback_no_jh_parity_anywhere); it's an internal consistency check

## §5 — Acceptance criteria
- PyHora installed in python-sidecar; reads `/app/ephe`
- Native chart Sun via PyHora = Capricorn 21°48' (±0.01°)
- ganita.graha_sthana writer uses PyHora; cockpit smoke build succeeds
- Internal consistency: PyHora vs Stream B's query_planet_position agree to ≤0.01°

## §6 — Budget $150.

## §7-§8 — Final summary
Standard format.
