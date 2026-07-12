# FUSED Lane 1b+5 shard — bg_medical_mappings (family_count=1)

## Channel classification
truly-UNREACHABLE. L0 global reference catalog (no chart_id). Registered as standalone asset `bg_medical_mappings` (count_sql `SELECT COUNT(*) FROM bg_medical_mappings`) but exposed by NO surgical primitive; not in manifest tool-map / tool_registry. Wire-confirmed unreachable (`read_asset` rejected — not in surgical whitelist). No `query_chart_facts` fact_category surfaces medical significations for the chart either (ga_medical is a separate asset surface; not among the surgical whitelist's served categories) — so the interpretive medical-mapping content is unreachable both as reference catalog and as applied per-chart data via the audited surgical channel.

## Per-family rows
| family_key | channel | retrievability_verdict | fidelity_verdict | derivation |
|---|---|---|---|---|
| `__table_row_count__=21` | truly-UNREACHABLE | UNREACHABLE (class 1) — 21-row planet/sign→body-part/disease medical mapping served by no tool | N/A — nothing arrives over wire; no diff possible, Lane-5 failure modes not exercisable | single-family path; exemplar==sole member; full per-family |

## Evidence (E-6)
- DB-truth call: `SELECT count(*) FROM bg_medical_mappings;` → `21` (matches ledger `__table_row_count__=21`).
- Wire call: `POST /api/mcp/primitives/read_asset {"params":{"chart_id":"482012f1-...","asset_id":"bg_medical_mappings"}}` → `{"ok":false,"error":{"class":"validation","message":"Tool not in surgical whitelist: read_asset","remediation":"Use ask_madhav for full-pipeline queries..."}}`.
- Registry: asset_registry HAS `bg_medical_mappings` (so the asset is built and counted) but no MCP tool fronts it; tool_registry has no medical tool.
- Coverage note: unlike the dignity/combustion/dik families, the derived RESULT is NOT reachable via query_chart_facts (no medical fact_category in the served surgical surface) — this is the strongest UNREACHABLE of the six: interpretive health-domain reference wholly absent from the wire.

## Finding
- lane=1b, class=1 UNREACHABLE, severity=MEDIUM. summary: L0 medical-mappings catalog (21 rows; planet/sign→body-part/disease significations) is built and asset-registered but has zero MCP serving path AND no derived-result fallback on the surgical channel — a health-domain question consumer cannot retrieve any of this interpretive reference. suspected layer: retrieval-plane / MCP contract (asset built, never fronted by a tool).
