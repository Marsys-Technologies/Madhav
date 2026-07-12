# FUSED 1b+5 shard — reference_signs

Note: NOT present in value_families.jsonl (L0 global reference/dimension table, never sampled into ledger). Family enumerated from path assignment (family_count=1). family_key = table name.

| family_key | channel | retrievability_verdict | fidelity_verdict | derivation |
|---|---|---|---|---|
| reference_signs | truly-UNREACHABLE | FAIL (class 1) — 12 rows exist in DB; no MCP tool (surgical OR full-pipeline) serves this table; reference attributes reach consumers only denormalized into chart_facts at build time | N/A — no wire probe possible (nothing serves the table) | full per-family (family_count=1) |

## Evidence (E-6)
- DB-truth SELECT: `SELECT count(*) FROM reference_signs` → 12. Exemplar row: `sign_id=7 / canonical_name_en=Libra / lord=venus`. Columns: canonical_name_sa, element, modality, natural_house, is_odd, is_biped, significations, source_citation.
- Serving-path check (code): no catalog.ts entry, no MCP primitive, no consume/full-pipeline SELECT. Read only by build-time writers (`bg_reference.py`, `l0_reference.py`). Note: `ph_rectification/engine.py`'s `reference_signs` is a local Python dict variable, NOT this DB table. No ALIVE surgical tool fronts reference sign data.
- Lane-5 four failure modes: N/A (no wire side). Lane 1b class 1 UNREACHABLE.

Rubric note: Charter §7.1 DRAFT — no degraded-form grading applied.
