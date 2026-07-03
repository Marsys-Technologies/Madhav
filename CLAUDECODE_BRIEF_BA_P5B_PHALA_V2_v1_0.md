---
canonical_id: CLAUDECODE_BRIEF_BA_P5B_PHALA_V2
version: 1.0
status: READY-FOR-EXECUTION — gated on BA-P5A COMPLETE (needs activation + dossiers); conductor fills ⟦SLOT⟧s
created: 2026-07-03
author: Cowork (Beyond-Acharya unified program; substance frozen — conductor fills slots only)
program: BEYOND_ACHARYA_UNIFIED_EXECUTION_PLAN_v1_0.md — phase P5B (Phala v2: prophecy's prediction half)
slots: ⟦P5A_CLOSE_STATE⟧ ⟦NEXT_MIGRATION_NUMBERS⟧
common_rules: FROZEN contract · degeneracy gates · two-chart rule · falsifiability-by-schema ·
  base rates from brahma_event_ontology (never invented in code).
sanity_values: posteriors MUST span the full range — `SELECT min(posterior) FROM phala_anchors WHERE
  chart_id=$NATIVE` < 0.2 (an instrument that cannot say "unlikely" is broken — the G-LADDER's sin);
  every anchor carries a lift_vector + structured falsifier; rectification's validated 10:43 unchanged.
may_touch: ["ph_nimitta REBUILD (services/ph_nimitta/engine.py + writer)", "ph_muhurta EXT", "prashna chart-type build path", "mi_bhavisya freeze format (additive)"]
must_not_touch: ["ka_* writers (P5A owns)", "L2 stored data", "orchestrator", "ph_pramana rectification logic (keep — it validates 10:43)"]
---

# BRIEF BA-P5B — PHALA v2 (ANCHOR REBUILD + ELECTION + PRASHNA)

**Code anchors:** `services/ph_nimitta/engine.py` — DELETE `compute_confidence_range` (G-LADDER L44–60)
and keyword `derive_domain`/`derive_event_type`; KEEP `_KARMIC_FRAME` + `compute_magnitude` (tiers →
brahma_formula_constants); `generate_falsifier` replaced by structured objects. `charts.chart_type`
exists since P3A. Activity ontology: `brahma_activity_ontology` (P3A). Confirm L4 `id`/`anchor_id`
schema fix (migration 365) live before rebuild.

## Step 1 — ph_nimitta v2 (PROMISE → ACTIVATION → TRIGGER → DELIVERY)
Anchor = `(event_class_id, window, magnitude, posterior)` where
`posterior = base_rate(event_class, age_band, window ← brahma_event_ontology) × promise_lift(bodha_pratijna
grade) × activation_lift(ka_avadhi/ka_yojaka cross-confirmation) × trigger_lift(AV-transit gates +
double-transit)`. Each lift's inputs frozen per anchor as `lift_vector` (P6's analytic-attribution
substrate). Falsifier = structured `{event_class, magnitude_floor, window, attestation_required}` —
machine-decidable against the LEL's ontology mapping. Event WHAT comes from the ontology's signature
model matched against the promise register — the keyword string-matching dies. Full probability range
served, incl. `denied/unlikely` anchors (they are predictions too). Ayanamsha robustness survives as a
lift modifier.

## Step 2 — ph_muhurta EXT (activity-aware election)
`brahma_activity_ontology` significators × panchanga (verify panchanga_daily populated — P0 closed this)
× tarabala/chandrabala vs the NATIVE'S chart (not generic) × fructification rules; emits follow-up hooks
(consumed by P7B's scheduler; P6's Loop B).

## Step 3 — Prashna path (chart-type, not layer)
`chart_type='prashna'` build: cast at question time (birth_params = question moment + location), minimal
asset set (ga_positions, ga_panchanga, prashna judgment via existing L0 bg_prashna_rules); Q4
undertaking recipe = prashna verdict × election scoring × fructification timing, composed in retrieval.

## Anti-goals
NO posterior floor or ceiling constants in code (bounds live in the registry if needed at all). No
keyword-derived event types. No writer-local base rates. Anchors without lift_vectors are Ring-1
failures. Do not touch rectification.

## Exit gates
- [ ] anchors both charts span full probability range w/ lift_vectors + structured falsifiers
      `[verify-against: db]` — smoke: min(posterior) < 0.2
- [ ] Q2/Q3 smoke: "job change this year?" returns an event-class anchor with posterior + falsifier +
      citations `[verify-against: prod]`
- [ ] Q4 smoke: an undertaking query composes prashna + election + fructification `[verify-against: prod]`
- [ ] G-LADDER absent from repo (grep) `[verify-against: repo]`
- [ ] golden-eval: PREDICTION/TIMING classes ≥ rubric floor; overall non-regression
