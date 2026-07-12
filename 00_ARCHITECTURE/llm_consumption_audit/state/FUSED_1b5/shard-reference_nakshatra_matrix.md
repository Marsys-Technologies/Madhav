# FUSED 1b+5 shard — reference_nakshatra_matrix

Note: NOT present in value_families.jsonl (L0 global reference/dimension table, never sampled into ledger). Family enumerated from path assignment (family_count=1). family_key = table name.

| family_key | channel | retrievability_verdict | fidelity_verdict | derivation |
|---|---|---|---|---|
| reference_nakshatra_matrix | truly-UNREACHABLE | FAIL (class 1) — 2721 rows exist in DB (kuta/compatibility matrices); no MCP tool (surgical OR full-pipeline) serves this table; consumed only build-time | N/A — no wire probe possible (nothing serves the table) | full per-family (family_count=1) |

## Evidence (E-6)
- DB-truth SELECT: `SELECT count(*) FROM reference_nakshatra_matrix` → 2721. Exemplar row: `matrix_type=gana_kuta / from_key=Deva -> to_key=Deva = relation_value=compatible`. Columns: matrix_type, from_key, to_key, relation_value, guna_points, max_points, notes, tradition_scope, classical_source.
- Serving-path check (code): no catalog.ts entry, no MCP primitive, no consume/full-pipeline SELECT. Read only by build-time writers (`bg_reference.py` / L0 reference build). No ALIVE surgical tool fronts it.
- Lane-5 four failure modes: N/A (no wire side). Lane 1b class 1 UNREACHABLE.

Rubric note: Charter §7.1 DRAFT — no degraded-form grading applied (table is absent, not degraded).
