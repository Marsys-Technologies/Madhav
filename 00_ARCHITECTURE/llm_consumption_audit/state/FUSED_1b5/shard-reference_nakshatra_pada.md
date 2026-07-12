# FUSED 1b+5 shard — reference_nakshatra_pada

Note: NOT present in value_families.jsonl (L0 global reference/dimension table, never sampled into ledger). Family enumerated from path assignment (family_count=1). family_key = table name.

| family_key | channel | retrievability_verdict | fidelity_verdict | derivation |
|---|---|---|---|---|
| reference_nakshatra_pada | truly-UNREACHABLE | FAIL (class 1) — 108 rows exist in DB (27 nak × 4 pada); no MCP tool (surgical OR full-pipeline) serves this table; consumed only build-time | N/A — no wire probe possible (nothing serves the table) | full per-family (family_count=1) |

## Evidence (E-6)
- DB-truth SELECT: `SELECT count(*) FROM reference_nakshatra_pada` → 108. Exemplar row: `pada_id=1 / nakshatra_id=1 / pada_lord=mars`. Columns: pada_navamsa_sign, pada_akshara, bija_sound, mantra_prefix, element_shading, dosha_shading, etc.
- Serving-path check (code): no catalog.ts entry, no MCP primitive, no consume/full-pipeline SELECT. Read only by build-time writers (L0/L1 nakshatra build). No ALIVE surgical tool fronts it.
- Lane-5 four failure modes: N/A (no wire side). Lane 1b class 1 UNREACHABLE.

Rubric note: Charter §7.1 DRAFT — no degraded-form grading applied.
