# WIRE shard-1a4-b1 — FUSED Lane 1a (synthesizability-as-received, §7.2) + Lane 4 (receipt honesty)

Charter: LLM_CONSUMPTION_AUDIT_CHARTER v1.1, §7.2 / §7.1 / §4. Surgical wire probe, chart 482012f1-710e-4a25-994a-93821f5871aa.
Cross-refs cited (NOT re-derived): LCA-1 (DEAD-19), LCA-2 (ask_madhav full-pipeline consult broken), LCA-3 (query_chart_facts), LCA-7 (msr_sql).

## Assigned tools (11): all bodha_* + catalog_* — 100% probed, no skips

| tool | probe result | channel | synthesizability | receipt_honesty |
|---|---|---|---|---|
| bodha_discoveries_get | "Tool not in surgical whitelist" | served-only-by-down-pipeline | not-probed | n/a |
| bodha_domain_reading_get | "Tool not in surgical whitelist" | served-only-by-down-pipeline | not-probed | n/a |
| bodha_graph_subgraph_get | "Tool not in surgical whitelist" | served-only-by-down-pipeline | not-probed | n/a |
| bodha_graph_traverse_get | "Tool not in surgical whitelist" | served-only-by-down-pipeline | not-probed | n/a |
| bodha_quality_get | "Tool not in surgical whitelist" | served-only-by-down-pipeline | not-probed | n/a |
| bodha_remedies_get | "Tool not in surgical whitelist" | served-only-by-down-pipeline | not-probed | n/a |
| bodha_remedies_search | "Tool not in surgical whitelist" | served-only-by-down-pipeline | not-probed | n/a |
| bodha_signals_get | "Tool not in surgical whitelist" | served-only-by-down-pipeline | not-probed | n/a |
| catalog_assets_all | "Tool not in surgical whitelist" | served-only-by-down-pipeline | not-probed | n/a |
| catalog_assets_l0 | "Tool not in surgical whitelist" | served-only-by-down-pipeline | not-probed | n/a |
| catalog_assets_list | "Tool not in surgical whitelist" | served-only-by-down-pipeline | not-probed | n/a |

All 11 probed once each (chart_id param). Uniform result: full-pipeline-only. None DEAD-19 (LCA-1), none in surgical whitelist.

## Verbatim evidence (E-6), representative — identical error class across all 11

```
{"ok":false,"trace_id":"","error":{"class":"validation",
 "message":"Tool not in surgical whitelist: bodha_discoveries_get",
 "remediation":"Use ask_madhav for full-pipeline queries. Surgical primitives are:
  query_chart_facts, query_signals, query_dasha_periods, query_panchanga, query_ephemeris,
  query_transit_event, lel_query, vector_search, get_cgm_subgraph, cross_school_lookup,
  read_classical_text, query_varshphal, query_divisional_chart, query_remedial_mantras,
  muhurta_finder, query_varshaphala, divisional_query, remedial_codex_query, query_muhurat,
  query_tara_balam, query_chandra_balam, jaimini_chara_dasha, jaimini_chara_dasha_full,
  msr_sql, temporal, kp_query, query_kp_ruling_planets, pattern_register, resonance_register,
  cluster_atlas, contradiction_register, query_ucn_walk, query_cdlm_lookup, ..."}}
```

The remediation-declared surgical whitelist contains NO bodha_* and NO catalog_* tool. All 11
assigned tools are served ONLY through the full ask_madhav pipeline (LCA-2: pipeline/consult broken).

## Findings

FUSED-1a4-b1 (lane 1a + lane 4): All 11 assigned MCP tools — 8 bodha_* (signals, domain_reading,
discoveries, graph_traverse, graph_subgraph, quality, remedies_get, remedies_search) + 3 catalog_*
(assets_all, assets_l0, assets_list) — are full-pipeline-only. Per LCA-2 the ask_madhav / consult
path is BROKEN, so this entire consumption surface is unreachable on the surgical wire and
un-consumable via the down pipeline. Synthesizability cannot be first-contact-probed (§7.2 requires
a real payload); receipt honesty n/a (no payload). Channel: served-only-by-down-pipeline. Failure
class: primary class 1 UNREACHABLE (retrieval plane — reachable only via a down path). Suspected
layer: MCP contract (whitelist) + serving-query (pipeline down per LCA-2). Distinct from DEAD-19
(LCA-1): these return "Tool not in surgical whitelist" (registered concept, pipeline-gated), not
"Retrieval tool not found in registry".

Coverage-honesty note (§8 crit 4 / §2.1 source 2): the catalog_* family IS the system's own
asset-inventory surface — the enumeration substrate the audit doctrine relies on. Its being
pipeline-only means the LLM cannot even enumerate the system's assets on the surgical channel.
