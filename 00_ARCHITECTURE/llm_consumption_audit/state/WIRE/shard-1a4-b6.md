# WIRE shard 1a4-b6 — FUSED Lane 1a (synthesizability-as-received) + Lane 4 (receipt honesty)

Charter: `00_ARCHITECTURE/llm_consumption_audit/briefs/CHARTER.md`. Cross-refs cited, not re-derived: LCA-1 (DEAD-19), LCA-2 (consult broken), LCA-3, LCA-7.

Assigned tool batch (11): list_my_charts, list_my_sessions, list_remedies_by_category, mimamsa_calibration_get, mimamsa_insight_get, mimamsa_lel_query, mimamsa_outcome_record, mitigation_map, muhurta_finder, pact_query, phala_anchors_get.
100% probed, no skips. Surgical wire on :3000.

## Channel classification

| tool | channel | note |
|---|---|---|
| list_remedies_by_category | reachable-surgical | maps → `list_remedies_by_category` retrieval tool |
| mitigation_map | reachable-surgical | maps → `query_remedy_program` (F-016) |
| muhurta_finder | reachable-surgical | maps → `query_muhurat` |
| list_my_charts | served-only-by-down-pipeline | "Tool not in surgical whitelist" (validation) |
| list_my_sessions | served-only-by-down-pipeline | "Tool not in surgical whitelist" |
| mimamsa_calibration_get | served-only-by-down-pipeline | legacy display-name; live L5 cap = `query_calibration` |
| mimamsa_insight_get | served-only-by-down-pipeline | no surgical mapping |
| mimamsa_lel_query | served-only-by-down-pipeline | no surgical mapping |
| mimamsa_outcome_record | served-only-by-down-pipeline | no surgical mapping |
| pact_query | served-only-by-down-pipeline | no surgical mapping |
| phala_anchors_get | served-only-by-down-pipeline | no surgical mapping |

8 of 11 assigned names are absent from the live MCP whitelist (name-drift between assigned batch and live surface). Per protocol → served-only-by-down-pipeline; consult path broken (LCA-2); synthesizability = not-probed.

## reachable-surgical grades

### list_remedies_by_category — synth FAIL, receipt HONEST
- chart_id only → `orchestrator_error … {"error":"category is required"}` (does NOT apply the code-side default 'mantras').
- `category=mantras` → `ok:true` … content: `{"category":"mantras","remedies":[],"returned_count":0}`.
- DB truth: `brahma_remedy_corpus` has 266 rows — 217 `category IS NULL`, 49 `category='corpus_sweep'`. The only guessable/default category ('mantras') matches ZERO rows; the one real category value is a non-human-facing 'corpus_sweep'. EMPTY SHELL as received.
- Receipt: `returned_count:0` truthfully matches empty array → HONEST. Tension: `epistemics.confidence_band:"high"` on a zero-row result.

### mitigation_map — synth FAIL, receipt HONEST (with confidence tension)
- chart_id only → `ok:true`. `result.results[0].content` = 493,635 bytes; full envelope 545,469 bytes (single line). Un-budgeted dump.
- `count:602`. All 602 remedies are hollow: `program_jsonb.total_scheduled==0` (602/602), `tradition_options_jsonb` all-empty {vastu/vedic/modern/tantra/ayurvedic/lal_kitab: []} (602/602), `recommended_tier_jsonb` all-empty, `cross_tradition_corroboration:0`. Zero remedies carry any actionable content. Bare `obstruction_id`/`linked_anchor_id` refs, no remedy text.
- Receipt: `count:602` matches array; `sparse_note:"phala_mitigation count is unknown — sparse rows expected."` truthfully discloses sparseness → HONEST. Tension: `epistemics.confidence_band:"high"` while 100% of payload is empty scaffolding.

### muhurta_finder — synth PARTIAL, receipt HONEST
- 3-round param discovery: chart_id → `{"error":"action_type must be one of: marriage, travel, business, medical, education, property, general"}`; +action_type → `{"error":"date_range.start and date_range.end are required"}`; +date_range → `ok:true`.
- Final payload well-formed: scored `windows[]` with `score`, `factors{panchanga_quality,dasha_quality,transit_quality,signal_activation}`, panchanga_details, and a `source_citation` string. Composable to a cited sentence — but only after out-of-band knowledge of required params (errors are self-describing enums, so recoverable). PARTIAL (needs tribal knowledge / multi-round).
- Content caveat (not my lane, noted): source_citation cites "FORENSIC v8.0" (archived/deleted source) and `ad_lord:"unknown"`.
- Receipt: invocation_params echo + latency consistent → HONEST.

## Independent re-probe confirmation (2nd worker pass)
Re-ran all 11 on surgical wire. Confirms above verbatim:
- list_remedies_by_category {category:"mantra"} → `{"category":"mantra","remedies":[],"returned_count":0}` (empty for either singular/plural). Receipt HONEST (count matches).
- mitigation_map → 545,470-byte envelope, `count:602`, verified 602 mitigation_id rows; total_scheduled!=0 rows = 0/602; non-empty tradition-option rows = 0/602. Confirms EMPTY-SHELL-at-scale + un-budgeted dump.
- muhurta_finder → confirmed 3-round param discovery (activity→action_type→nested date_range.{start,end}); success payload 4,395 bytes, scored windows + source_citation.

## Lane 4 reconciliation — identity + confidence flags (kept as milder findings, not full class-5)
- Envelope `tool_name` reflects the underlying retrieval tool, not the invoked MCP alias: mitigation_map→`query_remedy_program`, muhurta_finder→`query_muhurat`. Counters (count/returned_count) are honest vs payload, so receipts graded HONEST; the alias→retrieval-tool identity leak is a transparency note (a first-contact consumer sees a different tool_name than it called, and all param errors name the inner tool), logged under Lane 4 as class-5-adjacent, not a counter contradiction.
- Cross-cutting confidence-flag tension: `epistemics.confidence_band:"high"` is attached to a 0-row payload (list_remedies) and to a 100%-hollow 602-row payload (mitigation_map). A "high" confidence flag over empty evidence is a self-description that overstates payload quality — logged Lane 4, class 5 (flag ≠ payload), severity low.

## Served-only-by-down-pipeline (8) — retrieval-plane note
8/11 assigned names absent from live whitelist; consumable only via full pipeline (broken, LCA-2); synthesizability not-probed, receipt n/a. Substantive gap: the L2 `pact_query` flagship predictive instrument and the entire L5 mimamsa read/write surface (calibration/insight/lel/outcome) have NO surgical primitive — class-1 UNREACHABLE by the only working (surgical) channel. Whether this is name-drift (assigned batch used display names that never matched the live surface) or a genuine serving gap is itself a finding for Lane 10.
