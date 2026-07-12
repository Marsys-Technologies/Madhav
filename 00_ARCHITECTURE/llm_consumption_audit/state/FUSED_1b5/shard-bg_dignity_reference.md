# FUSED Lane 1b+5 shard — bg_dignity_reference (family_count=1)

## Channel classification
truly-UNREACHABLE. L0 global reference catalog (no chart_id). Registered as asset `bg_dignity_reference` but exposed by NO surgical primitive; not in manifest tool-map / tool_registry. Wire-confirmed unreachable (`read_asset` rejected — not in surgical whitelist). Full-pipeline `ask_madhav` surfaces derived per-chart dignity from chart_facts, never the reference table.

## Per-family rows
| family_key | channel | retrievability_verdict | fidelity_verdict | derivation |
|---|---|---|---|---|
| `__table_row_count__=9` | truly-UNREACHABLE | UNREACHABLE (class 1) — 9-row exalt/debil/moolatrikona reference served by no tool | N/A — nothing arrives over wire; no diff possible, Lane-5 failure modes not exercisable | single-family path; exemplar==sole member; full per-family |

## Evidence (E-6)
- DB-truth call: `SELECT count(*) FROM bg_dignity_reference;` → `9` (matches ledger `__table_row_count__=9`).
- Wire call: `POST /api/mcp/primitives/read_asset {"params":{"chart_id":"482012f1-...","asset_id":"bg_dignity_reference"}}` → `{"ok":false,"error":{"class":"validation","message":"Tool not in surgical whitelist: read_asset","remediation":"Use ask_madhav for full-pipeline queries..."}}`.
- Manifest/registry: no bg_dignity_reference tool mapping in CAPABILITY_MANIFEST.json; tool_registry has no serving tool.
- Mitigation note: derived per-chart dignity IS reachable via `query_chart_facts` (fact_category `graha_dignity_per_varga`, `graha_effective_dignity_modified_by_aspects`); only the abstract reference catalog is unserved.

## Finding
- lane=1b, class=1 UNREACHABLE, severity=LOW. summary: L0 dignity-reference catalog (9 rows) unserved by any MCP path; per-chart dignity verdict reachable via chart_facts but the classical reference rule is not citable over the wire. suspected layer: retrieval-plane / MCP contract.
