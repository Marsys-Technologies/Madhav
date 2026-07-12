# WIRE shard-1a4-b8 — FUSED Lane 1a (synthesizability-as-received) + Lane 4 (receipt honesty)

Chart: 482012f1-710e-4a25-994a-93821f5871aa. 11/11 tools probed (100%, no skips). Surgical wire :3000.

## Channel census

| tool | channel | synth | receipt |
|---|---|---|---|
| query_planet_transit | served-only-by-down-pipeline | not-probed | n/a |
| query_remediation | served-only-by-down-pipeline | not-probed | n/a |
| query_remedies | reachable-surgical | PASS | HONEST |
| query_remedies_by_planet | reachable-surgical | PARTIAL | HONEST |
| query_remedies_for_chart | reachable-surgical | FAIL | DISHONEST(contract) |
| query_retrograde_periods | served-only-by-down-pipeline | not-probed | n/a |
| query_special_lagnas | served-only-by-down-pipeline | not-probed | n/a |
| query_tantric_remedies | reachable-surgical | FAIL | HONEST |
| read_chapter | served-only-by-down-pipeline | not-probed | n/a |
| read_classical_text | reachable-surgical | PARTIAL | DISHONEST |
| read_remedy | reachable-surgical | PASS | HONEST |

## Notes per tool

- **query_planet_transit, query_retrograde_periods, query_special_lagnas, read_chapter, query_remediation**: `{"class":"validation","message":"Tool not in surgical whitelist: <t>"}` → full-pipeline-only. query_remediation is not even in the enumerated whitelist (unregistered alias). Consult broken per LCA-2 → synthesizability not-probed.
- **query_remedies** (chart_id only): ok:true. `returned:20,total:266,limit:20,offset:0,fields:"compact",truncated:true` — all counters internally consistent → receipt HONEST (clean contrast to LCA-7 msr_sql truncated:False lie). Rows self-describing: `prescription_text` + `source_citation` + `cost_tier` + `confidence`. Composable to one cited sentence on first contact → PASS. Caveat: with no planet/domain filter it silently returns jupiter-only (20 of 266); undocumented default, but self-describing.
- **query_remedies_by_planet** (planet=jupiter): ok:true, `returned_count:31` matches array → HONEST. BUT first 5 rows are `category:"corpus_sweep"` with raw OCR garbage in prescription_text, e.g. `"Significators and Significations of Planets & Houses\n131\nttl \":(J~6q«g6Q( ,1,f.\\I,ql\\l1..."` and `"5:16:3m [Adh. VIII. Sl. 5-7. gimme: quit firearm cum retain:"` — un-actionable page-scan dumps labeled as remedies. A consumer taking top-N gets garbage before real remedies → PARTIAL (class-6 finding).
- **query_remedies_for_chart** — MISLABELED CONTRACT (lane-1a class-9/6, lane-4 contract-dishonest). The `affliction` param is silently keyed to the **planet** column: planet names return data (`saturn`→5, `jupiter`→5, `mars`→5) but real affliction/dosha terms return EMPTY (`mangal_dosha`→0, `sade_sati`→0, `debilitation`→0, `weak_jupiter`→0, `kuja_dosha`→0). Output is **identical regardless of chart_id** (echoed, never consulted) despite the `_for_chart` name. `returned_count` matches the array (counter locally honest) BUT the tool NAME + param NAME advertise chart-aware affliction→remedy matching that does not exist; a consumer asking "remedies for this chart's afflictions" gets empty and wrongly concludes none exist → receipt DISHONEST at contract level, synth FAIL. Verbatim empty: `{"affliction":"sade_sati","remedies":[],"returned_count":0,"provenance":{"table":"brahma_remedy_corpus","note":"No audience_tier gating — serve-time only."}}`.
- **query_tantric_remedies** (chart_id only): ok:true, `{"remedies":[],"returned_count:0,"filters":{}}`. Advertised analysis stage returns nothing; no guidance on required filters → FAIL (class-4). count matches → HONEST.
- **read_classical_text** — DISHONEST counter (lane-4 class-5) + weak-form (lane-1a). Default (no query): returns 20 rows with meta `{"total":20}`, BUT DB `classical_text_chunks` = **10,651**. Reporting `total:20` for a 10,651-chunk corpus is dishonest — an LLM reads `total` as "everything available" and believes it has the whole canon after 20 page-1 chunks of one MEDIUM book (bhrigu_nandi_nadi). With `query` param the response SHAPE SHIFTS: `rows[].content_en` goes EMPTY and text relocates to `citations[].verse_text_en` (inconsistent form between modes → a naive rows[].content_en consumer gets blanks). Query relevance is weak+OCR-noisy: `query:"raja yoga"` surfaces infant-death yogas + a table-of-contents page, keyword_score 0.01–0.14 (combined_score vector-dominated), text like `"Thejoga leading to the instant death of the new born child"`. Text IS citable in query mode → synth PARTIAL, receipt DISHONEST.
- **read_remedy** (remedy_id=jupiter_matrix_behavioral): ok:true, `found:true`, full record with prescription_text/source_citation/scaffold_status:"live" → PASS, HONEST.

- **query_tantric_remedies**: DB check confirms `brahma_remedy_corpus` holds **0** tantric-typed rows → EMPTY SHELL (class-4). returned_count:0 counter honest; the capability itself is unpopulated.

## Lane 4 verdict (revised after DB grounding)
- HONEST: query_remedies (total:266 = DB 266, truncated:true), query_remedies_by_planet (returned_count:31 = DB jupiter 31, full set), query_tantric_remedies (0=0), read_remedy (found:true full record).
- **DISHONEST: read_classical_text** — `total:20` misrepresents a 10,651-chunk corpus (class-5, LCA-7-analogue for the classical-text plane). Independent finding.
- **DISHONEST(contract): query_remedies_for_chart** — counters honest but `_for_chart`+`affliction` naming advertises chart/affliction logic that does not exist (planet-keyed, chart-agnostic).
