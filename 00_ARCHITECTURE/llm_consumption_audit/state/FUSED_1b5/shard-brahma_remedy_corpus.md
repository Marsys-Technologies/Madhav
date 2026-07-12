# FUSED 1b+5 shard — brahma_remedy_corpus (1 family)

DB truth: `SELECT count(*) FROM brahma_remedy_corpus` = 266 rows.
Serving tool (ALIVE, whitelisted): `query_remedies` (SELECT ... FROM brahma_remedy_corpus; aliased
response tool_name "remedial_codex_query"). Also whitelisted: read_remedy, list_remedies_by_category,
query_tantric_remedies, query_remedies_by_planet. CONFIRMED reachable-surgical.
Wire call: POST /api/mcp/primitives/query_remedies body {"params":{}} → ok:true.

FIDELITY (Lane 5) exemplar diff — remedy_id=jupiter_matrix_behavioral:
  DB: planet=jupiter, remedy_type=behavioral, category=NULL, deity=NULL, prescription_text="Adopt
      Jupiter-strengthening conduct: serve the significations of Jupiter..."
  WIRE: identical planet/remedy_type/category/deity/prescription_text + source_canonical_id=BPHS,
      cost_tier=free, confidence=0.85. Wire value == DB truth EXACTLY. No field dropped in pivot,
      no subject merge, no mid-narration trim. Fidelity = PASS.
RETRIEVABILITY (Lane 1b): reachable. Minor: default unfiltered call returns 20 of 266 (default limit
20); full corpus reachable via planet/remedy_type filters + read_remedy(remedy_id) individual fetch.
Low-severity default-page note; not a decisive-row-loss (filterable + individually addressable).

| family_key | channel | retrievability | fidelity | derivation |
|---|---|---|---|---|
| __table_row_count__=266 | reachable-surgical | REACHABLE (default 20/266 page, filterable + read_remedy individual — full corpus obtainable) | PASS (wire==DB exact on exemplar) | path-grade(exemplar=__table_row_count__=266) sole family; full-depth fused probe |
