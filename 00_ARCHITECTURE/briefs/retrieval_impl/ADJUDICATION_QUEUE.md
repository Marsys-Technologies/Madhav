---
artifact: ADJUDICATION_QUEUE.md
canonical_id: RETRIEVAL_ADJUDICATION_QUEUE
version: 1.0
status: GENERATED — one row per discrepancy, proposed dispositions pending native/conductor ruling
generated_at: 2026-07-19T20:35:30.199Z
generator: platform/scripts/harvest/cross_diff_adjudication.ts (W1 Lane L1b, W-25)
---

# Adjudication Queue — Retrieval Plane Harvest Pipeline (W1 Lane L1b)

Cross-diff of E1 (declared: live `getCatalog()` registry + static SQL table_hint scan) against E2 (actual: live `information_schema` + row counts) and E3 (chart_facts `fact_category` reconciliation across 4 real sources). Every row below is a real, mechanically-produced discrepancy — not hand-curated. Dispositions are PROPOSED, not ratified; `NEEDS-OWNER` is the honest default wherever the evidence does not clearly support a stronger claim.

**Caveat (read before triaging DARK rows):** E1's table_hint only scans TS registry source. A large share of L0 `bg_*` reference tables and other compute-plane data are read from `platform/python-sidecar` (Python), which this scan cannot see. A DARK row means "no TS-registry capability route found", not "provably unreachable by any means".

## Summary

```json
{
  "dark_count": 77,
  "drift_count": 0,
  "fact_category_gap_rows": 3,
  "dark_by_layer": {
    "L0": 29,
    "L2": 16,
    "L1": 10,
    "L3": 3,
    "L5": 19
  },
  "dark_by_proposed_disposition": {
    "INTERNAL-BY-DESIGN": 25,
    "NEEDS-OWNER": 52
  }
}
```

## DARK — real table, no declared TS-registry capability route

| ID | Table | Layer | Rows | Method | Proposed | Rationale (short) |
|---|---|---|---:|---|---|---|
| DARK-001 | `bg_avastha_schemes` | L0 | 35 | exact | INTERNAL-BY-DESIGN | bg_* table name matches an internal reference/rule/threshold-table pattern — L0 Brahmagyan reference tables of this shape are typically consumed as computation INPUTS by the Python sidecar (ga_*/panchanga/transit engines), not served directly as a retrieval concept. |
| DARK-002 | `bg_combustion_orbs` | L0 | 8 | exact | INTERNAL-BY-DESIGN | bg_* table name matches an internal reference/rule/threshold-table pattern — L0 Brahmagyan reference tables of this shape are typically consumed as computation INPUTS by the Python sidecar (ga_*/panchanga/transit engines), not served directly as a retrieval concept. |
| DARK-003 | `bg_dignity_reference` | L0 | 9 | exact | INTERNAL-BY-DESIGN | bg_* table name matches an internal reference/rule/threshold-table pattern — L0 Brahmagyan reference tables of this shape are typically consumed as computation INPUTS by the Python sidecar (ga_*/panchanga/transit engines), not served directly as a retrieval concept. |
| DARK-004 | `bg_graha_dik` | L0 | 9 | exact | INTERNAL-BY-DESIGN | bg_* table name matches an internal reference/rule/threshold-table pattern — L0 Brahmagyan reference tables of this shape are typically consumed as computation INPUTS by the Python sidecar (ga_*/panchanga/transit engines), not served directly as a retrieval concept. |
| DARK-005 | `bg_graha_naisargika_friendship` | L0 | 72 | exact | INTERNAL-BY-DESIGN | bg_* table name matches an internal reference/rule/threshold-table pattern — L0 Brahmagyan reference tables of this shape are typically consumed as computation INPUTS by the Python sidecar (ga_*/panchanga/transit engines), not served directly as a retrieval concept. |
| DARK-006 | `bg_medical_mappings` | L0 | 21 | exact | INTERNAL-BY-DESIGN | bg_* table name matches an internal reference/rule/threshold-table pattern — L0 Brahmagyan reference tables of this shape are typically consumed as computation INPUTS by the Python sidecar (ga_*/panchanga/transit engines), not served directly as a retrieval concept. |
| DARK-007 | `bg_motion_state_thresholds` | L0 | 27 | exact | INTERNAL-BY-DESIGN | bg_* table name matches an internal reference/rule/threshold-table pattern — L0 Brahmagyan reference tables of this shape are typically consumed as computation INPUTS by the Python sidecar (ga_*/panchanga/transit engines), not served directly as a retrieval concept. |
| DARK-008 | `bg_nakshatra_medical` | L0 | 27 | exact | INTERNAL-BY-DESIGN | bg_* table name matches an internal reference/rule/threshold-table pattern — L0 Brahmagyan reference tables of this shape are typically consumed as computation INPUTS by the Python sidecar (ga_*/panchanga/transit engines), not served directly as a retrieval concept. |
| DARK-009 | `bg_prashna_fructification_rules` | L0 | 5 | exact | INTERNAL-BY-DESIGN | bg_* table name matches an internal reference/rule/threshold-table pattern — L0 Brahmagyan reference tables of this shape are typically consumed as computation INPUTS by the Python sidecar (ga_*/panchanga/transit engines), not served directly as a retrieval concept. |
| DARK-010 | `bg_prashna_lagna_methods` | L0 | 5 | exact | NEEDS-OWNER | Table exists, holds 5 row(s) (exact), and no capability's static table_hint references it. |
| DARK-011 | `bg_prashna_significators` | L0 | 12 | exact | NEEDS-OWNER | Table exists, holds 12 row(s) (exact), and no capability's static table_hint references it. |
| DARK-012 | `bg_prashna_special_techniques` | L0 | 3 | exact | NEEDS-OWNER | Table exists, holds 3 row(s) (exact), and no capability's static table_hint references it. |
| DARK-013 | `bg_prashna_tajik_yogas` | L0 | 16 | exact | NEEDS-OWNER | Table exists, holds 16 row(s) (exact), and no capability's static table_hint references it. |
| DARK-014 | `bg_shashtiamsha_deities` | L0 | 60 | exact | INTERNAL-BY-DESIGN | bg_* table name matches an internal reference/rule/threshold-table pattern — L0 Brahmagyan reference tables of this shape are typically consumed as computation INPUTS by the Python sidecar (ga_*/panchanga/transit engines), not served directly as a retrieval concept. |
| DARK-015 | `bg_transit_av_gates` | L0 | 8 | exact | NEEDS-OWNER | Table exists, holds 8 row(s) (exact), and no capability's static table_hint references it. |
| DARK-016 | `bg_transit_engine` | L0 | 9 | exact | NEEDS-OWNER | Table exists, holds 9 row(s) (exact), and no capability's static table_hint references it. |
| DARK-017 | `bg_transit_moorti` | L0 | 27 | exact | INTERNAL-BY-DESIGN | bg_* table name matches an internal reference/rule/threshold-table pattern — L0 Brahmagyan reference tables of this shape are typically consumed as computation INPUTS by the Python sidecar (ga_*/panchanga/transit engines), not served directly as a retrieval concept. |
| DARK-018 | `bg_transit_rules` | L0 | 57 | exact | INTERNAL-BY-DESIGN | bg_* table name matches an internal reference/rule/threshold-table pattern — L0 Brahmagyan reference tables of this shape are typically consumed as computation INPUTS by the Python sidecar (ga_*/panchanga/transit engines), not served directly as a retrieval concept. |
| DARK-019 | `bg_transit_vedha` | L0 | 33 | exact | INTERNAL-BY-DESIGN | bg_* table name matches an internal reference/rule/threshold-table pattern — L0 Brahmagyan reference tables of this shape are typically consumed as computation INPUTS by the Python sidecar (ga_*/panchanga/transit engines), not served directly as a retrieval concept. |
| DARK-020 | `bg_vastu_direction_remedials` | L0 | 24 | exact | INTERNAL-BY-DESIGN | bg_* table name matches an internal reference/rule/threshold-table pattern — L0 Brahmagyan reference tables of this shape are typically consumed as computation INPUTS by the Python sidecar (ga_*/panchanga/transit engines), not served directly as a retrieval concept. |
| DARK-021 | `bg_vastu_directions` | L0 | 8 | exact | INTERNAL-BY-DESIGN | bg_* table name matches an internal reference/rule/threshold-table pattern — L0 Brahmagyan reference tables of this shape are typically consumed as computation INPUTS by the Python sidecar (ga_*/panchanga/transit engines), not served directly as a retrieval concept. |
| DARK-022 | `bodha_anomalies` | L2 | 4954 | exact | NEEDS-OWNER | Table exists, holds 4954 row(s) (exact), and no capability's static table_hint references it. |
| DARK-023 | `bodha_cdlm_domain_rollups` | L2 | 60 | exact | NEEDS-OWNER | Table exists, holds 60 row(s) (exact), and no capability's static table_hint references it. |
| DARK-024 | `bodha_cdlm_evolution_gradients` | L2 | 0 | exact | NEEDS-OWNER | Table exists and no capability's static table_hint references it, AND it currently holds zero rows on the live chart. |
| DARK-025 | `bodha_cdlm_pattern_clusters` | L2 | 10 | exact | NEEDS-OWNER | Table exists, holds 10 row(s) (exact), and no capability's static table_hint references it. |
| DARK-026 | `bodha_cgm_chart_topology_summary` | L2 | 10 | exact | NEEDS-OWNER | Table exists, holds 10 row(s) (exact), and no capability's static table_hint references it. |
| DARK-027 | `bodha_cgm_edges` | L2 | 1573 | exact | NEEDS-OWNER | Table exists, holds 1573 row(s) (exact), and no capability's static table_hint references it. |
| DARK-028 | `bodha_cgm_nodes` | L2 | 649 | exact | NEEDS-OWNER | Table exists, holds 649 row(s) (exact), and no capability's static table_hint references it. |
| DARK-029 | `bodha_cgm_sub_graphs` | L2 | 10 | exact | NEEDS-OWNER | Table exists, holds 10 row(s) (exact), and no capability's static table_hint references it. |
| DARK-030 | `bodha_contradictions` | L2 | 23 | exact | NEEDS-OWNER | Table exists, holds 23 row(s) (exact), and no capability's static table_hint references it. |
| DARK-031 | `bodha_convergence` | L2 | 60 | exact | NEEDS-OWNER | Table exists, holds 60 row(s) (exact), and no capability's static table_hint references it. |
| DARK-032 | `bodha_rm_chart_summary` | L2 | 10 | exact | NEEDS-OWNER | Table exists, holds 10 row(s) (exact), and no capability's static table_hint references it. |
| DARK-033 | `bodha_rm_dasha_windowed_prescriptions` | L2 | 0 | exact | NEEDS-OWNER | Table exists and no capability's static table_hint references it, AND it currently holds zero rows on the live chart. |
| DARK-034 | `bodha_rm_dosha_remedy_bundles` | L2 | 0 | exact | NEEDS-OWNER | Table exists and no capability's static table_hint references it, AND it currently holds zero rows on the live chart. |
| DARK-035 | `bodha_rm_pattern_remedies` | L2 | 90 | exact | NEEDS-OWNER | Table exists, holds 90 row(s) (exact), and no capability's static table_hint references it. |
| DARK-036 | `bodha_signal_embeddings` | L2 | 85997 | estimate | NEEDS-OWNER | Table exists, holds 85997 row(s) (estimate), and no capability's static table_hint references it. |
| DARK-037 | `bodha_triangulation` | L2 | 200 | exact | NEEDS-OWNER | Table exists, holds 200 row(s) (exact), and no capability's static table_hint references it. |
| DARK-038 | `brahma_activity_ontology` | L0 | 12 | exact | NEEDS-OWNER | Table exists, holds 12 row(s) (exact), and no capability's static table_hint references it. |
| DARK-039 | `brahma_class_priors` | L0 | 164 | exact | NEEDS-OWNER | Table exists, holds 164 row(s) (exact), and no capability's static table_hint references it. |
| DARK-040 | `brahma_compendium_index` | L0 | 9538 | exact | NEEDS-OWNER | Table exists, holds 9538 row(s) (exact), and no capability's static table_hint references it. |
| DARK-041 | `brahma_dasha_systems` | L0 | 18 | exact | NEEDS-OWNER | Table exists, holds 18 row(s) (exact), and no capability's static table_hint references it. |
| DARK-042 | `brahma_event_ontology` | L0 | 27 | exact | NEEDS-OWNER | Table exists, holds 27 row(s) (exact), and no capability's static table_hint references it. |
| DARK-043 | `brahma_formula_constants` | L0 | 18 | exact | NEEDS-OWNER | Table exists, holds 18 row(s) (exact), and no capability's static table_hint references it. |
| DARK-044 | `brahma_prospective_ledger` | L0 | 7 | exact | NEEDS-OWNER | Table exists, holds 7 row(s) (exact), and no capability's static table_hint references it. |
| DARK-045 | `brahma_vichara_constants` | L0 | 7 | exact | NEEDS-OWNER | Table exists, holds 7 row(s) (exact), and no capability's static table_hint references it. |
| DARK-046 | `chart_facts_history` | L1 | 0 | exact | INTERNAL-BY-DESIGN | Table name suffix matches an internal-bookkeeping/audit-trail pattern (_history) — these tables typically back an already-served table's history/staging/cache, not a distinct retrieval concept of their own. |
| DARK-047 | `chart_facts_supersedence` | L1 | 0 | exact | INTERNAL-BY-DESIGN | Table name suffix matches an internal-bookkeeping/audit-trail pattern (_supersedence) — these tables typically back an already-served table's history/staging/cache, not a distinct retrieval concept of their own. |
| DARK-048 | `chart_grants` | L1 | 9 | exact | NEEDS-OWNER | Table exists, holds 9 row(s) (exact), and no capability's static table_hint references it. |
| DARK-049 | `chart_panchanga` | L1 | 0 | exact | NEEDS-OWNER | Table exists and no capability's static table_hint references it, AND it currently holds zero rows on the live chart. |
| DARK-050 | `chart_panchanga_cache` | L1 | 0 | exact | INTERNAL-BY-DESIGN | Table name suffix matches an internal-bookkeeping/audit-trail pattern (_cache) — these tables typically back an already-served table's history/staging/cache, not a distinct retrieval concept of their own. |
| DARK-051 | `ga_condition_composite` | L1 | 90 | exact | NEEDS-OWNER | Table exists, holds 90 row(s) (exact), and no capability's static table_hint references it. |
| DARK-052 | `ga_prashna_judgment` | L1 | 5 | exact | NEEDS-OWNER | Table exists, holds 5 row(s) (exact), and no capability's static table_hint references it. |
| DARK-053 | `ga_prashna_lagna` | L1 | 5 | exact | NEEDS-OWNER | Table exists, holds 5 row(s) (exact), and no capability's static table_hint references it. |
| DARK-054 | `ganita_dashas` | L1 | 0 | exact | NEEDS-OWNER | Table exists and no capability's static table_hint references it, AND it currently holds zero rows on the live chart. |
| DARK-055 | `ganita_graha_sthana` | L1 | 0 | exact | NEEDS-OWNER | Table exists and no capability's static table_hint references it, AND it currently holds zero rows on the live chart. |
| DARK-056 | `kala_activation_predicates` | L3 | 78996 | estimate | NEEDS-OWNER | Table exists, holds 78996 row(s) (estimate), and no capability's static table_hint references it. |
| DARK-057 | `kala_convergence_staging` | L3 | 0 | exact | INTERNAL-BY-DESIGN | Table name suffix matches an internal-bookkeeping/audit-trail pattern (_staging) — these tables typically back an already-served table's history/staging/cache, not a distinct retrieval concept of their own. |
| DARK-058 | `kala_gochara_windows` | L3 | 5 | exact | NEEDS-OWNER | Table exists, holds 5 row(s) (exact), and no capability's static table_hint references it. |
| DARK-059 | `mimamsa_adjudication_log` | L5 | 0 | exact | INTERNAL-BY-DESIGN | Table name suffix matches an internal-bookkeeping/audit-trail pattern (_log) — these tables typically back an already-served table's history/staging/cache, not a distinct retrieval concept of their own. |
| DARK-060 | `mimamsa_anchor_adjustment` | L5 | 384 | exact | NEEDS-OWNER | Table exists, holds 384 row(s) (exact), and no capability's static table_hint references it. |
| DARK-061 | `mimamsa_attribution` | L5 | 0 | exact | NEEDS-OWNER | Table exists and no capability's static table_hint references it, AND it currently holds zero rows on the live chart. |
| DARK-062 | `mimamsa_calibration_snapshot` | L5 | 0 | exact | INTERNAL-BY-DESIGN | Table name suffix matches an internal-bookkeeping/audit-trail pattern (_snapshot) — these tables typically back an already-served table's history/staging/cache, not a distinct retrieval concept of their own. |
| DARK-063 | `mimamsa_convergence_adjustment` | L5 | 1000 | exact | NEEDS-OWNER | Table exists, holds 1000 row(s) (exact), and no capability's static table_hint references it. |
| DARK-064 | `mimamsa_discoveries` | L5 | 45 | exact | NEEDS-OWNER | Table exists, holds 45 row(s) (exact), and no capability's static table_hint references it. |
| DARK-065 | `mimamsa_event_provenance` | L5 | 57 | exact | NEEDS-OWNER | Table exists, holds 57 row(s) (exact), and no capability's static table_hint references it. |
| DARK-066 | `mimamsa_export_log` | L5 | 0 | exact | INTERNAL-BY-DESIGN | Table name suffix matches an internal-bookkeeping/audit-trail pattern (_log) — these tables typically back an already-served table's history/staging/cache, not a distinct retrieval concept of their own. |
| DARK-067 | `mimamsa_fact_adjustment` | L5 | 121100 | estimate | NEEDS-OWNER | Table exists, holds 121100 row(s) (estimate), and no capability's static table_hint references it. |
| DARK-068 | `mimamsa_insight_embeddings` | L5 | 0 | exact | NEEDS-OWNER | Table exists and no capability's static table_hint references it, AND it currently holds zero rows on the live chart. |
| DARK-069 | `mimamsa_journal` | L5 | 0 | exact | NEEDS-OWNER | Table exists and no capability's static table_hint references it, AND it currently holds zero rows on the live chart. |
| DARK-070 | `mimamsa_load_bearing` | L5 | 10 | exact | NEEDS-OWNER | Table exists, holds 10 row(s) (exact), and no capability's static table_hint references it. |
| DARK-071 | `mimamsa_manifestation_sets` | L5 | 384 | exact | NEEDS-OWNER | Table exists, holds 384 row(s) (exact), and no capability's static table_hint references it. |
| DARK-072 | `mimamsa_negative_controls` | L5 | 4 | exact | NEEDS-OWNER | Table exists, holds 4 row(s) (exact), and no capability's static table_hint references it. |
| DARK-073 | `mimamsa_pool_contributions` | L5 | 0 | exact | INTERNAL-BY-DESIGN | Table name suffix matches an internal-bookkeeping/audit-trail pattern (_contributions) — these tables typically back an already-served table's history/staging/cache, not a distinct retrieval concept of their own. |
| DARK-074 | `mimamsa_preferences` | L5 | 0 | exact | NEEDS-OWNER | Table exists and no capability's static table_hint references it, AND it currently holds zero rows on the live chart. |
| DARK-075 | `mimamsa_resonance_feedback` | L5 | 0 | exact | INTERNAL-BY-DESIGN | Table name suffix matches an internal-bookkeeping/audit-trail pattern (_feedback) — these tables typically back an already-served table's history/staging/cache, not a distinct retrieval concept of their own. |
| DARK-076 | `mimamsa_signal_adjustment` | L5 | 97504 | estimate | NEEDS-OWNER | Table exists, holds 97504 row(s) (estimate), and no capability's static table_hint references it. |
| DARK-077 | `mimamsa_snapshot_cosign` | L5 | 0 | exact | INTERNAL-BY-DESIGN | Table name suffix matches an internal-bookkeeping/audit-trail pattern (_cosign) — these tables typically back an already-served table's history/staging/cache, not a distinct retrieval concept of their own. |

## DRIFT — declared table_hint with no matching real table

**None found** (0 rows) — after tightening the static scan to backtick-delimited SQL only (excluding English-prose "from"/"join" false positives from doc comments and error-message strings), every table_hint the TS registry declares resolves to a real live table. This is a real, positive result, not an unexecuted check — see `e1_registry_extractor.ts`'s honesty notes for the false-positive class this eliminated (a naive FROM/JOIN regex over raw source, before the backtick restriction, produced 40 spurious "drift" hits, all English stopwords).

## FACT_CATEGORY_GAP — chart_facts category reconciliation (from E3)

| ID | Description | Count | Sample | Proposed | Full list |
|---|---|---:|---|---|---|
| FCAT-001 | fact_category values live in chart_facts but absent from CHART_FACTS_SCHEMA.json (canonical governance copy) | 144 | anumukha_shani_period, ardha_ashtama_shani_period, ashtakavarga_bindu_per_varga, ashtakavarga_bindu_sign, ashtakavarga_kakshya_boundary, ashtakavarga_pinda_raasi, … | NEEDS-OWNER | `e3_fact_category_reconciliation.json .reconciliation.live_db_categories_not_in_schema_json` |
| FCAT-002 | fact_category values live in chart_facts but absent from coverage_matrix.ts CHART_FACTS_CATEGORIES (the TS retrieval registry's enum) | 66 | ashtakavarga_bindu_per_varga, ashtakavarga_bindu_sign, ashtakavarga_ekadhipathya_shodhana, ashtakavarga_kakshya_boundary, ashtakavarga_pinda_raasi, ashtakavarga_pinda_sarva_per_varga, … | NEEDS-OWNER | `e3_fact_category_reconciliation.json .reconciliation.live_db_categories_not_in_coverage_matrix` |
| FCAT-003 | fact_category declared in coverage_matrix.ts but never populated live (0 rows on the native chart for every value in this set) | 6 | ashtakavarga_anubindu, dosha_fires, esoteric_point_chatushphuta, esoteric_point_panchasphuta, esoteric_point_trisphuta, yoga_fires | NEEDS-OWNER | `e3_fact_category_reconciliation.json .reconciliation.coverage_matrix_categories_never_populated_live` |

## Disposition legend

- **SERVED** — a live capability reaches this concept; no action needed.
- **INTERNAL-BY-DESIGN** — deliberately unserved (backend computation input, audit/bookkeeping table).
- **RETIRED** — dead/superseded; safe to ignore or formally retire.
- **NEEDS-OWNER** — the honest default: evidence does not yet support a confident disposition; needs a human/conductor ruling.

