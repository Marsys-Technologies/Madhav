---
canonical_id: CLAUDECODE_BRIEF_BA_P3B_L2_REGENERATION
version: 1.0
status: READY-FOR-EXECUTION — gated on BA-P3A COMPLETE; conductor fills ⟦SLOT⟧s
created: 2026-07-03
author: Cowork (Beyond-Acharya unified program; substance frozen — conductor fills slots only)
program: BEYOND_ACHARYA_UNIFIED_EXECUTION_PLAN_v1_0.md — phase P3B (THE ONE SHOT: the single L2 regeneration)
slots: ⟦P3A_CLOSE_SHA_AND_MIGRATION_NUMBERS⟧ ⟦PRE_P3_SNAPSHOT_ID⟧ ⟦NEXT_MIGRATION_NUMBER⟧
common_rules: FROZEN contract §N.2 · delete-then-insert §N.3 · degeneracy gate on EVERY new scoring
  column · trap-1 (reference fact_ids, never restate) · two-chart rule (Abhinandan FIRST) · PD-5.
sanity_values: post-regen expectations — 482012f1 ≈12,954 signals/ayanamsha (±5% acceptable from
  aggregation), 90 yogas as composite signals ranked in domain top bands, contradictions >0 BOTH charts
  with domains_affected filled, signature_tier='chart_defining' fires >0, salience distribution
  non-degenerate (no value >3× expected frequency).
may_touch: ["bo_laksana/bo_bimba/bo_karanajala/bo_samvada/bo_upaya writers", "NEW bo_pratijna writer + migration", "bo_sangati writer + bodha_triangulation migration", "bodha_writers/formulas.py (unify—delete divergent site)", "retrieval intrinsic-input swap (shape-stable)"]
must_not_touch: ["orchestrator/planner", "L1 writers/data", "envelope shape / retrieval interfaces beyond the documented input swap", "prior values (frozen at P2T)"]
---

# BRIEF BA-P3B — THE L2 SINGLE REGENERATION

**Code anchors:** `bo_laksana.py` — `_compute_salience` L740–808 (v1 formula to replace),
`_signature_tier` L419–428 (thresholds to recut), `_build_signal_row` L847–851 (constituent-refs
re-resolution site, C9); DIVERGENT second formula in `bodha_writers/formulas.py` — unify to ONE function,
delete the other (C5). Priors read from `brahma_class_priors` (P3A) — the ONLY weight source.

## Step 0 — Snapshot before rebuild (charter §4)
Dump affected bodha_* tables for BOTH charts; record ⟦PRE_P3_SNAPSHOT_ID⟧. Rehearse restore on Abhinandan.

## Step 1 — bo_laksana v2.0 (formula version bump; ONE site)
`salience_v2 = class_prior(brahma_class_priors) × varga_weight × specificity × verification_rescale ×
condition_terms(v1: orb/dignity/house_wt/av_mult/vargottama/neechabhanga/cancellation) × bala_gate ×
functional_context` — stored STATIC (activation/karaka/varga-affinity remain query-time, trap #18).
- **specificity** = `1 + 0.5 × extremity_pctl`, extremity = percentile of |value − family median| within
  (family × chart × ayanamsha).
- **verification_rescale** = {two_pass_verified: 1.00, single_pass: 0.85, documented_approximation: 0.60}
  — REPLACES `log(1+corroboration)/log(10)` and its 0.778 ceiling (C5, the true top-band strangler).
- **bala_gate** (yoga-class only) = `clamp(norm_constituent_shadbala, 0.30, 1.00)`; serve state
  `present_but_enfeebled` when <0.60 — a state, never an exclusion.
- **functional_context** from ga_structural functional benefic/malefic per lagna.
- Store: `salience_pctl_in_class` (S-A — priors decide BETWEEN families, percentiles WITHIN; kills ties);
  NULL-propagation + `salience_inputs_complete` (S-C — no silent 0.5/1.0/bindus=4 defaults, trap #17);
  `salience_robustness` + cross-ayanamsha consistency fill (S-D/B5 — the stubbed columns).
- **Hierarchical aggregation:** atomic families (per-varga AV tallies etc.) roll into composite profile
  signals carrying the distribution; atoms remain rows, flagged `aggregation_member`, never top-band.
- **signature_tier recut** against the v2 distribution so `chart_defining` FIRES (top ~1% band by design).
- **Constituent integrity:** re-resolve constituent_facts_array at `_build_signal_row`; gate ≥99% resolve.

## Step 2 — Graph, contradictions, CDLM
bo_bimba/bo_karanajala: typed edges (dispositor · argala/virodha · parivartana · yoga-membership ·
karaka-role · nakshatra-dispositor · KP-sub-lord) with `valence`, `relationship_basis`,
`affected_domains` FILLED; node strengths from salience v2; pagerank backfilled (kills the P2 COALESCE
fallback). bodha_contradictions POPULATED both charts + `domains_affected` + reconciliation record
(evidence-weighted verdict citing both sides). CDLM/sangati aggregates apply S-B effective evidence:
family contribution = `max_salience_in_family × (1 + log10(1 + n_family))`; report raw AND effective counts.

## Step 3 — New assets + remedy fix
**bo_pratijna** (NEW; migration ⟦NEXT_MIGRATION_NUMBER⟧): `bodha_pratijna(chart_id, ayanamsha_id,
event_class_id → brahma_event_ontology, status ∈{promised,denied,conditional}, grade numeric,
supporting_signal_ids uuid[], contradicting_signal_ids uuid[], varga_confirmation jsonb, derivation
jsonb, formula_version, UNIQUE(chart_id, ayanamsha_id, event_class_id))` — the Promise Register.
**bo_sangati EXT:** `bodha_triangulation(chart_id, ayanamsha_id, question_class, tradition,
verdict_inputs jsonb, concordance_score, formula_version)` — Parashari/Jaimini/KP/Tajika stacks.
**bo_upaya:** de-degenerate resonance (F-007) from salience-v2 inputs — distribution gate applies.

## Step 4 — Regenerate ONCE + swap
One L2 regeneration via cockpit: Abhinandan FIRST → gates → 482012f1. Then swap retrieval's intrinsic
inputs from query-time computation to the stored columns — envelope diff must be EMPTY on 5 spot tools.

## Anti-goals
ONE regeneration (never iterate priors here — frozen at P2T). No envelope shape change. No interface
change beyond the documented swap. Abhinandan before native, always. No second formula site survives.

## Exit gates
- [ ] G10-STORED: `get_signals(482012f1, career, limit=10)` via STORED path → zero atomic tallies,
      ≥3 yoga-class, ranking_basis present `[verify-against: prod]`
- [ ] degeneracy sweep: salience_v2/pctl/robustness/resonance all non-degenerate `[verify-against: db]`
- [ ] constituent resolve ≥99% · signature_tier chart_defining >0 · contradictions >0 both charts w/
      domains `[verify-against: db]`
- [ ] promise register smoke: `SELECT status, count(*) FROM bodha_pratijna WHERE chart_id=$NATIVE GROUP
      BY 1` → all three statuses, grades non-degenerate `[verify-against: db]`
- [ ] zero consumer-visible interface change (5-tool envelope diff) + golden-eval ≥ P2 baseline
      `[verify-against: prod]`
- [ ] rollback rehearsed on Abhinandan from ⟦PRE_P3_SNAPSHOT_ID⟧
