# FUSED 1b+5 shard — reference_nakshatra

Note: NOT present in value_families.jsonl (ledger holds per-chart/global sampled families only; these L0 Brahmagyan global reference/dimension tables were never sampled into the ledger). Family enumerated from the path assignment (family_count=1). family_key = table name (whole-table reference content = 1 family).

| family_key | channel | retrievability_verdict | fidelity_verdict | derivation |
|---|---|---|---|---|
| reference_nakshatra | truly-UNREACHABLE | FAIL (class 1) — 28 rows exist in DB; no MCP tool (surgical OR full-pipeline) serves this table; reference content reaches consumers only denormalized into chart_facts at L1 build time, never as the reference row itself over the wire | N/A — no wire probe possible (nothing serves the table; cannot diff table-vs-wire) | full per-family (family_count=1) |

## Evidence (E-6)
- DB-truth SELECT: `SELECT count(*) FROM reference_nakshatra` → 28. Exemplar row: `nakshatra_id=1 / name_en=Ashwini / vimshottari_lord=ketu`. Columns include name_sa_iast, presiding_deity, gana, nadi, yoni, shakti, symbol, paramayus, etc. (45 cols).
- Serving-path check (code): no entry in `platform/src/lib/retrieval/registry/catalog.ts`; no MCP primitive under `src/app/api/mcp/primitives`; no `consume`/full-pipeline path SELECTs it. Only build-time WRITERS read it: `bg_reference.py`, `l0_nakshatra.py`, `ga_nakshatra.py`, `ga_nakshatra_emitters.py`. No ALIVE surgical tool fronts reference data.
- Lane-5 four failure modes: N/A (no wire side exists to diff). Lane 1b class 1 UNREACHABLE.

Rubric note: Charter §7.1 rubric is DRAFT/provisional pending Cowork ratification — no §7.1 grading applied here (unreachable, not degraded-form).
