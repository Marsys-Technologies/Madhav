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
  panchanga, sensitive points). **Every ayanamsha-dependent value carries a mandatory `ayanamsha_id` as part
  of its key**, plus an `engine_version` stamp. The engine computes the chart under MULTIPLE ayanamshas (see
  the isolation contract below) — not one.
- `fixtures/` dir with a `jh_oracle.json` LOADER + schema (the actual reference data arrives via the
  `jh_oracle_pinned` gate — native input).
- `tests/test_scaffold.py`: asserts the module imports, emits schema-valid JSONL for the native inputs
  (1984-02-05 10:43 IST, Bhubaneswar), and that `tests/test_jh_parity.py` EXISTS and is collectable (skips if
  the oracle fixture is absent).
- Existing `routers/` become thin adapters over the new engine in a LATER unit — do not rewire them now.

## Multi-ayanamsha & data-isolation contract (added 2026-05-27 — native decision)
The engine computes the chart under THREE ayanamshas; nothing may be mixed. Enforce by construction:
- **`ayanamsha_registry`** (versioned config) — each entry `{ayanamsha_id, display_name, swe_sid_mode,
  nutation_flag, pinned_value_arcsec, role, provenance}`. Seed three:
  - `jh_true_chitra` — swe `TRUE_CITRA`, pinned to JH's report value **23°37′09.78″** (raw TRUE_CITRA is ~8″
    off; 1.2 closes it via the nutation flag or `SE_SIDM_USER`). **role = canonical** — Parashari, divisionals,
    dashas, MSR/CDLM/CGM/RM all consume this.
  - `kp` — swe `KRISHNAMURTI` (~23°32′17″). **role = kp** — KP cusps / sub-lords / ruling planets consume this ONLY.
  - `lahiri_standard` — swe `LAHIRI` (≈ FORENSIC's 23°37′58″). **role = reference** — cross-check only.
- **Mandatory key:** every ayanamsha-dependent value is keyed `(chart_id, fact_id, ayanamsha_id)`; `ayanamsha_id`
  is NOT NULL and part of the unique key. **No implicit/default ayanamsha anywhere** — engine, schema, loader,
  or any downstream read. An untagged dependent value is a hard error.
- **Dependent vs invariant:** tag each fact type. Ayanamsha-INVARIANT facts (tithi, karana — pure longitude
  *differences* where the offset cancels) are stored ONCE with `ayanamsha_id='invariant'`. Ayanamsha-DEPENDENT
  facts (sidereal longitudes, nakshatra/pada, yoga, ascendant/cusps, sub-lords, vargas, dasha balance) are
  stored once PER `ayanamsha_id`. Don't triplicate invariants; don't single-store dependents.
- **Role-scoped consumption:** each downstream layer/tool declares the role it reads (Parashari=canonical,
  KP=kp). Recorded in the unified tool contract (2b); verified by the tool↔asset reconciliation (G6). No tool
  reads across roles.
- **Isolation guards (build-time; fail the gate):**
  1. **No untagged value** — schema validation rejects any ayanamsha-dependent row missing `ayanamsha_id`.
  2. **Constant-offset invariant** — for any two ids A,B, every body's sidereal longitude differs by EXACTLY
     `ayanamsha(B)−ayanamsha(A)` (arc-sec tolerance). Any body whose delta differs ⇒ sets were mixed/corrupted ⇒ fail.
  3. **Registry match** — each id's engine-computed ayanamsha equals its `pinned_value_arcsec` (Phase-0 gate).

## Acceptance criteria (all automated)
1. `pytest platform/python-sidecar/natal_engine/tests/test_scaffold.py -q` green.
2. Engine emits schema-valid JSONL for the native birth inputs (no parity assertion yet).
3. `test_jh_parity.py` is present and collectable (xfail/skip when `fixtures/jh_oracle.json` absent).
4. No LLM call anywhere in the engine path (grep asserts no model client import).
5. ISOLATION: schema rejects any ayanamsha-dependent value missing `ayanamsha_id`; the constant-offset
   invariant test passes across the three sets; each id's computed ayanamsha matches its registry pin.

## must_not_touch
`platform/python-sidecar/routers/**`, `platform/src/**`.

## Commit cadence / rollback
Commits: (1) module + schema, (2) fixture loader + harness, (3) scaffold tests. Rollback = revert; net-new
module, no effect on existing sidecar routers.
