# FUSED Lane 1b+5 shard — bg_motion_state_thresholds (family_count=1)

## Channel classification
truly-UNREACHABLE. L0 global reference catalog (no chart_id); 27-row speed/motion-state threshold table (vakri/atichara/etc. thresholds). Folded into asset `bg_dignity_reference` bundle; exposed by NO surgical primitive; not in manifest tool-map / tool_registry. Wire-confirmed unreachable (`read_asset` rejected). Full-pipeline `ask_madhav` surfaces the derived per-chart motion STATE from chart_facts, never the threshold reference.

## Per-family rows
| family_key | channel | retrievability_verdict | fidelity_verdict | derivation |
|---|---|---|---|---|
| `__table_row_count__=27` | truly-UNREACHABLE | UNREACHABLE (class 1) — 27-row motion-state threshold catalog served by no tool | N/A — nothing arrives over wire; no diff possible, Lane-5 failure modes not exercisable | single-family path; exemplar==sole member; full per-family |

## Evidence (E-6)
- DB-truth call: `SELECT count(*) FROM bg_motion_state_thresholds;` → `27` (matches ledger `__table_row_count__=27`).
- Wire call: `POST /api/mcp/primitives/read_asset {"asset_id":"bg_dignity_reference"}` → `{"ok":false,"error":"Tool not in surgical whitelist: read_asset"}`; whitelist has no motion/speed reference tool.
- Manifest/registry: no serving mapping in CAPABILITY_MANIFEST.json or tool_registry.
- Mitigation note: the derived per-chart motion state (retrograde/combust/vakri classification) is reachable via chart_facts; the speed-threshold reference constants that produce it are unserved.

## Finding
- lane=1b, class=1 UNREACHABLE, severity=LOW. summary: L0 motion-state threshold catalog (27 rows) unserved by any MCP path; per-chart motion state reachable via chart_facts but the numeric thresholds behind the classification are not citable over the wire. suspected layer: retrieval-plane / MCP contract.
