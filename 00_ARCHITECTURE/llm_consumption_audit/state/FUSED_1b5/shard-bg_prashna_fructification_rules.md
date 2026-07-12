# FUSED 1b+5 shard — bg_prashna_fructification_rules

| family_key | channel | retrievability_verdict | fidelity_verdict | derivation |
|---|---|---|---|---|
| `__table_row_count__=5` | served-only-by-down-pipeline | NOT-RETRIEVABLE via surgical LLM surface — no MCP primitive exposes this L0 Prashna catalog; reachable only through down-pipeline (`ga_prashna_writer` + `/api/prashna` product route consume `bg_prashna_*` → `ga_prashna_judgment`). | N/A (no wire probe — no reachable surgical tool) | full per-family (single-family table) |

## Evidence
- DB truth: `SELECT count(*) FROM bg_prashna_fructification_rules` → 5 (matches family_key).
- Surgical-tool check: absent from ALIVE-14 and DEAD-19 lists; no `*prashna*` MCP primitive in `platform/src/lib/mcp` / `platform/src/app/api/mcp`.
- Serving code (down-pipeline): `ga_writers/ga_prashna_writer.py`, `brahmagyan/l0_prashna.py`, product route `platform/src/app/api/prashna/route.ts`. Consumed only when a Prashna question is submitted; never surfaced to the natal-chart LLM consumption layer.
- Class: Lane-1b retrievability gap. Severity: medium (remediation quick-win).
