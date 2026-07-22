---
artifact: ADJUDICATION_QUEUE.md
canonical_id: RETRIEVAL_ADJUDICATION_QUEUE
version: 1.0
status: GENERATED — one row per discrepancy, proposed dispositions pending native/conductor ruling
generated_at: 2026-07-22T19:40:56.324Z
generator: platform/scripts/harvest/cross_diff_adjudication.ts (W1 Lane L1b, W-25)
---

# Adjudication Queue — Retrieval Plane Harvest Pipeline (W1 Lane L1b)

Cross-diff of E1 (declared: live `getCatalog()` registry + static SQL table_hint scan) against E2 (actual: live `information_schema` + row counts) and E3 (chart_facts `fact_category` reconciliation across 4 real sources). Every row below is a real, mechanically-produced discrepancy — not hand-curated. Dispositions are PROPOSED, not ratified; `NEEDS-OWNER` is the honest default wherever the evidence does not clearly support a stronger claim.

**Caveat (read before triaging DARK rows):** E1's table_hint only scans TS registry source. A large share of L0 `bg_*` reference tables and other compute-plane data are read from `platform/python-sidecar` (Python), which this scan cannot see. A DARK row means "no TS-registry capability route found", not "provably unreachable by any means".

## Summary

```json
{
  "dark_count": 42,
  "drift_count": 1,
  "fact_category_gap_rows": 3,
  "dark_by_layer": {
    "L0": 5,
    "L2": 13,
    "L1": 8,
    "L3": 3,
    "L5": 13
  },
  "dark_by_proposed_disposition": {
    "INTERNAL-BY-DESIGN": 12,
    "NEEDS-OWNER": 30
  }
}
```

## DARK — real table, no declared TS-registry capability route

| ID | Table | Layer | Rows | Method | Proposed | Rationale (short) |
|---|---|---|---:|---|---|---|
| DARK-001 | `bg_dignity_reference` | L0 | 9 | exact | INTERNAL-BY-DESIGN | bg_* table name matches an internal reference/rule/threshold-table pattern — L0 Brahmagyan reference tables of this shape are typically consumed as computation INPUTS by the Python sidecar (ga_*/panchanga/transit engines), not served directly as a retrieval concept. |
| DARK-002 | `bg_transit_rules` | L0 | 57 | exact | INTERNAL-BY-DESIGN | bg_* table name matches an internal reference/rule/threshold-table pattern — L0 Brahmagyan reference tables of this shape are typically consumed as computation INPUTS by the Python sidecar (ga_*/panchanga/transit engines), not served directly as a retrieval concept. |
| DARK-003 | `bodha_anomalies` | L2 | 4954 | exact | NEEDS-OWNER | Table exists, holds 4954 row(s) (exact), and no capability's static table_hint references it. |
| DARK-004 | `bodha_cdlm_chart_summary` | L2 | 10 | exact | NEEDS-OWNER | Table exists, holds 10 row(s) (exact), and no capability's static table_hint references it. |
| DARK-005 | `bodha_cdlm_domain_rollups` | L2 | 60 | exact | NEEDS-OWNER | Table exists, holds 60 row(s) (exact), and no capability's static table_hint references it. |
| DARK-006 | `bodha_cdlm_evolution_gradients` | L2 | 0 | exact | NEEDS-OWNER | Table exists and no capability's static table_hint references it, AND it currently holds zero rows on the live chart. |
| DARK-007 | `bodha_cdlm_pattern_clusters` | L2 | 10 | exact | NEEDS-OWNER | Table exists, holds 10 row(s) (exact), and no capability's static table_hint references it. |
| DARK-008 | `bodha_cgm_chart_topology_summary` | L2 | 10 | exact | NEEDS-OWNER | Table exists, holds 10 row(s) (exact), and no capability's static table_hint references it. |
| DARK-009 | `bodha_cgm_edges` | L2 | 1573 | exact | NEEDS-OWNER | Table exists, holds 1573 row(s) (exact), and no capability's static table_hint references it. |
| DARK-010 | `bodha_cgm_nodes` | L2 | 649 | exact | NEEDS-OWNER | Table exists, holds 649 row(s) (exact), and no capability's static table_hint references it. |
| DARK-011 | `bodha_cgm_sub_graphs` | L2 | 10 | exact | NEEDS-OWNER | Table exists, holds 10 row(s) (exact), and no capability's static table_hint references it. |
| DARK-012 | `bodha_contradictions` | L2 | 23 | exact | NEEDS-OWNER | Table exists, holds 23 row(s) (exact), and no capability's static table_hint references it. |
| DARK-013 | `bodha_convergence` | L2 | 60 | exact | NEEDS-OWNER | Table exists, holds 60 row(s) (exact), and no capability's static table_hint references it. |
| DARK-014 | `bodha_signal_embeddings` | L2 | 85997 | estimate | NEEDS-OWNER | Table exists, holds 85997 row(s) (estimate), and no capability's static table_hint references it. |
| DARK-015 | `bodha_spine_bundles` | L2 | 0 | exact | NEEDS-OWNER | Table exists and no capability's static table_hint references it, AND it currently holds zero rows on the live chart. |
| DARK-016 | `brahma_activity_ontology` | L0 | 12 | exact | NEEDS-OWNER | Table exists, holds 12 row(s) (exact), and no capability's static table_hint references it. |
| DARK-017 | `brahma_event_ontology` | L0 | 27 | exact | NEEDS-OWNER | Table exists, holds 27 row(s) (exact), and no capability's static table_hint references it. |
| DARK-018 | `brahma_prospective_ledger` | L0 | 7 | exact | NEEDS-OWNER | Table exists, holds 7 row(s) (exact), and no capability's static table_hint references it. |
| DARK-019 | `chart_facts_history` | L1 | 0 | exact | INTERNAL-BY-DESIGN | Table name suffix matches an internal-bookkeeping/audit-trail pattern (_history) — these tables typically back an already-served table's history/staging/cache, not a distinct retrieval concept of their own. |
| DARK-020 | `chart_facts_supersedence` | L1 | 0 | exact | INTERNAL-BY-DESIGN | Table name suffix matches an internal-bookkeeping/audit-trail pattern (_supersedence) — these tables typically back an already-served table's history/staging/cache, not a distinct retrieval concept of their own. |
| DARK-021 | `chart_grants` | L1 | 9 | exact | NEEDS-OWNER | Table exists, holds 9 row(s) (exact), and no capability's static table_hint references it. |
| DARK-022 | `chart_panchanga` | L1 | 0 | exact | NEEDS-OWNER | Table exists and no capability's static table_hint references it, AND it currently holds zero rows on the live chart. |
| DARK-023 | `chart_panchanga_cache` | L1 | 0 | exact | INTERNAL-BY-DESIGN | Table name suffix matches an internal-bookkeeping/audit-trail pattern (_cache) — these tables typically back an already-served table's history/staging/cache, not a distinct retrieval concept of their own. |
| DARK-024 | `ga_prashna_judgment` | L1 | 5 | exact | NEEDS-OWNER | Table exists, holds 5 row(s) (exact), and no capability's static table_hint references it. |
| DARK-025 | `ganita_dashas` | L1 | 0 | exact | NEEDS-OWNER | Table exists and no capability's static table_hint references it, AND it currently holds zero rows on the live chart. |
| DARK-026 | `ganita_graha_sthana` | L1 | 0 | exact | NEEDS-OWNER | Table exists and no capability's static table_hint references it, AND it currently holds zero rows on the live chart. |
| DARK-027 | `kala_activation_predicates` | L3 | 78996 | estimate | NEEDS-OWNER | Table exists, holds 78996 row(s) (estimate), and no capability's static table_hint references it. |
| DARK-028 | `kala_convergence_staging` | L3 | 0 | exact | INTERNAL-BY-DESIGN | Table name suffix matches an internal-bookkeeping/audit-trail pattern (_staging) — these tables typically back an already-served table's history/staging/cache, not a distinct retrieval concept of their own. |
| DARK-029 | `kala_gochara_windows` | L3 | 3148 | exact | NEEDS-OWNER | Table exists, holds 3148 row(s) (exact), and no capability's static table_hint references it. |
| DARK-030 | `mimamsa_adjudication_log` | L5 | 0 | exact | INTERNAL-BY-DESIGN | Table name suffix matches an internal-bookkeeping/audit-trail pattern (_log) — these tables typically back an already-served table's history/staging/cache, not a distinct retrieval concept of their own. |
| DARK-031 | `mimamsa_anchor_adjustment` | L5 | 384 | exact | NEEDS-OWNER | Table exists, holds 384 row(s) (exact), and no capability's static table_hint references it. |
| DARK-032 | `mimamsa_calibration_snapshot` | L5 | 0 | exact | INTERNAL-BY-DESIGN | Table name suffix matches an internal-bookkeeping/audit-trail pattern (_snapshot) — these tables typically back an already-served table's history/staging/cache, not a distinct retrieval concept of their own. |
| DARK-033 | `mimamsa_convergence_adjustment` | L5 | 1000 | exact | NEEDS-OWNER | Table exists, holds 1000 row(s) (exact), and no capability's static table_hint references it. |
| DARK-034 | `mimamsa_event_provenance` | L5 | 57 | exact | NEEDS-OWNER | Table exists, holds 57 row(s) (exact), and no capability's static table_hint references it. |
| DARK-035 | `mimamsa_export_log` | L5 | 0 | exact | INTERNAL-BY-DESIGN | Table name suffix matches an internal-bookkeeping/audit-trail pattern (_log) — these tables typically back an already-served table's history/staging/cache, not a distinct retrieval concept of their own. |
| DARK-036 | `mimamsa_fact_adjustment` | L5 | 121100 | estimate | NEEDS-OWNER | Table exists, holds 121100 row(s) (estimate), and no capability's static table_hint references it. |
| DARK-037 | `mimamsa_negative_controls` | L5 | 4 | exact | NEEDS-OWNER | Table exists, holds 4 row(s) (exact), and no capability's static table_hint references it. |
| DARK-038 | `mimamsa_pool_contributions` | L5 | 0 | exact | INTERNAL-BY-DESIGN | Table name suffix matches an internal-bookkeeping/audit-trail pattern (_contributions) — these tables typically back an already-served table's history/staging/cache, not a distinct retrieval concept of their own. |
| DARK-039 | `mimamsa_preferences` | L5 | 0 | exact | NEEDS-OWNER | Table exists and no capability's static table_hint references it, AND it currently holds zero rows on the live chart. |
| DARK-040 | `mimamsa_resonance_feedback` | L5 | 0 | exact | INTERNAL-BY-DESIGN | Table name suffix matches an internal-bookkeeping/audit-trail pattern (_feedback) — these tables typically back an already-served table's history/staging/cache, not a distinct retrieval concept of their own. |
| DARK-041 | `mimamsa_signal_adjustment` | L5 | 97504 | estimate | NEEDS-OWNER | Table exists, holds 97504 row(s) (estimate), and no capability's static table_hint references it. |
| DARK-042 | `mimamsa_snapshot_cosign` | L5 | 0 | exact | INTERNAL-BY-DESIGN | Table name suffix matches an internal-bookkeeping/audit-trail pattern (_cosign) — these tables typically back an already-served table's history/staging/cache, not a distinct retrieval concept of their own. |

## DRIFT — declared table_hint with no matching real table

| ID | Declared table | Declaring capabilities | Proposed | Rationale |
|---|---|---|---|---|
| DRIFT-001 | `events` | marsys://tool/L5/mechanism_retrodiction_get | NEEDS-OWNER | Either a genuinely stale/renamed table reference in the capability's SQL, or a static-scan false positive (regex over-match). Needs a human read of the capability's actual SQL to confirm which. |

## FACT_CATEGORY_GAP — chart_facts category reconciliation (from E3)

| ID | Description | Count | Sample | Proposed | Full list |
|---|---|---:|---|---|---|
| FCAT-001 | fact_category values live in chart_facts but absent from CHART_FACTS_SCHEMA.json (canonical governance copy) | 144 | anumukha_shani_period, ardha_ashtama_shani_period, ashtakavarga_bindu_per_varga, ashtakavarga_bindu_sign, ashtakavarga_kakshya_boundary, ashtakavarga_pinda_raasi, … | NEEDS-OWNER | `e3_fact_category_reconciliation.json .reconciliation.live_db_categories_not_in_schema_json` |
| FCAT-002 | fact_category values live in chart_facts but absent from coverage_matrix.ts CHART_FACTS_CATEGORIES (the TS retrieval registry's enum) | 55 | aspect_received_by_special_point, ayurdaya, bhava_cusps, bhava_significance_link, chart_center_of_gravity, chart_cluster, … | NEEDS-OWNER | `e3_fact_category_reconciliation.json .reconciliation.live_db_categories_not_in_coverage_matrix` |
| FCAT-003 | fact_category declared in coverage_matrix.ts but never populated live (0 rows on the native chart for every value in this set) | 6 | ashtakavarga_anubindu, dosha_fires, esoteric_point_chatushphuta, esoteric_point_panchasphuta, esoteric_point_trisphuta, yoga_fires | NEEDS-OWNER | `e3_fact_category_reconciliation.json .reconciliation.coverage_matrix_categories_never_populated_live` |

## Disposition legend

- **SERVED** — a live capability reaches this concept; no action needed.
- **INTERNAL-BY-DESIGN** — deliberately unserved (backend computation input, audit/bookkeeping table).
- **RETIRED** — dead/superseded; safe to ignore or formally retire.
- **NEEDS-OWNER** — the honest default: evidence does not yet support a confident disposition; needs a human/conductor ruling.

