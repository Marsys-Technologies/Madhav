# WIRE shard-1a4-b11 — FUSED Lane 1a (synthesizability-as-received) + Lane 4 (receipt honesty)

Batch b11 tools (11), 100% probed. Wire: POST localhost:3000/api/mcp/primitives/<tool>.

## Channel map
| tool | channel | note |
|---|---|---|
| resolve_entity | reachable-surgical | in whitelist; works with `name` param |
| ref_tantric_remedies_get | served-only-by-down-pipeline | "not in surgical whitelist" |
| ref_transit_rules_get | served-only-by-down-pipeline | "not in surgical whitelist" |
| ref_vector_search | served-only-by-down-pipeline | "not in surgical whitelist" |
| ref_yogas_get | served-only-by-down-pipeline | "not in surgical whitelist" |
| search_classical_texts | served-only-by-down-pipeline | "not in surgical whitelist" |
| select_chart | served-only-by-down-pipeline | "not in surgical whitelist" |
| synth_chart_brief_get | served-only-by-down-pipeline | "not in surgical whitelist" |
| synth_tail_divergence_get | served-only-by-down-pipeline | "not in surgical whitelist" |
| traverse_graph | served-only-by-down-pipeline | "not in surgical whitelist" |
| util_intent_classify | served-only-by-down-pipeline | "not in surgical whitelist" |

10/11 (91%) of the advertised MCP tool names for this batch are NOT surgically reachable — they are the "friendly" wrapper names (ref_*/synth_*/util_*/select_*/traverse_*/search_*) whose canonical surgical equivalents exist under DIFFERENT names in the whitelist (e.g. ref_vector_search→vector_search, ref_tantric_remedies_get→query_tantric_remedies, search_classical_texts→read_classical_text, ref_yogas_get→no equivalent). Per LCA-2 the full-pipeline consult these route to is broken, so as-received first-contact = FAIL/not-probed. Only resolve_entity's advertised name matches a whitelisted primitive verbatim.

## resolve_entity — reachable-surgical — synthesizability PASS / receipt HONEST
First probe with `{"query":"Saturn"}` errored: `"name is required"` (param name is `name`, not `query`; minor tribal-knowledge friction but error is self-remediating). Retry with `name`:

```json
{"ok":true,"epistemics":{"surgical":true,"confidence_band":"high"},
"result":{"tool_name":"resolve_entity","tool_version":"1.0",
"invocation_params":{"chart_id":"...","name":"Saturn"},
"results":[{"content":"{\"canonical_id\":\"saturn\",\"entity_class\":\"planet\",\"canonical_name_en\":\"Saturn\",\"canonical_name_sa\":\"Shani\",\"synonyms\":[\"shani\",\"sani\",\"Saturn\",\"shanaischar\",\"manda\",\"Shanaischara\"],\"description\":\"Karma, discipline, longevity, delays; natural malefic\",\"source_citation\":\"BPHS (Brihat Parasara Hora Sastra), classical tradition\"}"}],
"served_from_cache":false,"latency_ms":68,
"result_hash":"sha256:781bfbbe..","schema_version":"1.0"}}
```
- Synthesizability PASS: self-describing, cited (source_citation=BPHS), composable to one sentence on first contact: "Saturn → canonical_id `saturn`, a planet (Shani), signifying karma/discipline/longevity/delays, a natural malefic (BPHS)."
- Receipt HONEST: no counters/truncated flags claimed; results[] length (1) matches payload; result_hash + schema_version present; epistemics.surgical=true is accurate.
- Minor: payload double-encodes the entity as a JSON string inside `content` (stringly-typed), forcing a second parse — friction, not a failure.
