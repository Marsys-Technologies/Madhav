# Shard: yoga_families (FUSED Lane 1b + Lane 5)

channel: truly-UNREACHABLE
families_total: 1 | members_sampled: 1 (sole family) | per_family_rows_written: 1
heterogeneity_escalated: false

## Channel check (E-6)
- DB truth: `SELECT count(*) FROM yoga_families` → 0 (EMPTY table; matches ledger family_key `__table_row_count__=0`).
- Serving-tool search (no wire probe possible):
  - `grep CAPABILITY_MANIFEST.json` → no hit.
  - `grep platform/src/lib/retrieval` for `yoga_families` → no hit.
  - `grep platform/src platform/python-sidecar` for `yoga_families` → no serving hit.
- DOUBLE gap: (a) table is EMPTY at the data plane (0 rows — unpopulated L0 catalog / empty shell) AND (b) NO tool serves it. Even if a serving path existed it would return nothing.
- Verdict: truly-UNREACHABLE + data-plane empty. Primary class 1 UNREACHABLE (no serving path); secondary class 4 EMPTY SHELL (0 rows written by any writer).

## Per-family rows
| family_key | channel | retrievability_verdict | fidelity_verdict | derivation |
|---|---|---|---|---|
| `__table_row_count__=0` | truly-UNREACHABLE | UNREACHABLE (no MCP tool serves yoga_families; AND table is empty at data plane, 0 rows; class 1 + class 4) | N/A — no wire value (unreachable + empty, cannot probe) | path-grade sole-family (exemplar=`__table_row_count__=0`); family_count=1, member==exemplar |
