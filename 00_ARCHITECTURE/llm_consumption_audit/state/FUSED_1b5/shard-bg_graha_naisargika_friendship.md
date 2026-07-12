# FUSED Lane 1b+5 shard — bg_graha_naisargika_friendship (family_count=1)

## Channel classification
truly-UNREACHABLE. L0 global reference catalog (no chart_id); 72-cell natural-friendship matrix (9 planets × 8 others). Folded into asset `bg_dignity_reference` bundle; exposed by NO surgical primitive; not in manifest tool-map / tool_registry. Wire-confirmed unreachable (`read_asset` rejected). Full-pipeline `ask_madhav` surfaces the aggregate naisargika BALA value per-chart (chart_facts), never the pairwise friendship matrix.

## Per-family rows
| family_key | channel | retrievability_verdict | fidelity_verdict | derivation |
|---|---|---|---|---|
| `__table_row_count__=72` | truly-UNREACHABLE | UNREACHABLE (class 1) — 72-row natural-friendship matrix served by no tool | N/A — nothing arrives over wire; no diff possible, Lane-5 failure modes not exercisable | single-family path; exemplar==sole member; full per-family |

## Evidence (E-6)
- DB-truth call: `SELECT count(*) FROM bg_graha_naisargika_friendship;` → `72` (matches ledger `__table_row_count__=72`).
- Wire call: `POST /api/mcp/primitives/read_asset {"asset_id":"bg_dignity_reference"}` → `{"ok":false,"error":"Tool not in surgical whitelist: read_asset"}`; whitelist contains no friendship/relationship reference tool.
- Manifest/registry: no serving mapping in CAPABILITY_MANIFEST.json or tool_registry.
- Mitigation note: only the derived aggregate `graha_shadbala_naisargika` (strength scalar) surfaces via `query_chart_facts`; the underlying pairwise natural-friendship matrix (the classical baseline against which temporary relationships are combined) is unretrievable — a genuine width gap for any relationship-reasoning query.

## Finding
- lane=1b, class=1 UNREACHABLE, severity=LOW-MEDIUM. summary: L0 naisargika-friendship matrix (72 rows) unserved; consumer gets only the aggregate bala scalar, never the pairwise natural-relationship baseline needed to reason about pancha-dha maitri / temporary-vs-natural relationships. suspected layer: retrieval-plane / MCP contract.
