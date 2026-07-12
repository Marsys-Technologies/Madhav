# Shard: reference_upagrahas (FUSED Lane 1b + Lane 5)

channel: truly-UNREACHABLE
families_total: 1 | members_sampled: 1 (sole family) | per_family_rows_written: 1
heterogeneity_escalated: false

## Channel check (E-6)
- DB truth: `SELECT count(*) FROM reference_upagrahas` → 11 (matches ledger family_key `__table_row_count__=11`).
- Serving-tool search (no wire probe possible):
  - `grep CAPABILITY_MANIFEST.json` → no hit.
  - `grep platform/src/lib/retrieval` for `reference_upagrahas` → no hit.
  - `grep platform/src platform/python-sidecar` for `from reference_upagrahas` → no serving hit.
  - NOTE: chart-specific upagraha PLACEMENTS are served via chart_facts_query (fact_category `upagraha`), but the reference CATALOG table itself is not retrievable.
- Verdict: global L0 catalog, no chart_id; NO tool serves the catalog table. Class 1 UNREACHABLE.

## Per-family rows
| family_key | channel | retrievability_verdict | fidelity_verdict | derivation |
|---|---|---|---|---|
| `__table_row_count__=11` | truly-UNREACHABLE | UNREACHABLE (no MCP tool serves reference_upagrahas catalog; class 1) | N/A — no wire value (unreachable, cannot probe) | path-grade sole-family (exemplar=`__table_row_count__=11`); family_count=1, member==exemplar |
