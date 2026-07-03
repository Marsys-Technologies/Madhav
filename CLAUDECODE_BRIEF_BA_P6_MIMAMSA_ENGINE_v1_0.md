---
canonical_id: CLAUDECODE_BRIEF_BA_P6_MIMAMSA_ENGINE
version: 1.0
status: READY-FOR-EXECUTION — gated on BA-P5B COMPLETE; conductor fills ⟦SLOT⟧s
created: 2026-07-03
author: Cowork (Beyond-Acharya unified program; substance frozen — conductor fills slots only)
program: BEYOND_ACHARYA_UNIFIED_EXECUTION_PLAN_v1_0.md — phase P6 (Mīmāṃsā v2: the learning loop goes live)
design_authority: MIMAMSA_V2_LEARNING_LAYER_DESIGN_v1_0.md (§4 adjudication, §5 scoring, §6 updates)
slots: ⟦P5_CLOSE_SHAS⟧ ⟦LEL_FILE_SHA⟧
common_rules: FROZEN contract · scoring paths 100% LLM-free (D-1 — any LLM call in adjudication/scoring
  = Ring-1 failure) · eval∩learning corpora = ∅ (lel_overlap enforced) · bounded two-key updates.
sanity_values: LEL lives in `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` (PD-10 — the life_events DB table is
  empty/chart-less; markdown is source of truth); MD5-mod-10 20% holdout preserved; 3× classical-
  divergence cap RETAINED; manifestation-grammar priors RETAINED as Dirichlet smoothing base.
may_touch: ["mi_* writers per MIMAMSA_V2 §1 keep/replace verdicts", "retrodiction generator + date-filtered view mechanism", "bg_class_priors overlay tables", "record_outcome/query_calibration serving"]
must_not_touch: ["L1/L2/L3/L4 data (reads only)", "classical rule CONTENT", "orchestrator", "eval golden answers", "mi_jivanaghatana holdout partition logic"]
---

# BRIEF BA-P6 — MĪMĀṂSĀ v2 ENGINE

**Code anchors:** `mi_pramana.py` (stub falsifier L96–110 — DELETE; timing/magnitude scorers — replace
per §5); `mi_pariksha.py` (attribution catch-all `fam_graha_natal` w/ 0.5 defaults — DELETE;
`_DIM_WEIGHTS` — retire to registry); `mi_kula.py` (`_FAMILIES` — retire to registry); `mi_gunanaka.py`
(n≥10 gates — replace w/ shrinkage; 3× cap — KEEP); `mi_sambandha.py` (`_PRIOR_PROPENSITIES` — keep as
smoothing base); leakage-firewall precedent `services/ph_pramana` train/test split.

## Step 0 — LEL intake (PD-10)
mi_jivanaghatana EXT: parse `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` → mimamsa_event_provenance
(event_class + magnitude mapped per brahma_event_ontology matching_rules; MD5-mod-10 holdout preserved;
rows pinned to ⟦LEL_FILE_SHA⟧). Markdown stays source-of-truth; the DB projection is derived + rebuildable.

## Step 1 — mi_pramana ENGINE v2 (adjudication + scoring)
Adjudication per MIMAMSA_V2 §4: CONFIRMED / PARTIAL (ontology adjacency + magnitude-one-tier +
window±20%) / REFUTED (requires period ATTESTED-complete — an uncurated log never counts as a miss) /
EXPIRED/UNRESOLVED (→ ask-card queue) / FALSE_ALARM (control windows). Scoring per §5: Brier vs the
climatology null (base rates from brahma_event_ontology — sharpness enters through the null); rank-aware
retrodiction credit (1/log2(rank+1)); ECE reliability retained.

## Step 2 — mi_pariksha v2 substeps
`retrodiction_generate` — blind: for each admissible LEL event at date T, data-cutoff T−90d via
DATE-FILTERED VIEWS over chart_facts/chart_dashas (generalize the ph_pramana firewall); run the
R-pipeline (promise→activation→anchor v2) on pre-cutoff data; emit top-k (event_class, window, posterior).
`control_windows` — ≥3 same-length no-event windows per event, age-band stratified. `ablation` — rerun
with each technique family masked (per-family marginal skill). `attribution` — ANALYTIC from
lift_vectors (catch-all deleted; empty vectors excluded, never defaulted). `neg_control` + `discovery`
retained. `tail_only` — retrodiction over the salience tail alone (the Ranking Doctrine's falsifier).

## Step 3 — mi_gunanaka v2 + unification
Hierarchical shrinkage (cell → family → global pooling, weights ∝ n; at n=0 posterior = classical prior)
replaces n-gates; 3× divergence cap KEPT. Versioned calibration snapshots. **Weight unification (C6):**
mi_kula._FAMILIES + mi_pariksha._DIM_WEIGHTS + mi_pramana dims all read brahma_class_priors — three
embedded sites deleted.

## Step 4 — Feedback wiring + governance organs
mi_adhilepa: two-key snapshot publication (key-1 = proposing executor, key-2 = Ācārya-Pratinidhi, both
logged in the Judgment Ledger); overlays flow to EXACTLY three sinks (bg_class_priors overlay · anchor
lift calibrations · triangulation tradition-weights) — never L1. record_outcome: auto-resolution scan of
open anchors vs new LEL entries. query_calibration v2: per-cell skill/n/CI/snapshot served. **Sensitivity
harness:** vary brahma_formula_constants within bounds → output-stability ranking recorded (which knobs
actually turn the instrument).

## Anti-goals
No LLM anywhere in scoring/adjudication. No golden question with lel_overlap in any training cell. No
uninspected REFUTED (attestation rule). No third weight source. One life must not rewrite the śāstra
(shrinkage + cap enforce this structurally).

## Exit gates
- [ ] the first honest skill table: technique-family × event-class × dasha-system cells with n, skill vs
      null, CIs — train/held-out split intact `[verify-against: db]`
- [ ] ≥1 family beats the null on held-out OR the null finding is published with equal prominence
- [ ] snapshot publication demonstrably + reversibly changes served weights under two-key
      `[verify-against: prod]`
- [ ] LLM-free audit: scoring-path grep clean `[verify-against: repo]`
- [ ] tail-only retrodiction result recorded (does the tail carry independent skill?)
- [ ] sensitivity ranking of registry constants recorded; golden-eval non-regression
