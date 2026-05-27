---
unit: 1.1
wave: 1
title: JH-equivalent natal engine — scaffold + JH-parity test harness
stream: C
worktree: ../MadhavStreamC
blockedBy: [naming_ci]
on_red: rollback
---

## Context (self-contained)
Wave 1 is a BUILD, not a refactor (audit): today's `python-sidecar` is panchang/ephemeris/jaimini-stub only —
there is NO full natal engine. Create a new deterministic engine module that will (in unit 1.2) reproduce the
**pinned Jagannatha Hora oracle** (G1). NO LLM in the compute path (B.10). This unit builds the skeleton +
the parity-test HARNESS; the actual parity pass is unit 1.2 (which needs the JH fixture).

## Scope
- New module `platform/python-sidecar/natal_engine/` (pure deterministic: pyswisseph + a JH-parity formula
  layer). Define the canonical output JSONL schema (positions, ascendant, houses, dignities, vargas, dashas,
  panchanga, sensitive points) + an `engine_version` + `ayanamsha_config` stamp on every output.
- `fixtures/` dir with a `jh_oracle.json` LOADER + schema (the actual reference data arrives via the
  `jh_oracle_pinned` gate — native input).
- `tests/test_scaffold.py`: asserts the module imports, emits schema-valid JSONL for the native inputs
  (1984-02-05 10:43 IST, Bhubaneswar), and that `tests/test_jh_parity.py` EXISTS and is collectable (skips if
  the oracle fixture is absent).
- Existing `routers/` become thin adapters over the new engine in a LATER unit — do not rewire them now.

## Acceptance criteria (all automated)
1. `pytest platform/python-sidecar/natal_engine/tests/test_scaffold.py -q` green.
2. Engine emits schema-valid JSONL for the native birth inputs (no parity assertion yet).
3. `test_jh_parity.py` is present and collectable (xfail/skip when `fixtures/jh_oracle.json` absent).
4. No LLM call anywhere in the engine path (grep asserts no model client import).

## must_not_touch
`platform/python-sidecar/routers/**`, `platform/src/**`.

## Commit cadence / rollback
Commits: (1) module + schema, (2) fixture loader + harness, (3) scaffold tests. Rollback = revert; net-new
module, no effect on existing sidecar routers.
