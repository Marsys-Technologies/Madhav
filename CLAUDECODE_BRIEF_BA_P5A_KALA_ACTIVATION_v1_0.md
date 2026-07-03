---
canonical_id: CLAUDECODE_BRIEF_BA_P5A_KALA_ACTIVATION
version: 1.0
status: READY-FOR-EXECUTION — gated on BA-P3B COMPLETE (may run ∥ P4 tail); conductor fills ⟦SLOT⟧s
created: 2026-07-03
author: Cowork (Beyond-Acharya unified program; substance frozen — conductor fills slots only)
program: BEYOND_ACHARYA_UNIFIED_EXECUTION_PLAN_v1_0.md — phase P5A (Kāla activation: prophecy's timing half)
slots: ⟦P4_OR_P3B_CLOSE_SHA⟧ ⟦NEXT_MIGRATION_NUMBERS⟧
common_rules: FROZEN contract · delete-then-insert §N.3 · degeneracy gates · two-chart rule ·
  service-not-storage for fine-grain computation · single-constants-source (brahma_formula_constants).
sanity_values: 7 dasha systems live in chart_dashas (Vimshottari/Yogini/Ashtottari/Chara-karaka/
  Naisargika/Mudda/Kalachakra + P3A's classical Chara); current MD/AD derivable for run date; promise
  register populated (P3B) — activation predicates must link to real pratijna_ids.
may_touch: ["ka_yojaka/ka_sangam/ka_vighnakara writers", "NEW ka_avadhi + ka_taranga writers + migrations", "transit service (AV-gate logic)", "bg_transit_rules EXT (+bg_transit_av_gates)"]
must_not_touch: ["L2 stored data", "ph_* writers (P5B owns)", "orchestrator", "any second combustion/threshold constant anywhere"]
---

# BRIEF BA-P5A — KĀLA ACTIVATION

**Code anchors:** `ka_sangam.py` `_insert_windows` (confidence=convergence mirror — C10 bug);
`ka_vighnakara.py` `_COMBUSTION_ORB_DEG=6.0` (C12 bug — delete; read per-graha from
bg_combustion_orbs/L1 single truth) + `_SEVERITY_THRESHOLDS` → brahma_formula_constants; transit engine
REAL at `pipeline/transit_search.py` + `services/ka_gochara` (extend, don't rebuild).

## Step 1 — ka_yojaka EXT (the L2↔L3 bridge completes)
Fill signals' dasha_activation columns across ALL dasha systems; promise-linked activation predicates:
for each bodha_pratijna row, the periods whose lords connect to the promise (by lordship, occupancy,
karaka role, dispositor chain), with **multi-system cross-confirmation count** as a first-class score.

## Step 2 — NEW ka_avadhi (Period Dossiers — powers Q1 "how will my Ketu dasha be")
DDL: `kala_avadhi(chart_id, system_id, level_n, lord_graha, period_start, period_end, dossier jsonb
{lord_condition_fact_refs (sign/nakshatra/dispositor/D9/karaka roles — REFS to chart_facts, never
restated values — trap-1), activated_pratijna_ids, sublord_modulation}, quality jsonb, citations,
UNIQUE(chart_id, system_id, level_n, period_start))`. Populate MD+AD levels, all systems, both charts.

## Step 3 — NEW ka_taranga (Activation Waveform)
DDL: `kala_taranga(chart_id, month date, scope_kind ∈{domain,event_class}, scope_id, activation numeric,
components jsonb, formula_version, UNIQUE(chart_id, month, scope_kind, scope_id))`. Monthly convolution
of dasha×transit×promise, 1950–2100. Fine grain (daily/hourly) = SERVICE computation, never stored.

## Step 4 — Conflation fixes + AV-transit gates
ka_sangam: confidence_score gets a real derivation (distinct from convergence_score) or the column is
dropped w/ migration note. ka_vighnakara: per-graha combustion from the single L1 truth; flat 6.0°
DELETED. bg_transit_rules EXT: AV kakshya/SAV gates + vedha + double-transit (Jupiter+Saturn) rules,
cited; transit service applies them on demand.

## Anti-goals
No stored day-grain waveform. No writer-local judgment constants (registry only). Dossiers REFERENCE
fact_ids, never copy computed values. ka_* never writes to bodha_* tables.

## Exit gates
- [ ] kala_activation + predicates populated BOTH charts `[verify-against: db]`
- [ ] Q1 smoke: current-MD `kala_avadhi` row for 482012f1 includes ≥1 activated_pratijna_id + citations;
      a "Ketu dasha 2027" query composes a dossier-backed reading `[verify-against: prod]`
- [ ] one combustion truth: repo grep for orb literals → only bg_combustion_orbs consumers `[verify-against: repo]`
- [ ] confidence ≠ convergence in kala_convergence schema/values `[verify-against: db]`
- [ ] waveform sanity: kala_taranga rows both charts; distributions non-degenerate; known Sade-Sati years
      show elevated obstruction-adjusted activation `[verify-against: db]`
- [ ] golden-eval non-regression; TIMING-class questions now scoreable
