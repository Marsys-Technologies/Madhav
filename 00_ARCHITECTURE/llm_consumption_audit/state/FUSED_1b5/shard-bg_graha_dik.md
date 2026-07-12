# FUSED Lane 1b+5 shard — bg_graha_dik (family_count=1)

## Channel classification
truly-UNREACHABLE. L0 global reference catalog (no chart_id). NOT in asset_registry at all (no asset row), not in CAPABILITY_MANIFEST tool-map, not in tool_registry. No surgical primitive serves it. Full-pipeline `ask_madhav` surfaces derived per-chart directional strength (bhava_bala_directional) from chart_facts, never the reference table.

## Per-family rows
| family_key | channel | retrievability_verdict | fidelity_verdict | derivation |
|---|---|---|---|---|
| `__table_row_count__=9` | truly-UNREACHABLE | UNREACHABLE (class 1) — 9-row graha directional-strength reference served by no tool | N/A — nothing arrives over wire; no diff possible, Lane-5 failure modes not exercisable | single-family path; exemplar==sole member; full per-family |

## Evidence (E-6)
- DB-truth call: `SELECT count(*) FROM bg_graha_dik;` → `9` (matches ledger `__table_row_count__=9`).
- Wire call: `POST /api/mcp/primitives/read_asset` (only plausible generic reader) → `{"ok":false,"error":"Tool not in surgical whitelist: read_asset"}`; surgical whitelist enumerated by server contains no dik/directional reference tool.
- Registry: `bg_graha_dik` absent from asset_registry (SELECT returned no row) and from tool_registry — strongest form of unreachable (no asset wrapper, no tool).
- Mitigation note: derived per-chart directional bala IS reachable via `query_chart_facts` (fact_category `bhava_bala_directional`); the reference dik-bala baseline catalog is unserved.

## Finding
- lane=1b, class=1 UNREACHABLE, severity=LOW. summary: L0 graha-dik reference (9 rows) has neither an asset_registry wrapper nor any MCP serving tool; only the per-chart directional-bala result is reachable, not the reference catalog. suspected layer: retrieval-plane / MCP contract (compounded: no asset registration).
