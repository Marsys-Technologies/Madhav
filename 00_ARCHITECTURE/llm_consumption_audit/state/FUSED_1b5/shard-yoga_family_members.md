# FUSED 1b+5 shard — yoga_family_members

path: yoga_family_members | families_total: 1 | channel: truly-UNREACHABLE
derivation: full per-family (family_count=1; exemplar == the only family)

## Evidence
- DB-truth (E-6): `SELECT count(*) FROM yoga_family_members` → **0 rows** (both charts / global; table has no chart_id — global L0 catalog).
- Table exists: `information_schema.tables` returns `yoga_family_members` (created by migration 239_yoga_system.sql).
- Never seeded: `grep -rniE "INSERT INTO yoga_family_members" platform` → **no matches** (scaffold table, zero seed data).
- No serving tool: no MCP surgical tool in ALIVE list maps to yoga_* ; no full-pipeline/register tool fronts it; grep of MCP primitives → no matches. Only consumer is `ga_writers/ga_yoga_writer.py::_load_yoga_families` which reads it defensively ("if table exists") — an internal writer dependency, NOT a wire-facing retrieval path.
- Wire probe: NOT POSSIBLE — no tool serves the table; and with 0 rows there is nothing to retrieve or diff.

## Rows
| family_key | channel | retrievability_verdict | fidelity_verdict | derivation |
|---|---|---|---|---|
| `__table_row_count__=0` | truly-UNREACHABLE | UNREACHABLE (no serving tool + empty table) | N/A (nothing arrives over wire; no diff possible) | full per-family (exemplar=`__table_row_count__=0`) |

## Finding (lane 1b, class 1 UNREACHABLE, severity LOW)
Empty scaffold catalog: `yoga_family_members` created (migration 239) but never populated and fronted by no retrieval tool. Data-population gap, not a wire-fidelity defect. Consuming writer degrades gracefully. No Lane 5 (wire) finding — no wire surface to diff against.
