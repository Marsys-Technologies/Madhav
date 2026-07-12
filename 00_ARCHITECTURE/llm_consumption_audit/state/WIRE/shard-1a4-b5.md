# WIRE shard-1a4-b5 — Lane 1a (synthesizability-as-received) + Lane 4 (receipt honesty)

Charter: LLM_CONSUMPTION_AUDIT_CHARTER v1.1. Chart 482012f1. Surgical wire only.
Tools probed: 11/11 (100%, rider 1). Cross-refs cited, not re-derived: LCA-1, LCA-2, LCA-7.

## Channel census (11 tools)

| tool | channel | synthesizability | receipt_honesty |
|---|---|---|---|
| lel_query | reachable-surgical | PARTIAL | DISHONEST |
| list_entities | reachable-surgical | PASS | DISHONEST |
| judgment_query | served-only-by-down-pipeline | not-probed | n/a |
| kala_life_arc_get | served-only-by-down-pipeline | not-probed | n/a |
| kala_muhurta_get | served-only-by-down-pipeline | not-probed | n/a |
| kala_projections_get | served-only-by-down-pipeline | not-probed | n/a |
| kala_temporal_bundle | served-only-by-down-pipeline | not-probed | n/a |
| kala_windows_get | served-only-by-down-pipeline | not-probed | n/a |
| kala_yoga_activation_get | served-only-by-down-pipeline | not-probed | n/a |
| list_assets | served-only-by-down-pipeline | not-probed | n/a |
| list_classical_texts | served-only-by-down-pipeline | not-probed | n/a |

9 full-pipeline-only tools each verbatim-returned `{"ok":false,...,"message":"Tool not in surgical whitelist: <name>"}`.
Per LCA-2 the full-pipeline consult path (ask_madhav) is broken → these are dead-in-practice for the consuming LLM.

## Findings

### F1 [lane 4] lel_query — truncated:False on a 50-of-13,364 slice (LCA-7 clone). class 5.
Verbatim (E-6): `"returned_count":50,"total_matching_filters":13364,"truncated":false,"filters":{"top_k":50,...}`.
50 of 13,364 bodha_msr_signals served, `truncated:false`. Identical dishonesty pattern to LCA-7 (msr_sql). DISHONEST.

### F2 [lane 4] lel_query — name promises Life-Event-Log, payload delivers zero life events. class 4/5.
Verbatim (E-6): provenance.lel_note = `"lel_origin=true signals: 0 rows currently. LEL filter is safe but returns empty."` and `filters.lel_enabled:false`, `provenance.tables:["bodha_msr_signals"]`. Every one of 50 returned signals carries `"lel_origin":false` (grep: 50/50 false, 0 true). The tool named lel_query returns generic MSR structural/dignity signals, NOT the Life Event Log its name advertises. EMPTY SHELL for its named function, silently substituted with unrelated signals under ok:true.

### F3 [lane 1a] lel_query — un-scoped salience_fallback ranks D108 dignity=neutral as #1 chart_defining. class 7.
Verbatim (E-6): top signal rank 1 `citation_human:"Saturn neutral in Sagittarius (house 1) in D108 (lahiri_chitrapaksha)."` salience 2.99, `signature_tier:"chart_defining"`; `ranking_basis.mode:"salience_fallback"` with `domain:null`, note `"composite ranking requires domain"`. Per-row text IS self-describing/citable (PASS-grade rows), but as-received the consumer needs tribal knowledge (must pass domain+paradigm to get a coherent single-tradition ranked slice; must know lel_query≠life events) → synthesizability PARTIAL. A D108 neutral dignity ranked chart-defining is trivia-as-chart-defining (DROWNED).

### F4 [lane 4] list_entities — total:100 is a silent cap hiding 552 of 652 entities. class 5. CONFIRMED (DB).
Verbatim (E-6): payload ends alphabetically at `"prana_dasha"` with `"total":100,"filters":{"entity_class_requested":null,"entity_class_resolved":null}`. NO truncated flag, NO total_matching, NO pagination echoed. DB (mcp__postgres__query): `SELECT count(*) FROM brahma_ontology` = 652 (concepts=136, aspect_type=13, 15 classes). list_entities served 100 (13 aspect_type + 87 of 136 concepts, alphabetical to P) and labels it `total:100` — 552 entities (85%) silently unreachable via this tool, mislabeled as the complete total. DISHONEST + UNREACHABLE.

### F5 [lane 1a] list_entities — rows self-describing (PASS). 
Each entity = `{canonical_id, entity_class, canonical_name_en, canonical_name_sa, synonyms[]}` e.g. `{"canonical_id":"navamsa","canonical_name_en":"Navamsa","canonical_name_sa":"Navāṃśa","synonyms":["navamsa","D9","navamsha"]}`. Composable to a cited resolve-entity sentence on first contact. Synthesizability-as-received PASS (the completeness/honesty defect is F4/Lane 4, not a per-row synthesizability failure).

### F6 [lane 1a] 9 tools served-only-by-down-pipeline; consult path broken (LCA-2). class 1.
judgment_query, kala_life_arc_get, kala_muhurta_get, kala_projections_get, kala_temporal_bundle, kala_windows_get, kala_yoga_activation_get, list_assets, list_classical_texts — all return `"Tool not in surgical whitelist: <name>"`. Not in the surgical whitelist; only reachable via full-pipeline ask_madhav, which is broken per LCA-2. synthesizability not-probed (unreachable surgically). Of these, the 7 kala_* + judgment_query are exactly the Kāla/judgment temporal surfaces a time-indexed prediction query needs — their being non-surgical means the depth axis (Charter §2 temporal presence MD/AD/PD, structural×temporal convergence) is un-probeable on the surgical wire.
