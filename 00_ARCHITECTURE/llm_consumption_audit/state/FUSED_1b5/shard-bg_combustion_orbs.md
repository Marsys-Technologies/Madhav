# FUSED Lane 1b+5 shard — bg_combustion_orbs (family_count=1)

## Channel classification
truly-UNREACHABLE. L0 global reference catalog (no chart_id). Not in CAPABILITY_MANIFEST tool-map; not in tool_registry; folded into asset `bg_dignity_reference` bundle but exposed by NO surgical primitive. Wire-confirmed: `read_asset`/`data_coverage` rejected — server surgical whitelist enumerates 40+ primitives, none serves an L0 reference catalog; only fallback is `ask_madhav` full-pipeline (surfaces derived per-chart combustion RESULT via chart_facts, never the orb-constant catalog).

## Per-family rows
| family_key | channel | retrievability_verdict | fidelity_verdict | derivation |
|---|---|---|---|---|
| `__table_row_count__=8` | truly-UNREACHABLE | UNREACHABLE (class 1) — 8-row orb-degree constant catalog served by no tool | N/A — nothing arrives over wire; no table-vs-wire diff possible, Lane-5 four failure modes cannot be exercised | single-family path; exemplar==sole member; full per-family (trivially exhaustive) |

## Evidence (E-6)
- DB-truth call: `SELECT count(*) FROM bg_combustion_orbs;` → `8` (matches ledger family_key `__table_row_count__=8`).
- Wire call: `POST /api/mcp/primitives/read_asset {"params":{"chart_id":"482012f1-...","asset_id":"bg_dignity_reference"}}` → `{"ok":false,"error":{"class":"validation","message":"Tool not in surgical whitelist: read_asset"}}`. Surgical whitelist verbatim contains no combustion/reference tool.
- Manifest/registry: `grep bg_combustion_orbs CAPABILITY_MANIFEST.json` → no match; `tool_registry` (20 enabled tools) → no serving tool.
- Mitigation note: derived per-chart combustion RESULT IS reachable via `query_chart_facts` (fact_category `combustion_relationship`, `combustion_per_varga`); only the abstract orb-constant catalog is unserved.

## Finding
- lane=1b, class=1 UNREACHABLE, severity=LOW. summary: L0 combustion-orb constant catalog (8 rows) has no MCP serving path; consumer can obtain the combustion verdict per-chart but cannot cite the orb-degree rule behind it. suspected layer: retrieval-plane / MCP contract (no surgical primitive fronts L0 reference catalogs).
