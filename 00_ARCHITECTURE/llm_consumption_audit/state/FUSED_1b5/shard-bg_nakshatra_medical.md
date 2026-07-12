# FUSED 1b+5 shard — bg_nakshatra_medical

| family_key | channel | retrievability_verdict | fidelity_verdict | derivation |
|---|---|---|---|---|
| `__table_row_count__=27` | served-only-by-down-pipeline | NOT-RETRIEVABLE via surgical LLM surface — no MCP primitive exposes this L0 catalog; reachable only through down-pipeline (`ga_medical_writer` consumes `bg_nakshatra_medical` → `ga_medical` L1 asset at build time). | N/A (no wire probe — no reachable surgical tool) | full per-family (single-family table) |

## Evidence
- DB truth: `SELECT count(*) FROM bg_nakshatra_medical` → 27 (matches family_key).
- Surgical-tool check: table name absent from ALIVE-14 and DEAD-19 surgical tool lists; no `*medical*`/`*nakshatra*` primitive in `platform/src/lib/mcp` / `platform/src/app/api/mcp`.
- Serving code exists (down-pipeline): `platform/python-sidecar/ga_writers/ga_medical_writer.py`, `brahmagyan/l0_medical.py`. No LLM-facing retrieval tool.
- Class: Lane-1b retrievability gap (reference catalog un-exposed to consumption surface). Severity: medium (remediation quick-win — data + serving code exist).
