---
status: COMPLETE
unit: 1.2
wave: 1
title: Drive the natal engine to JH parity (hard gate G1)
stream: C
worktree: ../MadhavStreamC
blockedBy: [1.1, jh_oracle_pinned]
sets_gate: G1_jh_parity
on_red: halt_queue   # engine parity blocks ALL of L2.5 — stop and surface, don't churn
---

## Context (self-contained)
G1 is THE hard gate: nothing above L1 builds until the engine reproduces the pinned Jagannatha Hora oracle.
Native decision: **JH-as-oracle** — JH (a pinned version + ayanamsha) is the authority; FORENSIC v8.0 is a
reconciliation, not the oracle (resolves the circularity where FORENSIC defers to JH). JH is a build-time
validation fixture, NOT a runtime dependency.

## Precondition
`fixtures/jh_oracle.json` is present (the `jh_oracle_pinned` gate is green). Per native decision it holds
**INPUTS + CONVENTIONS ONLY** — birth datetime/tz, JH coordinates (85°50′E / 20°14′N), the `ayanamsha_registry`
(canonical `jh_true_chitra` pinned to JH's **23°37′09.78″**), house system, node type — **plus a small ANCHOR
set** the native chooses to expose (D1 ascendant + the 9 sidereal longitudes) for the automated gate. The FULL
JH report is **held back** by the native as the independent manual-verification set — do NOT seed JH's computed
outputs as the oracle (that would make parity circular). If the fixture is absent, this unit is INELIGIBLE.

## Scope
- **Canonical ayanamsha = True Chitra pinned to JH** (`jh_true_chitra`): raw pyswisseph `TRUE_CITRA` is ~8″
  from JH's 23°37′09.78″ — close the residual via the true-vs-mean (nutation) flag or `SE_SIDM_USER` pinned to
  JH's value, whichever reproduces JH exactly. (Standard `LAHIRI` reproduces FORENSIC, NOT JH — do not use it
  as canonical.) This determination IS the Phase-0 ayanamsha gate.
- Implement the JH-parity formula layer so the engine's outputs match the JH **anchor set** (ascendant + 9
  sidereal longitudes under `jh_true_chitra`) to arc-second tolerance; assert structural invariants
  (Vimshottari contiguous + sum 120y; SAV grand total 337; navamsa-lagna consistency). Deeper field-by-field
  parity is the native's manual comparison against the held-back full report.
- Compute + store all three ayanamsha sets (canonical / kp / reference) per the 1.1 isolation contract; the
  **constant-offset invariant** across sets is a REQUIRED parity sub-test (catches cross-contamination).
- Add an independent **pyswisseph cross-check** on the astronomical core (catches adapter/config drift).
- Add a **multi-chart edge-case validation set** (Gemini keeper): extreme latitudes, retrograde-station
  timing, leap-second boundaries — to prove parity generalizes beyond the single native chart.
- Pin `engine_version` + `ayanamsha_config_id` in provenance on every output.

## Acceptance criteria (all automated)
1. `pytest python-sidecar/natal_engine/tests/test_jh_parity.py -q` green (field-by-field vs the oracle).
2. pyswisseph cross-check agrees with the engine core to arc-second tolerance.
3. Edge-case validation set passes (no NaN/anomaly at extreme latitudes / retrograde stations / leap seconds).
4. Determinism: same inputs + same `engine_version` ⇒ byte-identical JSONL across two runs.

## must_not_touch
`platform/python-sidecar/routers/**`, `platform/src/**`.

## Commit cadence / rollback
Commits per formula domain (positions → houses → vargas → dashas → panchanga → sensitive points), each with
its parity sub-test. on_red=halt_queue: if parity cannot be reached, Conductor stops the whole queue and
writes CONDUCTOR_HALT_LOG.md (the engine is the program's spine — a human reads it at re-kick). Rollback =
revert to the last green formula domain.
