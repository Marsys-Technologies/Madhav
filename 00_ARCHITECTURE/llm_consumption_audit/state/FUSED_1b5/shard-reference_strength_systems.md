# Shard: reference_strength_systems (FUSED Lane 1b + Lane 5)

channel: truly-UNREACHABLE
families_total: 1 | members_sampled: 1 (sole family) | per_family_rows_written: 1
heterogeneity_escalated: false

## Channel check (E-6)
- DB truth: `SELECT count(*) FROM reference_strength_systems` → 33 (matches ledger family_key `__table_row_count__=33`).
- Serving-tool search (no wire probe possible — nothing to call):
  - `grep CAPABILITY_MANIFEST.json` for table name → no hit.
  - `grep platform/src/lib/retrieval` for `reference_strength_systems` → no hit (no MCP tool references it).
  - `grep platform/src platform/python-sidecar` for `from reference_strength_systems` → no serving-code hit.
- Verdict: global L0 catalog, no chart_id; NO surgical tool and NO full-pipeline tool serves this table to a consuming LLM. Class 1 UNREACHABLE (by nonexistence of any serving path). Consumed only as internal build-time reference vocabulary.

## Per-family rows
| family_key | channel | retrievability_verdict | fidelity_verdict | derivation |
|---|---|---|---|---|
| `__table_row_count__=33` | truly-UNREACHABLE | UNREACHABLE (no MCP tool serves reference_strength_systems; class 1) | N/A — no wire value (unreachable, cannot probe) | path-grade sole-family (exemplar=`__table_row_count__=33`); family_count=1, member==exemplar |
