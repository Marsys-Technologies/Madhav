---
artifact: PARIPRASHNA_DECISION_REGISTER_v1_0
canonical_id: PARIPRASHNA_DECISION_REGISTER
version: 1.0
status: LIVING — append-only; never renumber, rewrite, or delete; supersede by later entry
produced_during: PARIPRASHNA-V012-PHASE1 (Cowork, Fable 5, 2026-08-18)
date: 2026-08-18
authoritative_side: claude
role: >
  The single decision log for the Paripraśna workstream — ADR-style. Consolidates
  the native rulings (D-xx), resolved-by-events forks, DVA rulings that bind this
  surface, and the NCD series. New decisions APPEND here first; document edits
  follow. Cross-cutting decisions not owned by this workstream go to
  CROSS_CUTTING_DECISION_REGISTER instead.
changelog:
  - "1.0 (2026-08-18): first assembly from TA §1/§1.1/§1.2/§2 + the v0.12 §13 rulings."
---

# Paripraśna — Decision Register

## §1 — Native rulings (D-series, 2026-07-19 unless noted; full rationale: TA v0.11 §1)

D-01 name Paripraśna · D-02 consult/consume retire · D-03 channels unnamed ·
D-04 exactly two channels · D-05 cross-channel transcript portability dropped
· D-06 history to a high bar · D-07 evolve-architecture/replace-component ·
D-08 one registry, generated projections · D-09 guest model · D-10 prediction
capture implemented not deferred · D-11 architecture precedes execution ·
D-12 effectiveness irrespective of cost · D-13 Claude-Code/Gemini render bar
· D-14 no internal register in prose, universally · **D-15 no audience tier —
one register for everyone** (distinct from disclosure classes; see NCD packet
and the two-axis rule) · D-16 provenance stamp, per-turn, copied never
referenced · D-17 shim-first sequencing (superseded by events: PB-1 built the
fork; see §2) · D-18 corrections in place with the error visible. Plus the
2026-07-27 layout rulings (reference rail removed; grounding to the right
dock) and D-19 (three query controls, design plan §5.8.1).

## §2 — Resolved by events (governed campaigns; citations: TA v0.11 §1.2)

OT-2 → `prashna_ask` job handle · OT-7/OT-10 → generated full/compact/consult
profiles, OAuth-scope-gated · OT-8 → renderer rebuilt on canonical parts ·
OT-11 → `brahma_mimamsa_prediction_ledger` canonical (mig 470; `mcp_predictions`
retired) · OT-12 → fork-with-reorder (moot) · PARK L-5 → **DVA Ruling 55**
(new `mimamsa_conversational_calibration` table) + **DVA Ruling 79** (exact
schema, COLLECT-ONLY, leak guard) — ruled, deliberately unbuilt ·
**DVA Ruling 80** — byte-equality capture flag stays OFF pending the
Ruling-54 posture (apparatus repurposed per PPR-10).

## §3 — Proposed, awaiting ruling (v0.11 leans; unruled, low-stakes confirmations)

OT-1 engine in-process (confirm-and-close proposed) · OT-3 cron-in-webapp
(confirm-and-close proposed) · OT-4 guest build rights → (b) super-admin-only
with "request a rebuild" · OT-5 MCP OAuth issuer → ratify shipped direction ·
OT-6 MCP durable memory → (a) none, T-2's condition met.

## §4 — The NCD series (Native-Call Decisions, v0.12 packet)

| ID | Decision | Status · date |
|---|---|---|
| NCD-1 | Fidelity (G2–G3) before the default flip (G5) | **RULED (a)** · 2026-08-18 |
| NCD-2 | Five-artifact decomposition at G0 | **RULED adopt** · 2026-08-18 |
| NCD-3 | Acharya Reading Contract (receipt v1, B.4 trigger, confidence enum, earned-calibrated-language rule) | **RATIFIED** · 2026-08-18 |
| NCD-4 | Native-self sensitive readings: interstitial (cohort: full seal) | **RULED interstitial** · 2026-08-18 (formalization route = NCD-10) |
| NCD-5 | DB roles + RLS on C1/C3 at Gate 1 | **RULED (a)** · 2026-08-18 |
| NCD-6 | Provider posture: document now, strict allowlist on first cohort subject | **RULED** · 2026-08-18 |
| NCD-7 | Calibration activation defaults (±0.15 interval half-width on effective n; ≥60% coverage) pre-registered; `model_p` at G9 | **RATIFIED** · 2026-08-18 |
| NCD-8 | Spend caps $2/turn · $40/day, pre-dispatch, both doors | **RULED** · 2026-08-18 |
| NCD-9 | Adopt `chart_subject_consent` schema at G1 (Scope-Boundary rationale: PPR-14/PPR-27 — protection for charts that exist TODAY, not M7 pre-building) | **RULED — adopt at G1** · 2026-08-18 |
| NCD-10 | Formalization route for NCD-4's §3.5.C relaxation: §3.10.B MP amendment vs ND-class native directive | **RULED — ND directive** · 2026-08-18. Action bound to G0 close: log the directive in NATIVE_DIRECTIVES_FOR_REVISION (native-self interstitial for health-crisis/mental-health readings; cohort subjects unaffected — full seal); folds into the next natural MP revision per §3.10.A(d). |
| NCD-11 | `calibration_method_version` column on the Ruling-79 sink — a proposed amendment to a DVA-fixed schema | **RULED — amend at build time** · 2026-08-18. The sink is built once, with the column; recorded as a native-approved amendment to DVA Ruling 79's schema, effective at the G9 build. |

Ordering note (red-team lens C): NCD-1..8 were ruled before the package
red-team ran; CURRENT status stayed correctly gated on the red-team
(RED_TEAM_G0_v1_0.md, PASS-WITH-FIXES, fixes applied) — the rulings are value
decisions the panel could not make; the panel attacked the package's
soundness after them. NCD-9..11 were ruled AFTER the panel, closing every
decision the panel surfaced. **As of 2026-08-18 the NCD series is fully
ruled (NCD-1..11); no Paripraśna architecture decision awaits the native.**
What remains is mechanics: the G0-close session (registration, status flips,
the NCD-10 directive logging, SESSION_LOG) and then Gate-1 execution.

## §5 — Append protocol

New entry = next NCD number (or cite the external authority: DVA-n, CCD-n,
W-n) · date · decider · one-paragraph decision · affected PPR-IDs · the
document edits it authorizes. The Register is the FIRST write of any
architectural change; the Architecture edit cites the entry.

*End PARIPRASHNA_DECISION_REGISTER v1.0.*
