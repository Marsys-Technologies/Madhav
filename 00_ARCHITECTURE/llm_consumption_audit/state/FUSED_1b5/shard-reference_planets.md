# FUSED 1b+5 shard — reference_planets

Note: NOT present in value_families.jsonl (L0 global reference/dimension table, never sampled into ledger). Family enumerated from path assignment (family_count=1). family_key = table name.

| family_key | channel | retrievability_verdict | fidelity_verdict | derivation |
|---|---|---|---|---|
| reference_planets | truly-UNREACHABLE | FAIL (class 1) — 11 rows exist in DB (9 grahas + nodes); no MCP tool (surgical OR full-pipeline) serves this table; reference attributes reach consumers only denormalized into chart_facts at build time | N/A — no wire probe possible (nothing serves the table) | full per-family (family_count=1) |

## Evidence (E-6)
- DB-truth SELECT: `SELECT planet_id, canonical_name_en FROM reference_planets ORDER BY id LIMIT 1` → `rahu / Rahu`. Columns: exaltation_sign, exaltation_degree, debilitation_sign, mooltrikona_sign, own_signs, natural_benefic, karak_domains, dasha_years, source_citation.
- Serving-path check (code): no catalog.ts entry, no MCP primitive, no consume/full-pipeline SELECT. Read only by build-time writers (`bg_reference.py`, `l0_reference.py`, ga_* emitters). No ALIVE surgical tool fronts reference planet data.
- Lane-5 four failure modes: N/A (no wire side). Lane 1b class 1 UNREACHABLE.

Rubric note: Charter §7.1 DRAFT — no degraded-form grading applied.
