---
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
`fixtures/jh_oracle.json` is present (the `jh_oracle_pinned` gate is green): JH version/build + ayanamsha +
reference outputs for the native captured once. If absent, this unit is INELIGIBLE.

## Scope
- Implement the JH-parity formula layer so the engine's outputs match the JH oracle field-by-field to the
  declared tolerances (positions to arc-seconds; Vimshottari periods contiguous, sum 120y; SAV grand total
  337; navamsa-lagna consistency; etc.).
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
