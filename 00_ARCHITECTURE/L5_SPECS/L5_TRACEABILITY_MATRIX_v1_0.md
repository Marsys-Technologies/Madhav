---
artifact: L5_TRACEABILITY_MATRIX_v1_0.md
canonical_id: L5_TRACEABILITY_MATRIX
version: 1.0
status: CURRENT — the coverage checklist: every L5 insight/decision/gate mapped to its owning asset
authored_by: Cowork 2026-06-23
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
role: >
  The master coverage guarantee for the L5 per-asset spec pack. Every insight item (G1–G7, R1–R6), every
  ratified decision, every seal gate, every lifecycle/control rule is mapped to the asset(s) that own it.
  Each per-asset spec is reviewed against this matrix; the final coverage audit re-walks it to confirm
  ZERO orphans. If an item is not assigned here, it is visibly missing.
sibling_specs_dir: 00_ARCHITECTURE/L5_SPECS/
---

# L5 — Insight → Asset Traceability Matrix

> Read this as the checklist. Columns: **item** · **source artifact** · **owning asset(s)** · **status**
> (✅ assigned). Every spec in `L5_SPECS/` must satisfy its assigned rows. The final audit re-checks all.

## The L5 asset set (13: 10 data + 1 implicit-in-services pref + 2 services; insight assets added)

| # | asset | kind | activation | one-line |
|---|---|---|---|---|
| 1 | `mi_jivanaghatana` | data | v1 | clean-evidence vault + leakage firewall (LEL) |
| 2 | `mi_kula` | data | v1 | signal-family registry + negative-control battery |
| 3 | `mi_bhavisya` | data | v1 | prediction registry: frozen bundle + manifestation_set |
| 4 | `mi_pramana` | data | v1 | matcher + multi-dimensional scorecard + calibration |
| 5 | `mi_gunanaka` | data | v1 | learned-weight register (LL.1 + LL.2–8 structure) |
| 6 | `mi_adhilepa` | data | v1 | overlay surface + propagation + load-bearing map |
| 7 | `mi_pariksha` | data | v1 core + tiered | attribution + neg-control harness + DISCOVERY ENGINE (G1/G4/G5/G7) |
| 8 | `mi_sambandha` ⭐ | data | v1 | manifestation grammar (G2) |
| 9 | `mi_darshana` ⭐ | data | v1 | THE INSIGHT-RETRIEVAL SURFACE (R1–R6) |
| 10 | `mi_vistara` | data | v1 | export-integrity ledger |
| 11 | `mi_seva` ⭐ | service | v1 | serve-time apply (effective-value, toggles, transit-current) |
| 12 | `mi_abhilekha` ⭐ | service | v1 | journal + re-sync (ingest, due-sweep, recompute) |

⭐ = added/promoted during the pre-build + insight reviews. (`mimamsa_preferences` table owned by `mi_seva`.)

---

## §A — Superhuman-insight gaps (G1–G7)

| item | source | owning asset | status |
|---|---|---|---|
| G1 emergent-law mining over outcome corpus | GAPS §1 | `mi_pariksha` (discovery engine) → surfaced via `mi_darshana` | ✅ |
| G2 personal manifestation grammar | GAPS §1 | **`mi_sambandha`** (consumes scorecard channel data from `mi_pramana`) | ✅ |
| G3 load-bearing / sensitivity map | GAPS §1 | `mi_adhilepa` (computes per-conclusion sensitivity) → surfaced via `mi_darshana` | ✅ |
| G4 empirical contradiction-dominance | GAPS §1 | `mi_pariksha` (discovery engine) | ✅ |
| G5 temporal rhythm / lead-lag mining | GAPS §1 | `mi_pariksha` (discovery engine, tiered) | ✅ |
| G6 external-family interaction value | GAPS §1 | `mi_kula` (interaction scoring) + `mi_pramana` (incremental-value calc) | ✅ |
| G7 residual-driven new candidate discovery | GAPS §1 | `mi_pariksha` (discovery engine, tiered, citation-gated) | ✅ |

## §B — Retrievability gaps (R1–R6) — the retrievable layer

| item | source | owning asset | status |
|---|---|---|---|
| R1 pre-composed insight surface | GAPS §2 | **`mi_darshana`** | ✅ |
| R2 insight embeddings | GAPS §2 | **`mi_darshana`** (deterministic embedding transform) | ✅ |
| R3 query-shaped views (per domain/horizon/lens) | GAPS §2 | **`mi_darshana`** | ✅ |
| R4 retrievable provenance chain (one unit) | GAPS §2 | **`mi_darshana`** (materializes chain from `mi_pramana`/`mi_adhilepa`) | ✅ |
| R5 trust-metadata on every retrieved unit | GAPS §2 | **`mi_darshana`** (confidence/n/leakage/freshness/empirical-vs-prior) | ✅ |
| R6 retrievable negative knowledge | GAPS §2 | **`mi_darshana`** (from `mi_kula` neg-controls + `mi_gunanaka` suspended) | ✅ |

## §C — Calibration comparison model (the scoring core)

| item | source | owning asset | status |
|---|---|---|---|
| Full frozen prediction bundle | COMPARISON §2 | `mi_bhavisya` | ✅ |
| manifestation_set (hybrid classical+citation-gated LLM, frozen) | COMPARISON §5A | `mi_bhavisya` (generates) ; `mi_kula` (classical source) | ✅ |
| Deterministic many-to-many matcher | COMPARISON §4 | `mi_pramana` | ✅ |
| Multi-dimensional scorecard (timing/magnitude/domain/falsifier/manifestation→composite) | COMPARISON §3+§5A | `mi_pramana` | ✅ |
| Falsifier-as-judge (no confirmed without it) | COMPARISON §3 | `mi_pramana` | ✅ |
| Graded credit (literal full / alternate-cited partial / resonance-only) | COMPARISON §5A | `mi_pramana` | ✅ |
| Per-dimension + per-channel attribution | COMPARISON §5 | `mi_pariksha` | ✅ |
| base_rate adjustment (R-1) + seasonality null-models (R-2) | GAP_ANALYSIS | `mi_pramana` | ✅ |
| Reliability curves / Brier / ECE / meta-calibration (HC-2) | GAP_ANALYSIS | `mi_pramana` | ✅ |
| Held-out validity gate + min-n insufficient-evidence honesty (HC-4/B.12) | GAP_ANALYSIS | `mi_pramana` (gate) ; `mi_jivanaghatana` (held-out partition) | ✅ |
| Pre-registration admissibility (HC-5/§3.5.E) | GAP_ANALYSIS | `mi_bhavisya` (emitted_at) ; `mi_pramana` (admissibility check) | ✅ |
| No post-hoc manifestation-set widening | COMPARISON §5A | `mi_bhavisya` (freeze) ; `mi_pramana` (enforce) | ✅ |

## §D — Learning propagation (overlay / dedup / bounds / toggle)

| item | source | owning asset | status |
|---|---|---|---|
| Overlay model (base never mutated; strict segregation) | PROPAGATION §3 | `mi_adhilepa` | ✅ |
| 4 overlay tables (fact/signal/convergence/anchor) | PROPAGATION §3 | `mi_adhilepa` | ✅ |
| Single-origin attribution (dedup; no double-count) | PROPAGATION §4 | `mi_adhilepa` | ✅ |
| Bounded + evidence-scaled modulation | PROPAGATION §5 | `mi_adhilepa` (applies) ; `mi_gunanaka` (weight source) | ✅ |
| L1→L4 propagation, NEVER L0 | PROPAGATION §1 | `mi_adhilepa` | ✅ |
| Two-key lock (gate-passed AND high-confidence) | ELEVATION F (V4) | `mi_adhilepa` (apply) ; `mi_gunanaka` (gate) | ✅ |
| Effective-value cached views (P3) | PROPAGATION + GAP | `mi_seva` (serves) ; `mi_adhilepa` (source) | ✅ |

## §E — Contribution control (user governance)

| item | source | owning asset | status |
|---|---|---|---|
| Channel registry + resolver (per-request→saved→system-ON) | CONTRIBUTION §3 | `mi_seva` | ✅ |
| lel_citation gate (suppress literal LEL when off) | CONTRIBUTION §5 | `mi_seva` | ✅ |
| learning_influence gate (base vs effective) | CONTRIBUTION §5 | `mi_seva` | ✅ |
| Per-family + tier-group + soundness_basis controls | ELEVATION C | `mi_seva` (controls) ; `mi_kula` (family defs) | ✅ |
| Conversational defaults (LLM asks, sets session defaults) | ELEVATION F (C2) | `mi_seva` | ✅ |
| MCP optional args + parity-gate extension | CONTRIBUTION §4 | `mi_seva` | ✅ |
| contribution_state metadata + provenance endpoint | CONTRIBUTION §6 | `mi_seva` (state) ; `mi_darshana` (provenance) | ✅ |
| Preference store | ELEVATION + ASSET_ARCH | `mi_seva` (owns `mimamsa_preferences`) | ✅ |

## §F — Lifecycle, external families, honesty

| item | source | owning asset | status |
|---|---|---|---|
| Build-end trigger (DAG last) | ELEVATION A.2 | all data assets (orchestrator) | ✅ |
| LEL-update incremental recompute (L5-only, debounced) | ELEVATION A.2 | `mi_abhilekha` | ✅ |
| Prediction-due sweep (C-3) | GAP_ANALYSIS | `mi_abhilekha` | ✅ |
| Freshness marker (lel_version/last_calibrated_at) | ELEVATION A.2 | `mi_abhilekha` (writes) ; `mi_darshana` (surfaces) | ✅ |
| No-LEL structural-prior-only mode | ELEVATION A.3 | `mi_pramana` (mode) ; `mi_seva` (reports) | ✅ |
| External-family catalog (X-PHOTO/X-GEOMAG/T-NAKPADA + tiers) | ELEVATION B | `mi_kula` | ✅ |
| Negative-control battery (blocking seal gate, CONTROL_ONLY) | ELEVATION E3 | `mi_kula` (defs) ; `mi_pariksha` (harness, blocks) | ✅ |
| Learning-eligible behind hard gate (E1) + very-strict n-aware promotion (E2) | ELEVATION E | `mi_gunanaka` | ✅ |
| Transit-current binding (C-1) | GAP_ANALYSIS | `mi_seva` (calls L3 ka_* services) | ✅ |
| Governing principle: strict-unless-high-confidence; default restraint | ELEVATION F | ALL (cross-cutting) | ✅ |

## §G — Determinism + reliability seal gates

| item | source | owning asset / gate | status |
|---|---|---|---|
| No-LLM-in-L5 compute (D-1) | GAP_ANALYSIS | ALL data assets (CI gate) | ✅ |
| Frozen versioned formulas (D-2) | GAP_ANALYSIS | `mi_pramana`/`mi_adhilepa` (formula registry) | ✅ |
| Pinned external-data snapshots (D-3) | GAP_ANALYSIS | `mi_kula` (geomag/sunspot/ephemeris pins) | ✅ |
| Reproducibility (RL-1) — byte-identical re-run | GAP_ANALYSIS | seal gate (all) | ✅ |
| OFF==baseline (RL-2) | PROPAGATION §6 | seal gate (`mi_seva` path) | ✅ |
| Double-count path test (RL) | PROPAGATION §4 | seal gate (`mi_adhilepa`) | ✅ |
| No-L0-touch test | PROPAGATION §1 | seal gate (`mi_adhilepa`) | ✅ |
| Degenerate-distribution guard (RL-6) | GAP_ANALYSIS + CROSSCHECK | `mi_pariksha` (harness) — all attribution cols | ✅ |
| Kill-switch + drift-alert (RL-4) | GAP_ANALYSIS | `mi_gunanaka` | ✅ |
| Integrity-substrate registration (RL-5) | GAP_ANALYSIS | ALL tables (drift_detector/schema_validator) | ✅ |
| Frozen orchestrator contract conformance | CAMPAIGN §4 | ALL writers | ✅ |

## §H — Upstream leverage (confirm each asset reads the right sources)

| layer | asset(s) consumed | by L5 asset |
|---|---|---|
| L4 | phala_pramana, phala_anchors, phala_phaladesa | mi_bhavisya |
| L3 | kala_convergence + ka_* services (transit-current) | mi_seva |
| L2 | bodha_msr_signals (keystone), embeddings, CDLM | mi_adhilepa (modulates), mi_darshana (embeds) |
| L1 | chart_facts, chart_dashas | mi_bhavisya, mi_pramana |
| L0 | bg_rules, significations, citations | mi_kula, mi_bhavisya (manifestation_set) |
| LEL | life_events | mi_jivanaghatana |

---

## Coverage status

All G1–G7 ✅ · all R1–R6 ✅ · calibration model ✅ · propagation ✅ · contribution control ✅ · lifecycle ✅
· determinism/seal gates ✅ · upstream leverage ✅. **No orphans at matrix-authoring time.** The final
coverage audit (last spec task) re-walks every row against the written specs to confirm each is actually
specified, not just assigned.

*End of L5_TRACEABILITY_MATRIX v1.0 — the coverage checklist for the per-asset spec pack.*
