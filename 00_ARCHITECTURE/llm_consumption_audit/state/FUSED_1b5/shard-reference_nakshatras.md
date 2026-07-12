# FUSED 1b+5 shard — reference_nakshatras

Note: NOT present in value_families.jsonl (L0 global reference/dimension table, never sampled into ledger). Family enumerated from path assignment (family_count=1). family_key = table name. (This is a SECOND, parallel nakshatra reference table — 27 rows — distinct from `reference_nakshatra` (28 rows w/ Abhijit); both exist, a duplication, but neither is served over the wire.)

| family_key | channel | retrievability_verdict | fidelity_verdict | derivation |
|---|---|---|---|---|
| reference_nakshatras | truly-UNREACHABLE | FAIL (class 1) — 27 rows exist in DB; no MCP tool (surgical OR full-pipeline) serves this table; consumed only build-time | N/A — no wire probe possible (nothing serves the table) | full per-family (family_count=1) |

## Evidence (E-6)
- DB-truth SELECT: `SELECT count(*) FROM reference_nakshatras` → 27. Exemplar row: `nakshatra_id=21 / canonical_name_en=Uttara Ashadha / lord=sun`. Columns: canonical_name_sa, deity, nature, guna, pada_lords, body_part, source_citation.
- Serving-path check (code): no catalog.ts entry, no MCP primitive, no consume/full-pipeline SELECT. Read only by build-time writers. No ALIVE surgical tool fronts it.
- Lane-5 four failure modes: N/A (no wire side). Lane 1b class 1 UNREACHABLE.

Rubric note: Charter §7.1 DRAFT — no degraded-form grading applied.
