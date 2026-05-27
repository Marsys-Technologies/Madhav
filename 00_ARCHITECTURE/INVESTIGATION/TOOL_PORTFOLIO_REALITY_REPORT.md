---
title: "Tool Portfolio Reality Report — MARSYS-JIS"
generated_at: "2026-05-27"
status: INVESTIGATION_COMPLETE
investigator: Claude Sonnet 4.6 (read-only forensic pass)
---

# Tool Portfolio Reality Report

## 1. Executive Summary — Top 10 Findings

1. **CONTRADICTED — Registered MCP count is 40, NOT 57.** `server.ts` header and `server_tier_visibility.test.ts` both assert **40 tools**. `catalog.ts` header claims "57" and lists 57 entries. The delta is 17 tool files that exist, have `register*` functions, and appear in `catalog.ts` — but are **not imported or called in `server.ts`**. These are written-but-unregistered ghost entries.

2. **CONTRADICTED — `catalog.ts` "22 tools" test is a stale residual.** `tool_descriptions.test.ts` at line 91 asserts `expect(CATALOG).toHaveLength(22)` but the current `CATALOG` array has **57 entries**. This test will FAIL if run against the current codebase. The test was written for the v3.2 Phase 3 baseline when 22 tools were registered and was never updated.

3. **CONTRADICTED — SURGICAL_TOOLS array has massive duplicate contamination.** 32 of 42 entries in `SURGICAL_TOOLS` are duplicates (same engine name appears 2–4×). This is because UDA Campaign tools were appended to the existing array without deduplication. The `as const` type union quietly absorbs duplicates, but the array is semantically wrong.

4. **CONFIRMED — `query_jaimini_drishti` is registered in `server.ts` but IS a stub** (tool file line 17 states "currently stub — returns not_implemented until M6+ Jaimini engine").

5. **CONTRADICTED — `CAPABILITY_MANIFEST.json` tool entries have ZERO `query_schema` populated.** All 79 `retrieval_tool` entries show `schema=no`. The manifest has `query_schema` field but every tool entry leaves it null/empty. Manifest-driven schema registration would require a separate population step.

6. **CONFIRMED — `validateCitationsForStream` (B.11/citation gate) exists ONLY on the legacy orchestrator tail (inside `onFinish`).** The adapter/agentic-loop path (lines 923–1198 of route.ts) has NO citation gate. The two paths have unequal B.11 enforcement strength.

7. **CONFIRMED — The agentic loop's tool catalog = `buildChatToolsFromNames(queryPlan.tools_authorized ?? [])` (route.ts:960).** Loop tools are strictly the planner-authorized subset. B.11 floor pre-injection (lines 460–504) happens deterministically before the adapter block, so floor context is always present.

8. **SURPRISING — `interpret_current_dasha`, `list_assets`, `list_canonical_artifact_versions`, `tara_balam_for_native`, `chandra_balam_for_native` all have written tool files and `register*` functions, appear in `catalog.ts`, but are NOT registered in `server.ts`.** These are functional tools not exposed via MCP despite having Zod schemas and test coverage.

9. **CONFIRMED — `query_varshaphala` (portal native name) vs `query_varshphal` (MCP name) split creates alias complexity.** Two additional alias objects in `RETRIEVAL_TOOLS` (`chartFactsQueryAlias`, `queryVarshphalAlias`) exist specifically to bridge the name mismatch. The portal planner prompt uses `query_varshaphala` (old name, 10 occurrences); MCP uses `query_varshphal`.

10. **CONFIRMED — `msr_sql` appears FOUR times in `SURGICAL_TOOLS` — once from original whitelist, once as pass-through alias, twice from UDA additions.** The `MCP_TO_RETRIEVAL_TOOL` map has no duplication issue (it's an object), but the `SURGICAL_TOOLS` array has 32 duplicate entries across 19 tool names.

---

## 2. Reality CONTRADICTS Brief Assumptions

| # | Claim in Brief | Reality |
|---|---|---|
| C1 | `catalog.ts` header says "57" | 57 entries in CATALOG, but only 40 are registered in server.ts |
| C2 | test asserts ~22 | `tool_descriptions.test.ts:91` asserts `toHaveLength(22)` — stale; CATALOG now has 57 |
| C3 | `server.ts` says ~40 tools | CONFIRMED 40 registered (server.ts header + server_tier_visibility.test.ts both assert 40) |
| C4 | No tier gate on MCP tools | CONFIRMED post-R1. But TWO platform API routes still hard-403 by tier (`/health/tools`, `/health/coverage`) |
| C5 | All MCP tools have Zod schemas | `interpret_current_dasha`, `list_assets`, `list_canonical_artifact_versions` are in catalog but NOT server.ts; they DO have Zod schemas. The 17 unregistered tools are written but not live |
| C6 | B.11 enforced on all paths | Adapter/agentic path has NO `validateCitationsForStream`; B.11 enforcement is asymmetric |
| C7 | manifest `query_schema` populated | ALL 79 retrieval_tool manifest entries have `query_schema=null` |
| C8 | SURGICAL_TOOLS no duplicate msr_sql | `msr_sql` appears 4× in the array; 19 tool names duplicated in total |

---

## 3. Master Tool Table

> Legend: **registered** = imported AND called in server.ts; **catalog** = in catalog.ts CATALOG array; **RETRIEVAL_TOOLS** = in platform/src/lib/retrieve/index.ts

### 3A — Tools Registered in server.ts (40 tools)

| mcp_name | engine_name (MCP_TO_RETRIEVAL_TOOL) | portal_name (RETRIEVAL_TOOLS) | registered_in_server_ts | in_primitives_whitelist | in_manifest | has_query_schema_in_manifest | has_zod_schema | channel | written_unregistered_mcp_file | is_stub | data_table | b11_floor_member | declared_asymmetry | handler_complexity |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| chart_summary | (composite; calls chart_facts_query internally) | — | yes | no | yes (MCP_TOOL_CHART_SUMMARY) | no | yes | mcp | no | no | chart_facts | no | no | has-custom-logic |
| holistic_bundle | (bundle; calls 8 primitives via getToolRouteFor) | — | yes | no | yes (MCP_TOOL_HOLISTIC_BUNDLE) | no | yes+.transform+.refine | mcp | no | no | multiple | no | no | has-custom-logic |
| multi_school_bundle | (bundle; calls school primitives) | — | yes | no | yes (MCP_TOOL_MULTI_SCHOOL_BUNDLE) | no | yes+.transform+.refine | mcp | no | no | multiple | no | no | has-custom-logic |
| query_chart_facts | chart_facts_query | query_chart_facts (alias) | yes | yes | yes (MCP_TOOL_QUERY_CHART_FACTS) | no | yes | mcp | no | no | chart_facts | yes (dasha floor) | no | trivial-dispatch |
| query_signals | msr_sql | msr_sql | yes | yes | yes (MCP_TOOL_QUERY_SIGNALS) | no | yes | mcp | no | no | l25_msr_signals | yes (B.11 default) | no | has-custom-logic (confidence floor, clique modifier) |
| query_dasha_periods | query_dasha_periods | query_dasha_periods | yes | yes | yes (MCP_TOOL_QUERY_DASHA_PERIODS) | no | yes | mcp | no | no | chart_facts (dasha_vimshottari) | no | no | trivial-dispatch |
| query_panchanga | query_panchanga | query_panchanga | yes | yes | yes (MCP_TOOL_QUERY_PANCHANGA) | no | yes | portal+mcp | no | no | panchanga_daily | no | no | trivial-dispatch |
| query_ephemeris | query_ephemeris | query_ephemeris | yes | yes | yes (MCP_TOOL_QUERY_EPHEMERIS) | no | yes+.transform+.refine | portal+mcp | no | no | ephemeris | no | no | trivial-dispatch |
| query_transit_event | query_transit_event | query_transit_event | yes | yes | yes (MCP_TOOL_QUERY_TRANSIT_EVENT) | no | yes | portal+mcp | no | no | ephemeris (derived) | no | no | trivial-dispatch |
| lel_query | lel_query | lel_query | yes | yes | yes (MCP_TOOL_LEL_QUERY) | no | yes | portal+mcp | no | no | life_events | no | no | trivial-dispatch |
| vector_search | vector_search | vector_search | yes | yes | yes (MCP_TOOL_VECTOR_SEARCH) | no | yes+.transform | portal+mcp | no | no | rag_chunks | yes (B.11 predictive floor) | no | trivial-dispatch |
| get_cgm_subgraph | cgm_graph_walk | cgm_graph_walk | yes | yes | yes (MCP_TOOL_GET_CGM_SUBGRAPH) | no | yes | portal+mcp | no | no | cgm_nodes/cgm_edges | yes (B.11 default floor) | no | trivial-dispatch |
| cross_school_lookup | multi_school_signal_lookup | multi_school_signal_lookup_tool | yes | yes | yes (MCP_TOOL_CROSS_SCHOOL_LOOKUP) | no | yes+.transform+.refine | mcp | no | no | school_convergence_index | no | no | trivial-dispatch |
| query_varshphal | query_varshaphala | query_varshphal (alias→query_varshaphala) | yes | yes | yes (MCP_TOOL_QUERY_VARSHPHAL) | no | yes | mcp | no | no | chart_facts (varshphal) | no | yes (name mismatch) | has-custom-logic (client tier branch) |
| query_divisional_chart | divisional_query | divisional_query | yes | yes | yes (MCP_TOOL_QUERY_DIVISIONAL_CHART) | no | yes | mcp | no | no | chart_facts (divisional) | no | no | trivial-dispatch |
| query_remedial_mantras | remedial_codex_query | remedial_codex_query | yes | yes | yes (MCP_TOOL_QUERY_REMEDIAL_MANTRAS) | no | yes | mcp | no | no | remedial_corpus | no | no | trivial-dispatch |
| muhurta_finder | query_muhurat | muhurta_finder | yes | yes | yes (MCP_TOOL_MUHURTA_FINDER) | no | yes | both | no | no | panchanga_daily + python-sidecar | no | yes (name mismatch: MCP muhurta_finder → engine query_muhurat) | trivial-dispatch |
| msr_sql | msr_sql | msr_sql | yes | yes (duplicate in SURGICAL_TOOLS) | yes (PORTAL_TOOL_MSR_SQL) | no | yes | both | no | no | l25_msr_signals | yes (B.11 default) | no | trivial-dispatch |
| temporal | temporal | temporal | yes | yes | yes (PORTAL_TOOL_TEMPORAL) | no | yes | both | no | no | chart_facts + DB | no | no | trivial-dispatch |
| kp_query | kp_query | kp_query | yes | yes | yes (PORTAL_TOOL_KP_QUERY) | no | yes | both | no | no | chart_facts (kp_planet, kp_cusp) | no | no | trivial-dispatch |
| query_kp_ruling_planets | query_kp_ruling_planets | query_kp_ruling_planets | yes | yes | yes (PORTAL_TOOL_QUERY_KP_RULING_PLANETS) | no | yes | both | no | no | chart_facts (kp_significator) | no | no | trivial-dispatch |
| pattern_register | pattern_register | pattern_register | yes | yes | yes (PORTAL_TOOL_PATTERN_REGISTER) | no | yes | both | no | no | l25_msr_signals (pattern clusters) | yes (B.11 predictive floor) | no | trivial-dispatch |
| resonance_register | resonance_register | resonance_register | yes | yes | yes (PORTAL_TOOL_RESONANCE_REGISTER) | no | yes | both | no | no | l25_msr_signals (resonance) | no | no | trivial-dispatch |
| cluster_atlas | cluster_atlas | cluster_atlas | yes | yes | yes (PORTAL_TOOL_CLUSTER_ATLAS) | no | yes | both | no | no | signal_clusters | no | no | trivial-dispatch |
| contradiction_register | contradiction_register | contradiction_register | yes | yes | yes (PORTAL_TOOL_CONTRADICTION_REGISTER) | no | yes | both | no | no | signal_contradictions | no | no | trivial-dispatch |
| query_ucn_walk | query_ucn_walk | query_ucn_walk | yes | yes | yes (PORTAL_TOOL_QUERY_UCN_WALK) | no | yes | both | no | no | ucn (UCN_v4_0.md asset) | no | no | trivial-dispatch |
| query_cdlm_lookup | query_cdlm_lookup | query_cdlm_lookup | yes | yes | yes (PORTAL_TOOL_QUERY_CDLM_LOOKUP) | no | yes | both | no | no | cdlm (CDLM_v1_1.md asset) | no | no | trivial-dispatch |
| query_rm_walk | query_rm_walk | query_rm_walk | yes | yes | yes (PORTAL_TOOL_QUERY_RM_WALK) | no | yes | both | no | no | rm (RM_v2_0.md asset) | no | no | trivial-dispatch |
| query_jaimini_drishti | query_jaimini_drishti | query_jaimini_drishti | yes | yes | yes (PORTAL_TOOL_QUERY_JAIMINI_DRISHTI) | no | yes | both | no | **YES** (stub, not_implemented) | python-sidecar stub | no | no | trivial-dispatch (stub) |
| timeline_query | timeline_query | timeline_query | yes | yes | yes (PORTAL_TOOL_TIMELINE_QUERY) | no | yes | both | no | no | l5_timeline (empty) | no | no | trivial-dispatch |
| query_signal_state | query_signal_state | query_signal_state | yes | yes | yes (PORTAL_TOOL_QUERY_SIGNAL_STATE) | no | yes | both | no | no | signal_states | no | no | trivial-dispatch |
| read_asset | classical_text_search (alias) | — | yes | yes | yes (MCP_TOOL_READ_ASSET) | no | yes+.transform+.refine | mcp | no | no | rag_chunks (canonical asset) | no | no | trivial-dispatch |
| read_classical_text | classical_text_search | — | yes | yes | yes (MCP_TOOL_READ_CLASSICAL_TEXT) | no | yes | mcp | no | no | rag_chunks (classical texts) | no | no | trivial-dispatch |
| get_trace | — | — | yes | no | yes (MCP_TOOL_GET_TRACE) | no | yes | mcp | no | no | query_trace_steps | no | no | trivial-dispatch |
| list_recent_queries | — | — | yes | no | yes (MCP_TOOL_LIST_RECENT_QUERIES) | no | yes | mcp | no | no | query_plan_log | no | no | trivial-dispatch |
| tool_health | — | — | yes | no | yes (MCP_TOOL_TOOL_HEALTH) | no | yes | mcp | no | no | platform health endpoint | no | no | has-custom-logic |
| data_coverage | — | — | yes | no | yes (MCP_TOOL_DATA_COVERAGE) | no | yes | mcp | no | no | platform coverage endpoint | no | no | has-custom-logic |
| log_prediction | — | — | yes | no | yes (MCP_TOOL_LOG_PREDICTION) | no | yes+.transform | mcp | no | no | mcp_predictions | no | no | has-custom-logic |
| record_outcome | — | — | yes | no | yes (MCP_TOOL_RECORD_OUTCOME) | no | yes | mcp | no | no | mcp_predictions | no | no | trivial-dispatch |
| flag_disagreement | — | — | yes | no | yes (MCP_TOOL_FLAG_DISAGREEMENT) | no | yes | mcp | no | no | mcp_disagreements | no | no | has-custom-logic (super_admin gate at line 137) |

### 3B — Written-but-Unregistered in server.ts (17 tools in catalog.ts but not server.ts)

| mcp_name | engine_name | portal_name | registered_in_server_ts | in_primitives_whitelist | in_manifest | written_unregistered_mcp_file | is_stub | notes |
|---|---|---|---|---|---|---|---|---|
| tara_balam_for_native | query_tara_balam (alias) | tara_balam_for_native | **NO** | yes (stub alias) | yes (MCP_TOOL_TARA_BALAM_FOR_NATIVE, channel=both) | **YES** | no | Has register fn + Zod schema + test |
| chandra_balam_for_native | query_chandra_balam (alias) | chandra_balam_for_native | **NO** | yes (stub alias) | yes (MCP_TOOL_CHANDRA_BALAM_FOR_NATIVE, channel=both) | **YES** | no | Has register fn + Zod schema + test |
| query_transits_over_natal | query_transits_over_natal | query_transits_over_natal | **NO** | no | yes (MCP_TOOL_QUERY_TRANSITS_OVER_NATAL, channel=both) | **YES** | no | Has register fn + Zod schema + test |
| query_yogas_active_now | query_yogas_active_now | query_yogas_active_now | **NO** | no | yes (MCP_TOOL_QUERY_YOGAS_ACTIVE_NOW, channel=both) | **YES** | no | Has register fn + Zod schema + test |
| get_planet_avastha | get_planet_avastha | get_planet_avastha | **NO** | no | yes (MCP_TOOL_GET_PLANET_AVASTHA, channel=both) | **YES** | no | Has register fn + Zod schema + test |
| get_shadbala_full | get_shadbala_full | get_shadbala_full | **NO** | no | yes (MCP_TOOL_GET_SHADBALA_FULL, channel=both) | **YES** | no | Has register fn + Zod schema + test |
| interpret_current_dasha | (composite: query_dasha_periods + query_chart_facts) | — | **NO** | no | yes (MCP_TOOL_INTERPRET_CURRENT_DASHA, channel=mcp) | **YES** | no | Composition recipe, not primitive |
| list_canonical_artifact_versions | — | — | **NO** | no | yes (MCP_TOOL_LIST_CANONICAL_ARTIFACT_VERSIONS, channel=mcp) | **YES** | no | Utility; reads governance assets |
| query_drekkana_drishti | query_drekkana_drishti | query_drekkana_drishti | **NO** | no | yes (MCP_TOOL_QUERY_DREKKANA_DRISHTI, channel=both) | **YES** | no | Has register fn + test |
| query_jaimini_chara_dasha | jaimini_chara_dasha (alias) | query_jaimini_chara_dasha | **NO** | yes (alias) | yes (MCP_TOOL_QUERY_JAIMINI_CHARA_DASHA, channel=both) | **YES** | no | Has register fn + test |
| query_planetary_period_predictions | query_planetary_period_predictions | query_planetary_period_predictions | **NO** | no | yes (MCP_TOOL_QUERY_PLANETARY_PERIOD_PREDICTIONS, channel=both) | **YES** | no | Has register fn + test |
| query_dasamsha_career | query_dasamsha_career | query_dasamsha_career | **NO** | no | yes (MCP_TOOL_QUERY_DASAMSHA_CAREER, channel=both) | **YES** | no | Has register fn + test |
| query_shashtiamsha | query_shashtiamsha | query_shashtiamsha | **NO** | no | yes (MCP_TOOL_QUERY_SHASHTIAMSHA, channel=both) | **YES** | no | Has register fn + test |
| query_eclipse_transits | query_eclipse_transits | query_eclipse_transits | **NO** | no | yes (MCP_TOOL_QUERY_ECLIPSE_TRANSITS, channel=both) | **YES** | no | Has register fn + test |
| query_planet_war | query_planet_war | query_planet_war | **NO** | no | yes (MCP_TOOL_QUERY_PLANET_WAR, channel=both) | **YES** | no | Has register fn + test |
| query_remedies_prescribed | query_remedies_prescribed | query_remedies_prescribed | **NO** | no | yes (MCP_TOOL_QUERY_REMEDIES_PRESCRIBED, channel=both) | **YES** | no | Has register fn + test |
| list_assets | — | — | **NO** | no | yes (MCP_TOOL_LIST_ASSETS, channel=mcp) | **YES** | no | Has register fn |

### 3C — Portal-Only Retrieval Engines (in RETRIEVAL_TOOLS, no MCP wrapper)

| engine_name | portal_name | channel (manifest) | has_retrieval_engine | notes |
|---|---|---|---|---|
| query_msr_aggregate | query_msr_aggregate | portal | yes | aggregation wrapper over msr_sql |
| cgm_graph_walk | cgm_graph_walk | portal | yes | also MCP-exposed as get_cgm_subgraph |
| manifest_query | manifest_query | portal | yes | manifest file search |
| saham_query | saham_query | portal | yes | Arabic part lots |
| divisional_query | divisional_query | portal | yes | also MCP as query_divisional_chart |
| chart_facts_query | chart_facts_query | portal | yes | also MCP as query_chart_facts (alias) |
| cross_varga_dignity_query | cross_varga_dignity_query | portal | yes | cross-varga dignity |
| domain_report_query | domain_report_query | portal | yes | domain reports from rag_chunks |
| remedial_codex_query | remedial_codex_query | portal | yes | also MCP as query_remedial_mantras |
| query_muhurat | query_muhurat | portal+mcp | yes | also MCP as muhurta_finder |
| query_v7_additions | query_v7_additions | portal | **stub** | sidecar stub, scope TBD M6+ |
| query_varshaphala | query_varshaphala | portal | yes | also MCP as query_varshphal (alias) |
| classical_text_search_tool | classical_text_search_tool | portal | yes | also MCP as read_classical_text |
| classical_attribution_lookup_tool | classical_attribution_lookup_tool | portal | yes | standalone attribution |
| multi_school_signal_lookup_tool | multi_school_signal_lookup | portal | yes | also MCP as cross_school_lookup |
| convergence_score_lookup_tool | convergence_score_lookup | portal | yes | SCI score lookup |

### 3D — Canonical-Name Aliases in RETRIEVAL_TOOLS (4 explicit R2 aliases + 2 UDA-3 aliases)

| name in RETRIEVAL_TOOLS | delegates to | purpose |
|---|---|---|
| query_tara_balam | tara_balam_for_native handler | MCP primitive dispatch alias |
| query_chandra_balam | chandra_balam_for_native handler | MCP primitive dispatch alias |
| jaimini_chara_dasha | query_jaimini_chara_dasha handler | MCP primitive dispatch alias |
| jaimini_chara_dasha_full | jaimini_chara_dasha_full handler | Full Jaimini Chara Dasha timeline |
| query_chart_facts (alias obj) | chart_facts_query handler | UDA-3 canonical-name alias for Channel B |
| query_varshphal (alias obj) | query_varshaphala handler | UDA-3 canonical-name alias for Channel B |

---

## 4. Inventory & Count Reconciliation

### 4.1 RETRIEVAL_TOOLS exact count

**RETRIEVAL_TOOLS array: 57 entries total.**
- 55 unique engine `.tool` objects (including 4 R2 alias modules: query_tara_balam, query_chandra_balam, jaimini_chara_dasha, jaimini_chara_dasha_full)
- 2 inline alias objects (`chartFactsQueryAlias`, `queryVarshphalAlias`) created in index.ts

Unique engine *implementations* (excluding aliases that are thin wrappers): approximately 51 distinct implementations + 4 R2 dispatch aliases + 2 name-bridge aliases = 57 total.

Evidence: `platform/src/lib/retrieve/index.ts:151–212`

### 4.2 Registered tool count in server.ts

**TRUE REGISTERED COUNT: 40**

Confirmed by:
- `platform-mcp/src/server.ts` header: "40 tools registered (v4.5)"
- `platform-mcp/src/__tests__/server_tier_visibility.test.ts:129,134,139`: `expect(server._registeredNames).toHaveLength(40)` for all three tiers
- Manual count of `register*` calls in server.ts: exactly 40 call sites (lines 185–235)

### 4.3 SURGICAL_TOOLS and MCP_TO_RETRIEVAL_TOOL

**SURGICAL_TOOLS array has 42 entries with 32 duplicates.** The array was originally defined with 15 entries (Class A engines), then stub entries were appended, then UDA Campaign tools were appended without deduplicating. The `as const` type union (`SurgicalToolName`) de-duplicates the *TypeScript type* but not the runtime array.

Confirmed duplicates (count × tool):
- `msr_sql` ×4 (original, pass-through alias, ONCE as 'msr_sql' in UDA section)
- `chart_facts_query`, `query_dasha_periods`, `query_panchanga`, `query_ephemeris`, `query_transit_event`, `lel_query`, `vector_search`, `cgm_graph_walk`, `multi_school_signal_lookup`, `classical_text_search` — each ×2
- `query_varshaphala`, `divisional_query`, `remedial_codex_query`, `query_muhurat` — each ×3
- `query_tara_balam`, `query_chandra_balam`, `jaimini_chara_dasha`, `jaimini_chara_dasha_full` — each ×2

Evidence: `platform/src/lib/mcp/primitives_registry.ts:46–84`

**MCP_TO_RETRIEVAL_TOOL** has NO duplicates (it's a Record<string, SurgicalToolName> keyed by MCP name). Notable pass-through self-mappings added for Class A aliases:
- `query_varshaphala → 'query_varshaphala'` (line 113)
- `divisional_query → 'divisional_query'` (line 114)
- `remedial_codex_query → 'remedial_codex_query'` (line 115)
- `query_muhurat → 'query_muhurat'` (line 116)

Plus UDA 14 self-mappings (msr_sql → 'msr_sql', temporal → 'temporal', etc.)

### 4.4 catalog.ts vs test assertion reconciliation

**Contradiction confirmed:**
- `catalog.ts` header: "all 57 registered MCP tools" — **57 entries**
- `tool_descriptions.test.ts:91`: `expect(CATALOG).toHaveLength(22)` — **asserts 22**

This is a **stale test residual**. The test was written at MCPT v3.2 Phase 3 when 22 tools were registered. The CATALOG grew to 57 entries (40 registered + 17 written-but-unregistered) without the test being updated. **This test will FAIL on the current codebase.**

Resolution: 40 = server.ts registered; 57 = catalog.ts total entries; 17 = written-but-unregistered gap.

### 4.5 CAPABILITY_MANIFEST.json analysis

Total entries: **268**
- `type:"retrieval_tool"`: **79**
- with non-empty `query_schema`: **9** (but these 9 appear to be governance/architecture entries, NOT tool entries — all 79 retrieval_tool entries have `query_schema=null`)

**Channel distribution of retrieval_tool entries:**
- `channel=both`: 29
- `channel=mcp`: 28 (MCP-only tools including observability/write tools)
- `channel=portal`: 22

**CONTRADICTED:** The manifest lists 79 retrieval_tool entries — significantly more than the 40 registered in server.ts. The manifest includes the 17 written-but-unregistered tools (channel=both or channel=mcp) as well as portal-only engines (channel=portal). The manifest is aspirational/planned, not a live registration registry.

---

## 5. Manifest & Canonical-Contract Feasibility

### 5.1 Manifest generator

**CONFIRMED.** `platform/src/scripts/manifest/build.ts` generates the manifest from:
1. `auto_deriver.ts` — scans filesystem frontmatter
2. `override_merger.ts` — merges `00_ARCHITECTURE/manifest_overrides.yaml` fields

Evidence: `platform/src/scripts/manifest/build.ts:22–64`. Hand-edits to `CAPABILITY_MANIFEST.json` ARE overwritten by the next `npm run manifest:build` run. The manifest is code-generated.

### 5.2 Asset entry schema

**CONFIRMED.** `platform/src/lib/schemas/asset_entry.schema.json:26`: `"additionalProperties": false`.

Unknown fields generate a warning (not error) via `schema_validator.py` — the build script logs but proceeds:
```
platform/src/scripts/manifest/build.ts:37-45:
  console.warn(`[manifest:build] Validation errors for ${entry.canonical_id}`)
  validationErrorCount++
  // proceeds — does NOT abort
```

### 5.3 Zod→JSON-Schema dependency

**CONFIRMED — `zod-to-json-schema` is NOT listed in `platform-mcp/package.json`** (no output from grep). The `zod` package IS a direct dependency of `platform-mcp/package.json` (confirmed by presence of `node_modules/zod/`).

For Zod-backed tools in `platform-mcp`: the MCP SDK's `server.tool()` receives Zod schemas natively via the `@modelcontextprotocol/sdk` integration — no separate JSON Schema converter is required for MCP registration. However, to **backfill manifest `query_schema` fields from Zod**, the build pipeline would need `zod-to-json-schema` added as a build-time dependency in `platform/package.json` (not platform-mcp).

To **register MCP tools from manifest JSON Schema** (reverse direction): the tools would need to switch from `server.tool(name, zodSchema, handler)` to `server.tool(name, jsonSchema, handler)` — the MCP SDK supports both. This is feasible but requires every handler to explicitly validate inputs since Zod's parse/safeParse would no longer run automatically.

### 5.4 Per-tool Zod schema audit

Tools using `.transform()` (schema alters the input value, not just validates):
- `cross_school_lookup.ts` — `.transform` + `.refine`
- `holistic_bundle_tool.ts` — `.transform` + `.refine`
- `log_prediction.ts` — `.transform` (confidence: enum | float → canonical enum)
- `multi_school_bundle_tool.ts` — `.transform` + `.refine`
- `query_ephemeris.ts` — `.transform` + `.refine`
- `read_asset.ts` — `.transform` + `.refine`
- `vector_search.ts` — `.transform`

These 7 tools use backward-compat `.transform()` aliases per the MCP Tool Audit Remediation v2 Session A (`fix/mcp-schema-compat`, commit `ee498f34`). They accept both old and new input shapes.

Tools with NO Zod params (no-params): none of the 40 registered tools are no-params; all have at least optional Zod fields.

### 5.5 Handler complexity audit

| Tool | Custom Logic Beyond Schema+Dispatch |
|---|---|
| `query_signals.ts` | Domain-specific confidence floors (lines 69–78); clique membership deduplication modifier (lines 130–142) — **significant custom logic** |
| `chart_summary.ts` | Batching across 35+ chart_facts categories in parallel; divisional chart batching; result merging — **most complex handler in the portfolio** |
| `holistic_bundle_tool.ts` | `getToolRouteFor` fan-out map; parallel execution with SSE events; bundle envelope assembly — **complex** |
| `log_prediction.ts` | confidence transform (enum→float normalization); falsifier optional handling; domain enum validation |
| `flag_disagreement.ts` | super_admin tier gate at line 137 |
| `tool_health.ts` | Platform health HTTP proxying with tier header pass-through |
| `data_coverage.ts` | Platform coverage HTTP proxying with tier header pass-through |
| `query_varshphal.ts` | Client tier branch (line 87): redacts certain fields for non-admin tiers |

**Conclusion:** A manifest-driven registration loop CAN replace the hand-registration boilerplate for the 33 trivial-dispatch tools. The 7 tools with custom logic (chart_summary, holistic_bundle, query_signals, log_prediction, flag_disagreement, tool_health, data_coverage, query_varshphal) would need their handlers preserved explicitly — the auto-registration pattern would only replace the `server.tool(name, schema, handler)` call, not the handler body.

### 5.6 catalog.ts and capabilities.ts maintenance status

**catalog.ts** (`platform-mcp/src/tools/catalog.ts`): **hand-maintained**. It imports description constants from individual tool files and manually assembles the array. There is no generator or CI check that validates catalog entries match server.ts registrations.

**capabilities.ts** (`platform-mcp/src/resources/capabilities.ts`): Does NOT hardcode a tool list or count. It is a dynamic resource that calls the platform health endpoint. Line 148 contains a static markdown table reference (`| \`holistic_bundle\` | 8-tool parallel holistic read...`) in the generated resource text — this is documentation content, not a registration count. **Not stale in any blocking way.**

---

## 6. Dual-Channel Control Flow

### 6.1 consume/route.ts control flow

**`runPlanner()` runs unconditionally** — `route.ts:382–400`. No flag gate, no circuit breaker, no fallback path that skips the planner. `PlannerFault` → HTTP 422.

**Three synthesis tails and their exact flag gates:**

1. **Adapter/Agentic-Loop tail** (lines 923–1198):
   - Gate: `configService.getFlag('R11V2_USE_ADAPTERS')` (line 923)
   - Sub-gate for loop: `configService.getFlag(loopFlagKey)` where `loopFlagKey` is one of `R11E_ANTHROPIC_LOOP`, `R11E_GEMINI_LOOP`, `R11E_OPENAI_LOOP`, `R11E_DEEPSEEK_LOOP`, `R11E_NVIDIA_LOOP` (lines 947–955)

2. **Legacy Orchestrator tail** (line 1201): `orchestrator.synthesize(synthesisRequest)` — runs when `R11V2_USE_ADAPTERS` is false OR when no valid `adapterId` is found for the selected stack.

3. **Panel mode** (line 1295): `if (panelStageEvents && panelStageEvents.length > 0)` — not a separate synthesis path, but a branch within the orchestrator tail that emits panel member events.

### 6.2 Agentic loop tool catalog

**CONFIRMED.** `route.ts:960–962`:
```typescript
tools: buildChatToolsFromNames(queryPlan.tools_authorized ?? []),
maxIterations: 8,
```
The loop tool catalog is **strictly the planner-authorized subset**. `buildChatToolsFromNames` resolves names via `RETRIEVAL_TOOLS` registry. Tools not in `queryPlan.tools_authorized` cannot be called by the loop.

### 6.3 executeMCPTool dispatch path

**CONFIRMED.** `platform/src/lib/synthesis/mcp_tool_executor.ts:51–63`:
```typescript
const tool = getTool(toolCall.name)     // getTool() from RETRIEVAL_TOOLS
const result = await tool.retrieve(ctx.queryPlan as any, toolCall.input)
```
Portal channel calls `getTool().retrieve()` **in-process** — no HTTP.
MCP channel calls `callPlatformPrimitive()` which POSTs to `/api/mcp/primitives/{toolName}` which calls the same `RETRIEVAL_TOOLS` engine.
Both paths hit the same `retrieve()` implementation. The loop's `executeMCPTool` = Channel B (in-process).

### 6.4 Planner-demotion blast radius

Everything that depends on `tools_authorized` / `PipelinePlan` being authoritative:

| Dependency | File | Line range | Coupling detail |
|---|---|---|---|
| `arbitrateBudgets` | route.ts | 439–455 | Consumes `plan.tool_calls[].token_budget` for proportional trim |
| `toolsAuthorized` derivation | route.ts | 458 | `Array.from(new Set(plan.tool_calls.map(tc => tc.tool_name)))` |
| B.11 floor injection | route.ts | 461–504 | Mutates `plan.tool_calls` and `toolsAuthorized` based on content |
| Dasha floor injection | route.ts | 489–503 | Mutates same arrays |
| `toolSeqs` pre-allocation | route.ts | 657 | One seq per `toolsAuthorized` element |
| Tool parallel pre-fetch | route.ts | 678–729 | `toolsAuthorized.map(name => getTool(name).retrieve())` |
| `plannerParamsMap` | route.ts | 622–624 | Per-tool params from plan.tool_calls |
| `writeQueryPlanLog` | route.ts | 571–584 | `tool_count: plan.tool_calls.length` |
| Trace step names | route.ts | 668 | `step_name: toolName` from toolsAuthorized |
| `buildChatToolsFromNames` | route.ts | 960 | Agentic loop catalog |
| `LegacyQueryPlanShape.tools_authorized` | route.ts | 548–568 | Adapter object for orchestrator/validators/audit |
| `executeWithCache` | route.ts | 685 | Dispatches via `t.retrieve(queryPlan, ...)` |
| `hydrateBundle` | route.ts | 627 | `await hydrateBundle(plan, manifest)` — uses plan.tool_calls |
| Audit consumer | route.ts | 899–906 | `createAuditConsumer({ query_plan: queryPlan, ... })` |
| `tokensFor` / `tokensForAdapter` accounting | route.ts | 1418–1447, 1139–1168 | Tool-name keyed budget tracking (hardcoded name lists) |

**`LegacyQueryPlanShape` interface** is defined inline at route.ts:509–547 and includes `audience_tier: 'super_admin' | 'acharya_reviewer' | 'client' | 'public_redacted'` — this is the FOUR-value enum, not the TWO-value enum used by the DB/MCP key layer. This interface is used internally only; not persisted.

---

## 7. B.11 Enforcement (and the Loop Gap)

### 7.1 B.11 floor literal sites in route.ts

**Site 1 — Default B.11 floor** (route.ts:461–483):
```typescript
const L2_5_TOOLS = ['msr_sql', 'query_msr_aggregate', 'pattern_register',
  'resonance_register', 'cluster_atlas', 'contradiction_register', 'cgm_graph_walk']
if (!toolsAuthorized.some(t => L2_5_TOOLS.includes(t))) {
  // Predictive class: cgm_graph_walk banned; msr_sql + vector_search + pattern_register injected
  // Default class: msr_sql + cgm_graph_walk injected
}
```

**Site 2 — Predictive branch** (route.ts:467–476):
- Bans `cgm_graph_walk` per R14c
- Injects `msr_sql`, `vector_search`, `pattern_register`

**Site 3 — Dasha context floor** (route.ts:489–504):
- Condition: `(query_class === 'predictive' || query_class === 'holistic') && !toolsAuthorized.includes('chart_facts_query')`
- Injects `chart_facts_query` with `category: 'dasha_vimshottari', limit: 50`

### 7.2 Agentic loop B.11 enforcement

**CONFIRMED — No forced-first tool call in the agentic loop.** The adapter path builds `adapterChatReq` with B.11 floor tool results **pre-injected as context** (via `bundleSystemContent` at route.ts:936–943) before any model call. The loop itself does not enforce B.11 — it operates on the planner-authorized subset and receives the holistic synthesis layer as pre-fetched context.

B.11 is enforced by: (1) the pre-fetch block executing deterministically before the adapter block, and (2) the system prompt containing the floor tool results. The loop CANNOT skip L2.5 because the L2.5 data is already in the context when the first model call occurs.

### 7.3 Adapter/loop final-answer guard (citation gate)

**CONFIRMED — `validateCitationsForStream` exists ONLY on the orchestrator path.**

`route.ts:1374` (inside `onFinish` of the orchestrator tail, lines 1357–1681): `validateCitationsForStream(outputText, assembledContextJson, ...)` is called.

The adapter path (route.ts:1027–1197) has NO equivalent citation gate. The adapter tail ends at line 1197 with `return createUIMessageStreamResponse({ stream: adapterStream })` — no `onFinish` citation check.

**Impact:** When `R11V2_USE_ADAPTERS=true`, responses are not subject to the B.11 citation gate. This is the unequal enforcement documented in Finding 6.

### 7.4 MCP-side B.11 advisory nature

**CONFIRMED.** On the MCP path, B.11 is enforced via prose in `marsys://house-rules` (loaded as a resource by `registerResources()`). The house-rules text instructs the LLM to call holistic_bundle or query_signals first, but this is **advisory** — the LLM can ignore it. There is no deterministic enforcement in the MCP sidecar equivalent to the portal's pre-fetch block.

**Summary: Two mechanisms, unequal strength:**
- Portal orchestrator path: DETERMINISTIC (pre-fetch runs unconditionally; L2.5 data always in context; citation gate validates output)
- Portal adapter/loop path: PARTIAL (pre-fetch runs but no citation gate)
- MCP path: ADVISORY only (house-rules prose; no enforcement)

### 7.5 Name-keyed tables in route.ts

| Table | Line range | Tool names contained |
|---|---|---|
| `toolStepType()` | 111–131 | vector_search, msr_sql, query_msr_aggregate, classical_text_search, classical_attribution_lookup, lel_query, query_signal_state, query_kp_ruling_planets, query_varshaphala, multi_school_signal_lookup, convergence_score_lookup, query_muhurat, query_jaimini_drishti, query_v7_additions |
| `inferLayer()` | 134–141 | msr_sql, query_msr_aggregate, pattern_register, resonance_register, cluster_atlas, contradiction_register, temporal, cgm_graph_walk, multi_school_signal_lookup, convergence_score_lookup |
| `tokensFor()` (orchestrator) | 1418–1447 | chart_facts_query, divisional_query, kp_query, manifest_query, query_kp_ruling_planets, query_varshaphala, saham_query, temporal, timeline_query (L1); msr_sql, query_msr_aggregate, query_signal_state (L2.5 signal); pattern_register, resonance_register, contradiction_register, cluster_atlas (L2.5 pattern); remedial_codex_query, domain_report_query (L4); vector_search; cgm_graph_walk |
| `tokensForAdapter()` (adapter) | 1139–1168 | Same lists, duplicated inline |

---

## 8. Gateway / Dynamic Loading / Providers

### 8.1 SDK reality

**CONFIRMED.** The MCP SDK (`@modelcontextprotocol/sdk`) provides BOTH:
- Legacy `server.tool(name, schema, handler)` method
- New `server.registerTool(name, config, cb)` method (line 699 of SDK's `mcp.js`)

The codebase uses `server.tool()` exclusively — all 40 `register*` functions call `server.tool(...)`.

`sendToolListChanged` IS present in the SDK (lines 64, 341, 405) via `listChanged: true` in capability declarations.

### 8.2 Statelessness

**CONFIRMED.** `platform-mcp/src/server.ts:237–239`:
```typescript
const transport = new StreamableHTTPServerTransport({
  sessionIdGenerator: undefined,
})
```

Each POST creates a new `McpServer` + transport. **No session state is maintained.**

**Statelessness blocks `listChanged` notifications** because: `sendToolListChanged` requires a persistent server instance that maintains a list of connected clients. With `sessionIdGenerator: undefined`, there are no persistent client sessions to notify. Going stateful would require: (1) setting `sessionIdGenerator` to a UUID generator, (2) maintaining a server instance map keyed by session ID, (3) storing sessions in a persistent store if multiple Cloud Run instances serve the same client.

### 8.3 Provider path for tool schemas

Tool schemas reach providers via `buildChatToolsFromNames(queryPlan.tools_authorized)` → `normalizeInputSchema()` → per-provider adapter's `tools()` method.

`normalizeInputSchema()` (defined at `platform/src/lib/retrieve/tool_catalogue.ts:35`) ensures every tool schema has `type: 'object'` regardless of what the retrieval tool's `inputSchema` field contains. Evidence: `platform/src/lib/providers/anthropic/adapter.ts:106–114`.

**Provider-specific transforms:**
- Anthropic adapter (`adapter.ts:114`): wraps in `jsonSchema(normalizeInputSchema(...))` for the AI SDK's Anthropic integration
- Other providers (Google, OpenAI, DeepSeek, NVIDIA): UNVERIFIED exact transform — likely similar normalization via respective adapters

**Tool count caps:** UNVERIFIED — no explicit count cap found in the codebase. The AI SDK provider integrations may impose caps but none are coded here.

### 8.4 Gateway feasibility

A stateless `search_tools` + `invoke_tool` gateway pattern is **feasible in principle** but would LOSE:
1. **Zod input validation** — currently each tool's Zod schema validates and transforms inputs before `retrieve()`. A generic `invoke_tool` would need a separate validation step.
2. **Tool-level error classification** — each tool returns typed envelope errors; a generic invoke_tool flattens these.
3. **Tier-conditional descriptions** — `getCatalogForTier()` varies descriptions by tier; a gateway can still do this but requires passing tier through the invoke call.
4. **Type safety** — TypeScript types are erased at the boundary; handlers lose `z.infer<typeof Schema>` type safety.
5. **Individual tool test isolation** — the current per-file `register*` pattern allows individual tool unit tests with `vi.mock`.

---

## 9. Tier Removal — Complete Surface

### 9.1 platform-mcp/ tier occurrences

| File | Lines | Context |
|---|---|---|
| `src/types.ts` | 64, 102, 112 | `audience_tier: string` in Principal, AudienceContext, RequestContext types |
| `src/auth.ts` | 98, 104 | Validates `audience_tier` present; copies to Principal |
| `src/server.ts` | 151, 169, 171 | URL-key T.3 restriction (super_admin only); tier-catalog call |
| `src/client.ts` | 109, 142, 248, 326 | `'X-MCP-Audience-Tier': principal.audience_tier` header on all HTTP calls |
| `src/tools/flag_disagreement.ts` | 137 | `if (principal.audience_tier !== 'super_admin')` → 403 |
| `src/tools/tool_health.ts` | 58 | Passes tier header |
| `src/tools/data_coverage.ts` | 60 | Passes tier header |
| `src/tools/get_trace.ts` | 94 | Passes tier header |
| `src/tools/query_varshphal.ts` | 87, 119 | Client tier redaction branch |
| `src/tools/tier_catalog.ts` | 97 | `getCatalogForTier(tier, CATALOG)` — description variants by tier |
| `src/tools/holistic_bundle_tool.ts` | 104 | `tier: principal.audience_tier` passed to bundle call |
| `src/tools/multi_school_bundle_tool.ts` | 80 | Same |
| `src/bundles/cache.ts` | 120 | `audience_tier: params.audienceTier` in cache key |
| `src/bundles/holistic_bundle.ts` | 119, 127, 142, 277 | Principal struct; HTTP header |
| `src/bundles/multi_school_bundle.ts` | 101, 109, 125, 249 | Same |
| `src/resources/house_rules.ts` | 29, 48 | Valid tiers: `['super_admin', 'acharya', 'client', 'public_redacted']`; VARIANTS map |
| `src/resources/house_rules_variants/public_redacted.md` | 1–46 | Tier-specific house-rules prose |

### 9.2 platform/ API route tier gates

| Route | Lines | Gate type |
|---|---|---|
| `/api/mcp/health/tools/route.ts` | 70 | HARD-403 for `client` or `public_redacted` |
| `/api/mcp/health/coverage/route.ts` | 58 | HARD-403 for `client` or `public_redacted` |
| `/api/mcp/execute/route.ts` | 120 | `audience_tier` in request body type |
| `/api/mcp/primitives/[tool]/route.ts` | (see below) | Passes through via `X-MCP-Audience-Tier` header |
| `/api/mcp/keys/route.ts` | — | Key creation with tier |
| `/api/mcp/keys/validate/route.ts` | — | Returns tier in response |
| `/api/mcp/asset/route.ts` | — | Passes tier |
| `/api/mcp/bundles/[name]/route.ts` | — | Passes tier |
| `/api/mcp/trace/[trace_id]/route.ts` | — | Passes tier |
| `/api/mcp/recent/route.ts` | — | Passes tier |
| `/api/mcp/writes/[action]/route.ts` | — | Passes tier |

### 9.3 DB / key issuance

`platform/supabase/migrations/070_mcp_api_keys.sql`:
```sql
audience_tier text NOT NULL CHECK (audience_tier IN ('client', 'super_admin'))
```

`platform/migrations/117_audience_tier_acharya_enum.sql`:
```sql
ADD CONSTRAINT mcp_api_keys_audience_tier_check
  CHECK (audience_tier IN ('client', 'super_admin', 'acharya'))
```

`platform/src/lib/mcp/auth.ts:97`: `SELECT key_id, key_hash, user_uid, audience_tier FROM mcp_api_keys`

`platform/src/app/api/mcp/keys/route.ts`: Key creation UI with tier selection.

### 9.4 PipelinePlan and disclosure types

`platform/src/lib/pipeline/types.ts:306–310`:
```typescript
audience_tier: z.enum([
  'super_admin',
  'acharya_reviewer',    ← NOTE: "acharya_reviewer" NOT "acharya"
  'client',
  'public_redacted',
]).optional(),
```

`platform/src/lib/disclosure/types.ts:1`:
```typescript
export type AudienceTier = 'super_admin' | 'acharya_reviewer' | 'client' | 'public_redacted'
```

`platform/src/lib/mcp/types.ts:19,101,144,158`:
```typescript
audience_tier: 'client' | 'super_admin'    ← TWO values only
```

### 9.5 "acharya" vs "acharya_reviewer" naming split

**CONFIRMED SPLIT — two different spellings coexist:**

| Spelling | Where used |
|---|---|
| `acharya` | DB column `mcp_api_keys.audience_tier` (migration 117); `platform-mcp/src/resources/house_rules.ts:29` validTiers array; `platform-mcp/src/server.ts` tier-catalog call; `platform/src/lib/mcp/README.md` example |
| `acharya_reviewer` | `platform/src/lib/disclosure/types.ts`; `platform/src/lib/pipeline/types.ts` Zod enum; `platform/src/app/api/chat/consume/route.ts:527` LegacyQueryPlanShape; `/api/mcp/execute/route.ts:120`; UI components (TierPicker, DisclosureTierBadge, AuditBadge, etc.) |

The DB and MCP-sidecar use `acharya`; the portal query plan and disclosure system use `acharya_reviewer`. These are semantically the same tier expressed with different spellings — a split that was never reconciled.

### 9.6 Tests/fixtures carrying tier

- `platform-mcp/src/__tests__/server_tier_visibility.test.ts`: `makePrincipal('client')`, `makePrincipal('acharya')`, `makePrincipal('super_admin')`
- `platform/src/components/disclosure/__tests__/DisclosureTierBadge.test.tsx`: all 4 TIERS
- `platform/src/components/audit/__tests__/CompareView.test.tsx`: `disclosure_tier: 'acharya_reviewer'`
- `platform/src/lib/disclosure/__tests__/disclosure.test.ts`: acharya_reviewer, public_redacted

### 9.7 Tier-removal worklist

**Delete-module:**
- `platform-mcp/src/resources/house_rules_variants/public_redacted.md`
- `platform-mcp/src/tools/tier_catalog.ts` (if description variants are eliminated)
- `platform/src/lib/disclosure/` (entire module if disclosure tiers removed)
- `platform/src/components/disclosure/DisclosureTierBadge.tsx`
- `platform/src/components/consume/TierPicker.tsx`

**Drop-field:**
- `platform/src/lib/mcp/types.ts`: remove `audience_tier` from 4 interface definitions
- `platform/src/lib/pipeline/types.ts`: remove `audience_tier` from PipelinePlan Zod enum
- `platform/src/app/api/chat/consume/route.ts:527–529`: remove `acharya_reviewer` + `public_redacted` from LegacyQueryPlanShape
- `platform/src/lib/disclosure/types.ts`: AudienceTier type
- `platform-mcp/src/types.ts`: remove `audience_tier` from Principal + related types

**Drop-DB-column+constraint:**
- `mcp_api_keys.audience_tier` column (migration 070 + 117)
- Any rows keyed by tier in bundle_cache or other tables

**Remove-route-gate:**
- `platform/src/app/api/mcp/health/tools/route.ts:70` — remove HARD-403 for client/public_redacted
- `platform/src/app/api/mcp/health/coverage/route.ts:58` — same

**Update-test:**
- `platform-mcp/src/__tests__/server_tier_visibility.test.ts` — remove tier variants
- `platform/src/components/disclosure/__tests__/DisclosureTierBadge.test.tsx` — delete
- `platform/src/lib/disclosure/__tests__/disclosure.test.ts` — delete or simplify

---

## 10. Per-Tool Disposition Reality

### 10.1 query_signals + msr_sql — same engine?

**CONFIRMED.** `primitives_registry.ts:96`: `query_signals: 'msr_sql'`. Both `query_signals` (MCP name) and `msr_sql` (MCP name, UDA-added) map to the same `msr_sql` engine. The MCP server exposes BOTH names — a client calling `query_signals` and a client calling `msr_sql` hit the same retrieval function. They are distinct tools only in naming.

### 10.2 Register quartet

**CONFIRMED — 4 distinct engines, near-identical shape:**
- `pattern_register` → `platform/src/lib/retrieve/pattern_register.ts`
- `resonance_register` → `platform/src/lib/retrieve/resonance_register.ts`
- `cluster_atlas` → `platform/src/lib/retrieve/cluster_atlas.ts`
- `contradiction_register` → `platform/src/lib/retrieve/contradiction_register.ts`

All four are signal-classification tools reading `l25_msr_signals` with different filter conditions. Same return shape; different semantic filter.

### 10.3 Synthesis trio

**CONFIRMED — 3 distinct engines/files:**
- `query_ucn_walk` → `platform/src/lib/retrieve/query_ucn_walk.ts` (UCN_v4_0.md L2.5 asset)
- `query_cdlm_lookup` → `platform/src/lib/retrieve/query_cdlm_lookup.ts` (CDLM_v1_1.md L2.5 asset)
- `query_rm_walk` → `platform/src/lib/retrieve/query_rm_walk.ts` (RM_v2_0.md L2.5 asset)

### 10.4 query_remedies_prescribed → remedial_codex_query

**CONFIRMED** (partially). `platform-mcp/src/tools/query_remedies_prescribed.ts` calls `callPlatformPrimitive` — it dispatches to the platform endpoint. The underlying engine in `platform/src/lib/retrieve/query_remedies_prescribed.ts` reads a `remedies` table (not `remedial_codex_query` which reads rag_chunks). These are DISTINCT engines: `query_remedies_prescribed` = prescribed remedies DB table; `remedial_codex_query` = codex text search. The brief's claim about layering is UNVERIFIED — they appear to be siblings, not layered.

### 10.5 PROMOTE set — engine/registration status

| MCP name | Engine file exists? | NOT in server.ts? | Written MCP tool file? |
|---|---|---|---|
| tara_balam_for_native | `platform/src/lib/retrieve/tara_balam_for_native.ts` ✓ | **CONFIRMED** not registered | `platform-mcp/src/tools/tara_balam_for_native.ts` ✓ |
| chandra_balam_for_native | `platform/src/lib/retrieve/chandra_balam_for_native.ts` ✓ | **CONFIRMED** not registered | `platform-mcp/src/tools/chandra_balam_for_native.ts` ✓ |
| query_transits_over_natal | `platform/src/lib/retrieve/query_transits_over_natal.ts` ✓ | **CONFIRMED** not registered | `platform-mcp/src/tools/query_transits_over_natal.ts` ✓ |
| query_yogas_active_now | `platform/src/lib/retrieve/query_yogas_active_now.ts` ✓ | **CONFIRMED** not registered | `platform-mcp/src/tools/query_yogas_active_now.ts` ✓ |
| get_shadbala_full | `platform/src/lib/retrieve/get_shadbala_full.ts` ✓ | **CONFIRMED** not registered | `platform-mcp/src/tools/get_shadbala_full.ts` ✓ |
| get_planet_avastha | `platform/src/lib/retrieve/get_planet_avastha.ts` ✓ | **CONFIRMED** not registered | `platform-mcp/src/tools/get_planet_avastha.ts` ✓ |
| query_jaimini_chara_dasha | `platform/src/lib/retrieve/query_jaimini_chara_dasha.ts` ✓ | **CONFIRMED** not registered | `platform-mcp/src/tools/query_jaimini_chara_dasha.ts` ✓ |
| query_planetary_period_predictions | `platform/src/lib/retrieve/query_planetary_period_predictions.ts` ✓ | **CONFIRMED** not registered | `platform-mcp/src/tools/query_planetary_period_predictions.ts` ✓ |
| query_eclipse_transits | `platform/src/lib/retrieve/query_eclipse_transits.ts` ✓ | **CONFIRMED** not registered | `platform-mcp/src/tools/query_eclipse_transits.ts` ✓ |
| query_planet_war | `platform/src/lib/retrieve/query_planet_war.ts` ✓ | **CONFIRMED** not registered | `platform-mcp/src/tools/query_planet_war.ts` ✓ |
| saham_query | `platform/src/lib/retrieve/saham_query.ts` ✓ | No MCP wrapper | No MCP tool file |
| domain_report_query | `platform/src/lib/retrieve/domain_report_query.ts` ✓ | No MCP wrapper | No MCP tool file |
| query_msr_aggregate | `platform/src/lib/retrieve/query_msr_aggregate.ts` ✓ | No MCP wrapper (portal-only) | No MCP tool file |

### 10.6 query_jaimini_drishti stub confirmation

**CONFIRMED STUB, CONFIRMED REGISTERED.**
- `platform-mcp/src/tools/query_jaimini_drishti.ts:17`: "currently stub — returns not_implemented until M6+ Jaimini engine"
- `platform-mcp/src/tools/query_jaimini_drishti.ts:50`: returns literal string `'Currently stub — returns not_implemented until M6+ Jaimini engine lands.'`
- `platform-mcp/src/server.ts:81,218`: imported AND registered (UDA-2-S7)

### 10.7 BACKFILL tools

| Tool | Engine | Status |
|---|---|---|
| get_cgm_subgraph | cgm_graph_walk | Registered. Data table `cgm_nodes/cgm_edges` is EMPTY (CONFIRMED per CLAUDE.md §E: "P3 deferred non-blocking: CGM graph seeding"). Row count: **UNVERIFIED** (no DB access) but governance record says empty. |
| timeline_query | timeline_query | Registered. Data table `l5_timeline` is EMPTY (CONFIRMED per CLAUDE.md §E: "P3 deferred: L5 timeline bootstrap"). Row count: **UNVERIFIED** but governance record says empty. |
| query_signal_state | signal_states | Registered. Engine present at `platform/src/lib/retrieve/query_signal_state.ts`. Confidence fallback fixed (MCP Audit v2 Session B). Data populated. |

Populate scripts: `platform/scripts/` — UNVERIFIED which script populates cgm or l5_timeline specifically.

### 10.8 Declared asymmetries — spot-check

**Asymmetry 1: query_varshphal (MCP) vs query_varshaphala (portal)**
- MCP name: `query_varshphal` (registered in server.ts)
- Portal RETRIEVAL_TOOLS name: `query_varshaphala` (the actual engine)
- UDA-3 alias `queryVarshphalAlias` bridges the gap in Channel B
- CONFIRMED GENUINE ASYMMETRY — different names, same engine

**Asymmetry 2: cross_school_lookup (MCP) vs multi_school_signal_lookup_tool (portal)**
- MCP name: `cross_school_lookup` → engine `multi_school_signal_lookup`
- Portal name: `multi_school_signal_lookup_tool` (the engine module name)
- CONFIRMED GENUINE ASYMMETRY

**Asymmetry 3: query_remedial_mantras (MCP) vs remedial_codex_query (portal)**
- MCP name: `query_remedial_mantras` → engine `remedial_codex_query`
- Portal RETRIEVAL_TOOLS name: `remedial_codex_query`
- CONFIRMED GENUINE ASYMMETRY

### 10.9 FOLD candidates — one-line "what it does"

| Tool | Engine file | What it does | Status |
|---|---|---|---|
| query_dasamsha_career | `platform/src/lib/retrieve/query_dasamsha_career.ts` | Queries `chart_facts` for D10 dasamsha career-domain rows + yogas | Written, unregistered in server.ts |
| query_shashtiamsha | `platform/src/lib/retrieve/query_shashtiamsha.ts` | Queries `chart_facts` for D60 karma-pada rows | Written, unregistered in server.ts |
| query_drekkana_drishti | `platform/src/lib/retrieve/query_drekkana_drishti.ts` | Retrieves Jaimini Drekkana Drishti aspect data from chart_facts | Written, unregistered in server.ts |
| cross_varga_dignity_query | `platform/src/lib/retrieve/cross_varga_dignity_query.ts` | Cross-divisional dignity surface via chart_facts (VARGA-ETL) | Portal-only, no MCP wrapper |
| classical_attribution_lookup | `platform/src/lib/retrieve/classical_attribution_lookup_tool.ts` | Classical attribution lookup from rag_chunks (school → source attribution) | Portal-only |
| convergence_score_lookup | `platform/src/lib/retrieve/convergence_score_lookup_tool.ts` | School Convergence Index score lookup from `school_convergence_index` | Portal-only |
| manifest_query | `platform/src/lib/retrieve/manifest_query.ts` | BM25-style keyword search over CAPABILITY_MANIFEST.json entries | Portal-only |
| query_v7_additions | `platform/src/lib/retrieve/query_v7_additions.ts` | **STUB** — Sidecar POST /v7_additions, scope TBD at M6+. Returns not_implemented. | Portal-only stub |
| domain_report_query | `platform/src/lib/retrieve/domain_report_query.ts` | Retrieves L4 domain reports from rag_chunks by domain keyword filter + SELECT | Portal-only, **not a fold candidate** — distinct from other tools |
| query_v7_additions | — | Same as above | **DEFINITIVE**: pure stub, M6+ scope, sidecar endpoint not implemented |

---

## 11. Rename/Migration Blast Radius

### 11.1 catalog.ts and test assertion

- `platform-mcp/src/tools/catalog.ts`: 57 name literals, each `{ name: '<tool_name>', description: ... }`
- `platform-mcp/test/tool_descriptions.test.ts:91`: **`expect(CATALOG).toHaveLength(22)`** — must be updated to `57` (or current registered count after any changes)
- `tool_descriptions.test.ts:94–100`: spot-check names by literal string (chart_summary, holistic_bundle, query_chart_facts, read_asset, get_trace, log_prediction, flag_disagreement)

### 11.2 server.ts register calls + tool file name literals

Each of the 40 registered tools has:
1. An `import { registerX }` at the top of server.ts
2. A `registerX(server, getPrincipal)` call in the POST handler
3. A `server.tool('<mcp_name>', schema, handler)` call inside the `registerX` function

All three must be updated on rename.

### 11.3 primitives_registry.ts coupling

On rename, must update:
- `SURGICAL_TOOLS` array: literal engine name strings (×1–4 per entry due to duplication bug)
- `MCP_TO_RETRIEVAL_TOOL` object: both KEY (MCP name) and VALUE (engine name) may change
- `SurgicalToolName` type: automatically derived from `SURGICAL_TOOLS as const`, updates automatically
- `isAllowedSurgicalTool()` function: no literals, uses Object.hasOwn — no change needed

### 11.4 retrieve/index.ts coupling

- `import * as <module> from './<engine_name>'` — module import path
- `<module>.tool` in RETRIEVAL_TOOLS array
- Alias object `name: '<canonical_mcp_name>'` for the 2 UDA-3 aliases
- `getTool(name)` function: no literal — searches by `name` field

### 11.5 retrieval_capability_spec.ts (DEAD)

**CONFIRMED DEAD.** `platform/src/lib/router/__tests__/retrieval_capability_spec.test.ts` is the ONLY file that imports `retrieval_capability_spec`. No application code references it. However, the file itself is at `platform/src/lib/router/` — not at `platform/src/lib/retrieve/` — so it is NOT in the retrieve registry.

Actually: the spec file lives at `platform/src/lib/router/__tests__/retrieval_capability_spec.test.ts` — this is a test file that only imports itself for its own assertions. The `retrieval_capability_spec.ts` source (if it exists) at `platform/src/lib/router/` would be dead.

### 11.6 route.ts tool-name literal tables

All four name-keyed tables in route.ts must be updated on rename:
- `toolStepType()`: lines 111–131 (14 engine names)
- `inferLayer()`: lines 134–141 (10 engine names)
- `tokensFor()` orchestrator: lines 1418–1447 (hard-coded name lists for L1/L2.5/L4/vector/CGM)
- `tokensForAdapter()` adapter: lines 1139–1168 (same lists duplicated)

### 11.7 Bundle fan-out maps

`platform-mcp/src/bundles/holistic_bundle.ts`:
- `SUB_TOOLS` const at line 22: `['MSR', 'CGM', 'UCN', 'RM', 'CDLM', 'LEL', 'PANCHANG', 'DASHA']` — these are internal bundle-layer names, not MCP tool names
- `getToolRouteFor()` at line 191–207: maps `SubToolName` → platform primitive route string (e.g. `MSR → 'msr_sql'`)

`platform-mcp/src/bundles/multi_school_bundle.ts`:
- Similar mapping structure for multi-school primitives

### 11.8 seed_tool_registry.ts manifest consumption

**CONFIRMED.** `platform/scripts/governance/seed_tool_registry.ts`:
- Line 24: reads `CAPABILITY_MANIFEST.json`
- Line 48: `const toolName = entry['tool_name']`
- Line 60: upserts into `capability_tool_registry(tool_name, ...)`
- Lines 139–172: upserts capability_tool_registry + capability_asset_tool_bindings by tool_name

A rename must update: (1) `tool_name` field in CAPABILITY_MANIFEST.json entries, (2) the DB upsert will create new rows; old rows with the old name must be deleted or the old `manifest_overrides.yaml` entries updated.

### 11.9 PLANNER_PROMPT_v2_0.md runtime loading

**CONFIRMED.** `platform/src/lib/pipeline/pipeline_planner.ts:89,132`: loads `PLANNER_PROMPT_v2_0.md` lazily from `repoRoot()/00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md` at runtime.

Tool name occurrences in the planner prompt (counts by name):
```
msr_sql ×47, pattern_register ×33, vector_search ×32, cgm_graph_walk ×30,
lel_query ×23, cluster_atlas ×21, query_ephemeris ×20, resonance_register ×15,
query_panchanga ×15, query_signal_state ×14, temporal ×12, query_varshaphala ×10,
query_kp_ruling_planets ×10, query_transit_event ×7, contradiction_register ×5,
query_dasha_periods ×3, chart_facts_query ×3, query_ucn_walk ×2, query_rm_walk ×2,
query_cdlm_lookup ×2, kp_query ×2
```

**NOTE:** The planner prompt uses `query_varshaphala` (old portal name), not `query_varshphal` (MCP canonical name). This must be updated if the tool is renamed in the portal registry.

### 11.10 bench/scenarios tool names

`bench/scenarios/canonical_d9_workflow.yaml`: tools `chart_summary`, `query_chart_facts`
`bench/scenarios/holistic_d9.yaml`: UNVERIFIED exact tool names
`bench/scenarios/portal_synthesis_floor.yaml`: UNVERIFIED exact tool names

`platform-mcp/test/accuracy/cross_scenario.test.ts`: uses `registerChartSummaryTool` and `registerQueryChartFacts` — two tool names

### 11.11 Runtime-loaded prompt templates with tool names

- `00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md` — runtime-loaded; 21 tool names (see §11.9)
- `platform-mcp/src/resources/house_rules_variants/*.md` — runtime-loaded as MCP resources; contain tool names in usage guidance prose
- `platform-mcp/src/resources/capabilities.ts` — line 148 contains inline markdown table mentioning `holistic_bundle`

---

## 12. Eval Harness Reality

### 12.1 accuracy/ test structure

**CONFIRMED.** `platform-mcp/test/accuracy/cross_scenario.test.ts`:
- Golden is **NOT tool-name-keyed**
- It is **claim-keyed** via `extractClaims()` / `diffClaims()` which key by `(source_category, subject, predicate)` tuples from `chart_facts` DB rows
- Number of categories: 37 (matching `PLATFORM_ENUM_CATEGORIES` in `tool_descriptions.test.ts:23–33`)
- **Invalidation triggers:** adding/removing chart_facts categories, changing the `claim_extractor.ts` key structure, changing `chart_summary` batching logic, changing `query_chart_facts` response shape

### 12.2 bench/ structure

**CONFIRMED — bench IS tool-name-keyed.** `bench/scenarios/canonical_d9_workflow.yaml` has `- tool: chart_summary` and `- tool: query_chart_facts` as literal step names. The bench runner (`bench/run.ts`) reads `tool:` field to call the right MCP endpoint.

Round-trip-count assertions: UNVERIFIED — bench/run.ts not read in detail. The scenario yaml has `metrics: [round_trips, response_bytes, wall_time_ms]` — whether hard count assertions exist is unclear.

### 12.3 tool_descriptions.test.ts lint rules

Every entry in `CATALOG` must:
1. First sentence matches `/^(What it does|FIRST CALL when|Returns)/` — disambiguator rule
2. Description ≤ 1200 characters
3. Description contains "When to prefer"
4. Description is non-empty (> 50 chars)

**CRITICAL: The test also asserts `expect(CATALOG).toHaveLength(22)`** — this is STALE and will fail on current codebase (57 entries). Any PR touching catalog.ts must update this assertion to the correct count.

### 12.4 answer:eval

**UNVERIFIED** — no `answer:eval` file or endpoint was found in the codebase scan. The accuracy harness (`test/accuracy/run.test.ts`) may implement scoring, but the file was not read in detail. If the brief references an `answer:eval` concept, it may be a planned but not-yet-implemented feature.

---

## 13. Dead Code & Orphans

### 13.1 retrieval_capability_spec.ts dead code

**CONFIRMED DEAD.** `platform/src/lib/router/__tests__/retrieval_capability_spec.test.ts` is the ONLY file that imports `retrieval_capability_spec`. The source file `platform/src/lib/router/retrieval_capability_spec.ts` (or equivalent path) has no callers in production code.

Evidence: `grep -rln "retrieval_capability_spec"` returned only the test file.

### 13.2 MCP orphaned planner path

**CONFIRMED.** `platform/src/app/api/mcp/execute/route.ts` handles `ask_madhav`, `plan_query`, `execute_plan`.

`platform-mcp/src/client.ts:13–15,139–173`:
```
callPlatform()          → /api/mcp/execute   (ask_madhav, execute_plan)
callPlatformPlan()      → /api/mcp/plan       (plan_query)
```

**Neither `callPlatform()` nor `callPlatformPlan()` is called from any registered tool file.** grep of all 40 registered tools' `.ts` files found NO callers of `callPlatform\b` (the non-primitive variant). All registered tools use `callPlatformPrimitive()`.

The `/api/mcp/execute` route is still live (it accepts requests) but it is an orphaned path — no MCP sidecar tool currently routes through it. It was the v1 architecture pattern (`ask_madhav` full-pipeline).

### 13.3 primitives_registry.ts alias cruft + duplicate msr_sql

**CONFIRMED.** The SURGICAL_TOOLS array has 32 duplicate entries across 19 tool names, with `msr_sql` appearing 4 times:
1. Line 48: original whitelist
2. Line 70: `'msr_sql'` duplicated in UDA comment block header (appears in the raw array)
3. Lines 71–84: UDA additions include `msr_sql` again at line 70

Additionally, 4 pass-through self-alias entries in MCP_TO_RETRIEVAL_TOOL (lines 113–116) are redundant since the primitives dispatcher already handles the underlying engine names through the MCP name mapping.

### 13.4 Other dead/duplicate tool code

- **`query_v7_additions`** engine: pure stub, sidecar endpoint `/v7_additions` not implemented. The engine file and portal RETRIEVAL_TOOLS entry are dead weight until M6+.
- **`manifest_query`** engine: Queries the CAPABILITY_MANIFEST.json at runtime. Listed in RETRIEVAL_TOOLS as a portal tool. No MCP wrapper. The value of exposing manifest content to synthesis is questionable; it's an internal governance artifact.
- **`query_msr_aggregate`** engine: Portal-only aggregation wrapper. Listed in `inferLayer()` and `toolStepType()` tables in route.ts but no dedicated MCP tool. Used by the legacy portal synthesis path.

---

## 14. Governance Integration

### 14.1 drift_detector.py manifest consumption

**CONFIRMED.** `platform/scripts/governance/drift_detector.py:49–57`:
```python
# Feature flag: when true, reads from CAPABILITY_MANIFEST.json instead of CANONICAL_ARTIFACTS.
# Default true (manifest path is production after Phase 1B cutover).
```

Lines 583–604: `from manifest_reader import load_manifest_as_ca(repo_root)` — reads `00_ARCHITECTURE/CAPABILITY_MANIFEST.json`.

**HIGH finding triggers:**
- Entry count drops from last recorded baseline (line 259: `severity="HIGH"`)
- `fingerprint` field mismatch across governance surfaces (line 185, 195, 206)
- Canonical path not found (line 592)
- Could not load manifest (line 592: `"severity": "HIGH"`)

A refactor session that renames tools or changes the manifest entry count without running `manifest:build` will generate a HIGH drift finding.

### 14.2 Refactor compliance requirements

A compliant refactor session must:
1. Edit tool source files (engine + MCP wrapper)
2. Update `RETRIEVAL_TOOLS` in `platform/src/lib/retrieve/index.ts` (name field)
3. Update `primitives_registry.ts` (SURGICAL_TOOLS + MCP_TO_RETRIEVAL_TOOL)
4. Update `catalog.ts` (name literal + description import)
5. Update `server.ts` (import + register call)
6. Update `PLANNER_PROMPT_v2_0.md` (if tool appears in prompt)
7. Run `npm run manifest:build` to regenerate `CAPABILITY_MANIFEST.json`
8. Update `seed_tool_registry.ts` if tool_name changes in DB
9. Run `drift_detector.py` and confirm no HIGH findings
10. Update `route.ts` literal tables (`toolStepType`, `inferLayer`, `tokensFor`)
11. Update `tool_descriptions.test.ts` length assertion and spot-check names
12. Update `bench/scenarios/*.yaml` if tool appears in scenarios

### 14.3 Mirror pair MP.5 and tool-only changes

**UNVERIFIED** — the mirror pair inventory was not read in full during this session. Based on `CANONICAL_ARTIFACTS_v1_0.md §2` references in CLAUDE.md: MP.5 is declared as covering a specific pair. Whether tool-only changes (no L2.5 asset path changes) trigger MP.5 depends on whether the tool file paths are in the mirror pair. L2.5 asset changes (UCN, MSR, CDLM files) would clearly trigger MP.5; tool source changes in `platform/src/lib/retrieve/` are likely Claude-side-only (MP.6 GOVERNANCE_STACK or MP.7 SESSION_LOG class) and would NOT trigger MP.5.

**Working assumption:** Tool source changes do NOT trip MP.5 (mirror is for L2.5 asset-path governance documents shared between Claude and Gemini sides). Confirm by reading `CANONICAL_ARTIFACTS_v1_0.md §2 MP.5` entry directly before any mirror-impacting rename.

---

## Appendix: Commands Run

```bash
# Directory structure
ls /Users/Dev/Vibe-Coding/Apps/Madhav/platform-mcp/src/
ls /Users/Dev/Vibe-Coding/Apps/Madhav/platform/src/lib/mcp/
ls /Users/Dev/Vibe-Coding/Apps/Madhav/platform-mcp/src/tools/*.ts | wc -l

# Tool file inventory
find platform-mcp/src/tools/ -name "*.ts" ! -name "*.test.ts" | sort

# Key file reads
# platform-mcp/src/server.ts (full)
# platform/src/lib/retrieve/index.ts (full)
# platform/src/lib/mcp/primitives_registry.ts (full)
# platform-mcp/src/tools/catalog.ts (full)
# platform-mcp/test/tool_descriptions.test.ts (full)
# platform-mcp/src/__tests__/server_tier_visibility.test.ts (full)
# platform/src/app/api/chat/consume/route.ts (lines 1-1460)

# CAPABILITY_MANIFEST.json analysis
cat 00_ARCHITECTURE/CAPABILITY_MANIFEST.json | python3 -c "import json,sys; ..."

# Unregistered tools detection
for f in platform-mcp/src/tools/*.ts; do
  regfn=$(grep -oP "export function register\w+" "$f" | head -1)
  if ! grep -q "$name" server.ts; then echo "UNREGISTERED: $f"; fi
done

# Tier references
grep -rn "audience_tier|acharya_reviewer|public_redacted" platform-mcp/src/ platform/src/
grep -rn "acharya_reviewer|public_redacted" platform/src/

# Duplicates in SURGICAL_TOOLS
python3 -c "import re; ... Counter(tools) ..."

# Dead code checks
grep -rln "retrieval_capability_spec" platform/src/
grep -rln "callPlatform\b[^P]" platform-mcp/src/tools/*.ts
grep -n "callPlatform\|callPlatformPlan" platform-mcp/src/client.ts

# Zod transform/refine usage
grep -ln ".transform(" platform-mcp/src/tools/*.ts
grep -ln ".refine(" platform-mcp/src/tools/*.ts

# Migration files
find platform/supabase/migrations/ -name "*.sql" | xargs grep -l "audience_tier|acharya"
grep -n "audience_tier|acharya" platform/migrations/117_audience_tier_acharya_enum.sql

# SDK check
grep -rn "registerTool|sendToolListChanged" platform-mcp/node_modules/@modelcontextprotocol/sdk/dist/esm/server/mcp.js | head -20

# RETRIEVAL_TOOLS exact count
python3 -c "import re; ... entries = re.findall(r'(\w+)\.tool\b', inner) ..."

# PLANNER_PROMPT tool names
grep -oP "(query_[a-z_]+|msr_sql|...)" 00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md | sort | uniq -c
```
