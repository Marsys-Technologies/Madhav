---
artifact: OVERFLOW_QUEUE (Elevation Campaign v2.1, charter §7.6)
version: 1.0
status: FROZEN
authored_by: RUNWAY session (non-participant, per charter M2.4 — supersedes §7.6's original
  "written by α" note, which M2.4 explicitly moves to the runway session)
---

# Overflow queue

A stream that completes its own lane early pulls the NEXT item from this queue rather than idling.
**Never pulls another stream's open lane.** Items are ordered; pull from the top. Mark an item
`CLAIMED-<stream>` in place when pulled — never delete a row, so the morning report shows exactly
what overflow work happened and who did it.

| # | item | source | notes |
|---|---|---|---|
| 1 | EL-21 phase-2 — serving-time claim-checker rollout beyond the initial scope-pass | `ELEVATION_REGISTER_v1_0.md` EL-21 | Root-cause pass already scoped where it runs / latency budget / claim classes; phase-2 is applying it beyond the first claim class once phase-1 lands in a stream's own lane. |
| 2 | EL-22 — four mandated instrumentation tracks (experience telemetry, investigation I1–I5, Vidhi V1–V5, retrieval RE1–RE5) not yet captured outside Darpana run 1 | `ELEVATION_REGISTER_v1_0.md` EL-22 | Extend capture to this campaign's own battery runs once the base lanes are dispositioned. |
| 3 | EL-23 — battery blind spot: add consumption-ratio (EL-04) + volunteered-findings counts as first-class grading dimensions in the standing battery, with benchmark pairs per domain | `ELEVATION_REGISTER_v1_0.md` EL-23 | Extends the standing battery, not this run's harness (§2 Ω-V is separately frozen and out of scope for this item). |
| 4 | Corpus-OCR tail — any remaining classical-source OCR/citation backfill items not folded into a stream's assigned lane | `ELEVATION_CAMPAIGN_CHARTER_v2_1.md` §7.6 | Scope to be confirmed against the classical-bridge work already merged (`fix/ba-classical-bridge`, `docs/ba-l0-classical-bridge-reports`) before claiming — check for overlap first. |
| 5 | Additional battery domains beyond the two flagship domains (wealth, career) — extend Ω4/Ω7-style routing and dark-corpus coverage to marriage and health | This queue | The 60-item routing suite already covers all four domains (`ROUTING_SUITE_60_v1_0.json`); this item is extending Ω7 dark-corpus-style replay coverage to marriage/health once wealth+career are closed. |
| 6 | γ.I planner-coverage items not required for flagship acceptance — EL-01,02,03,04,05,06,14,23,26,27,29,31,44,45,56,61 residuals beyond what Lane Ω's Phase 4 acceptance strictly requires | `ELEVATION_CAMPAIGN_CHARTER_v2_1.md` §4 (RC-4 cluster table) | Pull only the residual items still open after Lane Ω's own acceptance criteria (§2 Ω-V) are met — do not duplicate work already covered by Ω1–Ω8. |

## Rules
- Pulling an item does not relieve a stream of its own lane's completion criteria — overflow work is
  additive, never a substitute for a `PARKED-HONEST` lane.
- An item claimed and later abandoned (stream ran out of time) is marked `CLAIMED-<stream>,
  ABANDONED-<reason>` in place, never removed — the queue is an audit trail as much as a work source.
- New items may be appended during the run (e.g. a stream discovers genuine overflow-shaped work) but
  the existing six rows are frozen and must not be reworded.
