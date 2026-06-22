---
artifact: DRAFT_CLAUDECODE_BRIEF_L4_PH_PRAMANA_v0_1.md
canonical_id: DRAFT_CLAUDECODE_BRIEF_L4_PH_PRAMANA
brief_for: ph_pramana (NEW) — Falsifiability SCAFFOLDING (NOT calibration) [evidence-readiness]
status: SUPERSEDED (2026-06-22) by CLAUDECODE_BRIEF_L4_PH_PRAMANA_v1_0.md (FINALIZED). Retained-in-place for audit trail only — do NOT build from this draft.
version: 0.1
authored_by: Cowork 2026-06-21
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
decisions_ref: L4_PHALA_DECISIONS_LEDGER_v1_0.md (D5, D6, D7 — the calibration boundary)
swarm_coordination:
  wave: P4 (after the prediction assets exist)
  blocked_by: [ph_nimitta, ph_sankrama]
  blocks: [ph_phaladesa]
  may_touch:
    - platform/python-sidecar/pipeline/orchestrator/writers/ph_pramana.py
    - platform/python-sidecar/services/ph_pramana/**
    - platform/supabase/migrations/337_phala_pramana.sql   # [RECON — number]
    - platform/scripts/seed/asset_registry_seed.ts
---

# DRAFT BRIEF — ph_pramana (Falsifiability Scaffolding) — NEW

> **CRITICAL BOUNDARY (D5/D6/D7).** This asset builds the falsifiability SPINE that makes L4
> predictions L5-ready. It does **NOT** backtest, score, or calibrate — ALL scoring lives in L5
> Mīmāṃsā. The test: "does it improve a prediction NOW (L4) or score predictions OVER TIME (L5)?"
> Making a prediction machine-checkably falsifiable = L4. Scoring it against outcomes = L5.

## §0 — What this asset IS (and is NOT)
**IS:** the asset that guarantees every L4 prediction is machine-checkably falsifiable — it normalizes
each prediction's falsifier into a structured, evaluable form, assigns an explicit evaluation date,
and registers the empty outcome hook that L5 will later fill. It produces the **falsification register**
that L5's calibration loop consumes.

**IS NOT:** a backtest, a hit-rate computer, a calibration-curve builder, or a confidence re-tuner.
Those are L5. (Rationale: 57 LEL events are statistically too thin to calibrate per-domain; leakage/
circularity make a clean backtest require non-native validation = L5 apparatus; L5 exists to own this.)

## §1 — Why it matters
A prediction you cannot mechanically refute is not a prediction — it's a horoscope. This asset is what
separates this instrument from every astrologer: every claim ships with a structured, dated,
machine-evaluable refutation condition. It is also the project's mission spine — "calibrated,
correctable predictions testable against lived reality" — built to the point where L5 can do the
testing. L4 makes the predictions *testable*; L5 *tests* them.

## §2 — VERIFIED ground truth
- Every `ph_nimitta` / `ph_sankrama` (and other ph_*) row already carries a `falsifier` text + a
  window. This asset structures them.
- `kala_bhavishya` (L3) has FROZEN `outcome_recorded` + `falsifiability` columns (unfilled) — the
  L3→L5 prediction-record hook already exists. `ph_pramana` aligns L4's predictions to the same shape.
- LEL (`01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md`, 57 events) is the eventual scoring corpus — referenced
  for STRUCTURE (what an evaluable outcome looks like) but NOT scored here.

## §3 — Schema (migration 337 `[RECON]`)
`phala_pramana`:
```
pramana_id            uuid PK
chart_id              uuid NOT NULL
prediction_ref_id     uuid NOT NULL           -- the ph_* row being made falsifiable
prediction_asset      text NOT NULL           -- ph_nimitta | ph_sankrama | ph_muhurta | ...
domain                text
structured_falsifier_jsonb jsonb NOT NULL      -- {confirm_observable, deny_observable, metric, threshold}
evaluation_date       date NOT NULL           -- when L5 should check (typically window_end + grace)
evaluation_window_start date
evaluation_window_end   date
outcome_status        text NOT NULL DEFAULT 'pending'  -- pending|confirmed|denied|partial (L5 WRITES these later)
outcome_recorded_at   timestamptz             -- NULL until L5 fills
outcome_evidence_jsonb jsonb                   -- NULL until L5 fills
l5_handoff_ref        text                     -- pointer to the mi_* record that will score it
derivation_ledger_jsonb jsonb NOT NULL
source_citation       text NOT NULL
computed_at           timestamptz NOT NULL DEFAULT now()
UNIQUE (chart_id, prediction_ref_id)
```
> The `outcome_*` columns are WRITTEN BY L5, not L4. L4 creates the row with `outcome_status='pending'`.

## §4 — Engine spec (`services/ph_pramana/engine.py`)
1. For every prediction row across the ph_* assets, parse its free-text `falsifier` into a STRUCTURED
   form: `{confirm_observable, deny_observable, metric, threshold}` — machine-evaluable.
2. Assign `evaluation_date` = prediction `window_end` + a documented grace period.
3. Register the row with `outcome_status='pending'` and a `l5_handoff_ref` placeholder.
4. **Do NOT score.** No comparison against LEL. No hit-rate. No calibration. (Hard boundary.)
5. Anti-drift: cite the `prediction_ref_id`; write ONLY `phala_pramana`.

## §5 — Acceptance criteria
1. `[pytest]` every prediction across ph_* assets gets exactly one `phala_pramana` row with a structured falsifier.
2. `[pytest]` structured_falsifier_jsonb is machine-evaluable (has confirm/deny observables + metric + threshold).
3. `[pytest]` every row is `outcome_status='pending'`; the engine writes NO outcome/score (boundary check — grep the engine for any LEL scoring → must be ZERO).
4. `[pytest]` evaluation_date computed from window_end + documented grace.
5. `[boundary]` the asset contains NO backtest/hit-rate/calibration code (the D5 line; a Vimarśaka check).
6. `[anti-drift]` writes only phala_pramana; zero `.commit()/.rollback()`.
7. `[psql_prod + curl_prod]` lit; cockpit shows ph_pramana; idempotent; FORENSIC 7/7.

## §6 — Asset registration (NEW) + L5 handoff
Add `ph_pramana` / `Pramāṇa` / `Falsifiability scaffolding` / `phala_pramana` / depends_on
`['ph_nimitta','ph_sankrama']` (+ all prediction-emitting ph_*) / `$1` count_sql / artifact /
delete-then-insert. **Document the L5 onboarding contract:** L5 `mi_pramana` reads `phala_pramana`
where `outcome_status='pending'`, evaluates against lived reality at `evaluation_date`, and WRITES the
`outcome_*` columns + the calibration. L4 never writes outcomes.

## §7 — VALUE ADDED
Makes every L4 prediction machine-checkably falsifiable and dated — the precondition for any honest
calibration — while scrupulously NOT scoring (which would be statistically unsound on 57 events and a
layer-boundary violation). It is the clean seam between "makes predictions" (L4) and "has a measured
track record" (L5).

---
*End of DRAFT ph_pramana v0.1. Scaffolding, not scoring. The L4/L5 seam.*
