# Shard: reference_yogas (FUSED Lane 1b + Lane 5)

channel: truly-UNREACHABLE
families_total: 1 | members_sampled: 1 (sole family) | per_family_rows_written: 1
heterogeneity_escalated: false

## Channel check (E-6)
- DB truth: `SELECT count(*) FROM reference_yogas` → 175 (matches ledger family_key `__table_row_count__=175`).
- Serving-tool search (no wire probe possible):
  - `grep CAPABILITY_MANIFEST.json` → no hit.
  - `grep platform/src/lib/retrieval` for `reference_yogas` → no hit (no MCP tool references it).
  - `grep platform/src platform/python-sidecar` for `from reference_yogas` → no serving hit.
  - NOTE: chart-specific yoga MEMBERSHIP is served via chart_facts_query (fact_key `yoga_label`) / cgm_graph_walk(DEAD). The 175-row reference yoga DEFINITION catalog itself has no retrieval path — an acharya-grade consumer cannot pull the classical yoga definition set.
- Verdict: global L0 catalog, no chart_id; NO tool serves the catalog table. Class 1 UNREACHABLE.

## Per-family rows
| family_key | channel | retrievability_verdict | fidelity_verdict | derivation |
|---|---|---|---|---|
| `__table_row_count__=175` | truly-UNREACHABLE | UNREACHABLE (no MCP tool serves reference_yogas definition catalog; class 1) | N/A — no wire value (unreachable, cannot probe) | path-grade sole-family (exemplar=`__table_row_count__=175`); family_count=1, member==exemplar |
