# Shard: reference_vargas (FUSED Lane 1b + Lane 5)

channel: truly-UNREACHABLE
families_total: 1 | members_sampled: 1 (sole family) | per_family_rows_written: 1
heterogeneity_escalated: false

## Channel check (E-6)
- DB truth: `SELECT count(*) FROM reference_vargas` → 19 (matches ledger family_key `__table_row_count__=19`).
- Serving-tool search (no wire probe possible):
  - `grep CAPABILITY_MANIFEST.json` → no hit.
  - `grep platform/src/lib/retrieval` for `reference_vargas` → no hit.
  - `grep platform/src platform/python-sidecar` for `from reference_vargas` → no serving hit.
  - NOTE: chart-specific varga placements are served via divisional_query / chart_facts_query, but the reference varga-definition CATALOG (D1..D60 metadata) is not retrievable over the wire.
- Verdict: global L0 catalog, no chart_id; NO tool serves the catalog table. Class 1 UNREACHABLE.

## Per-family rows
| family_key | channel | retrievability_verdict | fidelity_verdict | derivation |
|---|---|---|---|---|
| `__table_row_count__=19` | truly-UNREACHABLE | UNREACHABLE (no MCP tool serves reference_vargas catalog; class 1) | N/A — no wire value (unreachable, cannot probe) | path-grade sole-family (exemplar=`__table_row_count__=19`); family_count=1, member==exemplar |
