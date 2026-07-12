# Shard 1a4-b4 — FUSED Lane 1a (synthesizability-as-received) + Lane 4 (receipt honesty)

Charter: CHARTER.md §7.2 (synthesizability-as-received), §4 taxonomy, §6 finding schema.
Chart probed: 482012f1-710e-4a25-994a-93821f5871aa (native).
Wire: POST http://localhost:3000/api/mcp/primitives/<tool> (surgical channel).

## Census — 11/11 tools probed (rider 1, 100%, no skips)

Tools: get_dashas, get_domain_reading, get_graha_yuddha, get_positions, get_projections,
get_remedies, get_signals, get_temporal_windows, graha_portrait, holistic_bundle_chart_facts,
intent_classify.

## Result: ALL 11 are served-only-by-down-pipeline

Every one of the 11 tools returned an identical validation rejection on the surgical wire:

```json
{"ok":false,"trace_id":"","error":{"class":"validation",
 "message":"Tool not in surgical whitelist: <tool>",
 "remediation":"Use ask_madhav for full-pipeline queries. Surgical primitives are: query_chart_facts, query_signals, query_dasha_periods, query_panchanga, query_ephemeris, query_transit_event, lel_query, vector_search, get_cgm_subgraph, cross_school_lookup, read_classical_text, query_varshphal, query_divisional_chart, query_remedial_mantras, muhurta_finder, query_varshaphala, divisional_query, remedial_codex_query, query_muhurat, query_tara_balam, query_chandra_balam, jaimini_chara_dasha, jaimini_chara_dasha_full, msr_sql, temporal, kp_query, query_kp_ruling_planets, pattern_register, resonance_register, cluster_atlas, contradiction_register, query_ucn_walk, query_cdlm_lookup, query_rm_walk, query_jaimini_drishti, timeline_query, query_signal_state, resolve_entity, list_entities, query_remedies, query_remedies_for_chart, list_remedies_by_category, read_remedy, query_tantric_remedies, query_remedies_by_planet, query_mantras, mitigation_map, query_calibration"}}
```

### Cross-check against surgical whitelist
None of the 11 assigned tools appear in the whitelist enumerated in the remediation string.
They are a distinct naming family (`get_*` / `graha_portrait` / `holistic_bundle_*` /
`intent_classify`) — the higher-level pipeline-fronting/orchestration tools, NOT surgical
primitives. Therefore:
- channel = **served-only-by-down-pipeline** for all 11.
- synthesizability-as-received = **not-probed** (payload unreachable via surgical channel;
  the only advertised path is `ask_madhav` full-pipeline, whose consult path is documented
  broken per LCA-2).
- receipt_honesty = **n/a** (no payload emitted — only a validation envelope).

### Note on the validation envelope itself (Lane 4 aside)
The rejection envelope is honest about its own state: `ok:false`, `class:"validation"`, and a
literal remediation. `trace_id:""` is empty (a minor observability gap — a rejected surgical
call produces no traceable id), noted but not graded as receipt-dishonesty since no coverage
counter/flag is being misrepresented.

### Rate-limit observation (operational, not a tool defect)
Surgical wire enforces 60 RPM; batched probing tripped `class:"rate_limit"` and required
spacing (~6s between calls) to complete the census. Recorded for RESUME/throttle awareness.

## Findings (tagged lane 1a / lane 4)

All 11 tools produce ONE structural finding each (identical mechanism): the tool is advertised
in the MCP surface but is unreachable in the surgical/consult channel and is only served by the
full `ask_madhav` pipeline, whose consult path is broken (LCA-2). Per Charter §4 this is a
class-1 (UNREACHABLE) condition scoped to the surgical channel, with a class-9 (UNGOVERNED
JUDGMENT) rider: a consuming LLM handed these tool descriptions has no in-band signal that the
tool cannot be exercised except via the down pipeline — it must improvise that knowledge.

Aggregate finding: an entire 11-tool family of pipeline-fronting MCP tools is unconsumable in
the surgical channel; combined with LCA-2 (broken consult path) these tools are effectively
unconsumable end-to-end at audit time. This is a lane-1a coverage/reachability wall, not a
per-tool payload defect (no payloads could be graded).

No DEAD-19 tools and no known-defect live tools (query_chart_facts, msr_sql) fell in this
shard's assignment — LCA-1/-3/-7 cited by reference only, not re-derived.
