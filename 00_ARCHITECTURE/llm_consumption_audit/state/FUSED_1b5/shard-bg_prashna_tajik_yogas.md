# FUSED 1b+5 shard — bg_prashna_tajik_yogas

| family_key | channel | retrievability_verdict | fidelity_verdict | derivation |
|---|---|---|---|---|
| `__table_row_count__=16` | served-only-by-down-pipeline | NOT-RETRIEVABLE via surgical LLM surface — no MCP primitive exposes this L0 Tajik-yoga catalog; reachable only through down-pipeline (`ga_prashna_writer` + `/api/prashna` product route). Note: `query_varshaphala` (ALIVE) serves per-chart varshaphala assets, NOT this bg_ reference catalog. | N/A (no wire probe — no reachable surgical tool) | full per-family (single-family table) |

## Evidence
- DB truth: `SELECT count(*) FROM bg_prashna_tajik_yogas` → 16 (matches family_key).
- Surgical-tool check: absent from ALIVE-14 and DEAD-19 lists; no `*prashna*`/`*tajik*` MCP primitive. `query_varshaphala` does not read this reference table.
- Serving code (down-pipeline): `ga_writers/ga_prashna_writer.py`, `brahmagyan/l0_prashna.py`, `platform/src/app/api/prashna/route.ts`.
- Class: Lane-1b retrievability gap. Severity: medium (remediation quick-win).
