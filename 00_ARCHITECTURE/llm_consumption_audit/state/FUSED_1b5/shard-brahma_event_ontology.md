# FUSED 1b+5 shard — brahma_event_ontology (1 family)

DB truth: `SELECT count(*) FROM brahma_event_ontology` = 22 rows.
No DEDICATED surgical/catalog retrieval tool for this table. Its values are consumed only INTERNALLY,
embedded as base-rate provenance inside L4/L5 predictive full-pipeline outputs:
 - query_predictive_anchors.ts: reads `brahma_event_ontology.base_rate_by_age` (row-normalized), emits
   it only as a `base_rate_source` provenance STRING inside a phala anchor payload.
 - query_predictions.ts: reads `brahma_event_ontology.base_rate` similarly.
Neither exposes the ontology as a browsable catalog surface, and both are full-pipeline (not surgical-
whitelisted). The 22-row event-class catalog (event_class definitions, priors) has no retrieval surface
of its own → served-only-by-down-pipeline (surfaced only as derived provenance fragments). No surgical
wire probe → no fidelity diff.

| family_key | channel | retrievability | fidelity | derivation |
|---|---|---|---|---|
| __table_row_count__=22 | served-only-by-down-pipeline | UNREACHABLE-AS-CATALOG (no dedicated tool; values only embedded as base_rate provenance in L4/L5 full-pipeline outputs) | N/A (no wire reachable) | path-grade(exemplar=__table_row_count__=22) sole family |
