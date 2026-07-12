# FUSED 1b+5 shard — bg_prashna_significators

| family_key | channel | retrievability_verdict | fidelity_verdict | derivation |
|---|---|---|---|---|
| `__table_row_count__=12` | served-only-by-down-pipeline | NOT-RETRIEVABLE via surgical LLM surface — no MCP primitive exposes this L0 Prashna catalog; reachable only through down-pipeline (`ga_prashna_writer` reads `bg_prashna_significators` → `ga_prashna_judgment`; `/api/prashna` product route). | N/A (no wire probe — no reachable surgical tool) | full per-family (single-family table) |

## Evidence
- DB truth: `SELECT count(*) FROM bg_prashna_significators` → 12 (matches family_key).
- Direct consumption proof: `ga_writers/ga_prashna_writer.py:176` — `SELECT querent_planet, quesited_planet FROM bg_prashna_significators ...` (build-time only).
- Surgical-tool check: absent from ALIVE-14 and DEAD-19 lists; no `*prashna*` MCP primitive.
- Class: Lane-1b retrievability gap. Severity: medium (remediation quick-win).
