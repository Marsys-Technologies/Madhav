# FUSED 1b+5 shard — yoga_interaction_rules

path: yoga_interaction_rules | families_total: 1 | channel: truly-UNREACHABLE
derivation: full per-family (family_count=1; exemplar == the only family)

## Evidence
- DB-truth (E-6): `SELECT count(*) FROM yoga_interaction_rules` → **0 rows** (global L0 catalog, no chart_id).
- Table exists: `information_schema.tables` returns `yoga_interaction_rules` (created by migration 239_yoga_system.sql).
- Never seeded: `grep -rniE "INSERT INTO yoga_interaction_rules" platform` → **no matches** (scaffold table, zero seed data).
- No serving tool: no MCP surgical tool (ALIVE or DEAD-19) maps to yoga_interaction_rules; no full-pipeline/register tool fronts it; grep of MCP primitives → no matches. Not even referenced by a writer consumer in the current codebase (only yoga_family_members is read, by ga_yoga_writer).
- Wire probe: NOT POSSIBLE — no tool serves the table; 0 rows means nothing to retrieve or diff.

## Rows
| family_key | channel | retrievability_verdict | fidelity_verdict | derivation |
|---|---|---|---|---|
| `__table_row_count__=0` | truly-UNREACHABLE | UNREACHABLE (no serving tool + empty table) | N/A (nothing arrives over wire; no diff possible) | full per-family (exemplar=`__table_row_count__=0`) |

## Finding (lane 1b, class 1 UNREACHABLE, severity LOW)
Empty scaffold catalog: `yoga_interaction_rules` created (migration 239) but never populated, fronted by no retrieval tool, and consumed by no current writer. Data-population gap, not a wire-fidelity defect. No Lane 5 (wire) finding — no wire surface to diff.
