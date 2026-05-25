---
title: "PRE-S1 Diagnostic Report — Universal Parity Campaign Baseline"
campaign: universal-parity
session: PRE-S1
date: 2026-05-25
git_sha: c894b0c33d8d70d5d1d36564d130b63430124606
status: BASELINE_CAPTURED
---

# PRE-S1 Diagnostic Report — Universal Parity Campaign Baseline

> Captured 2026-05-25. This is the pre-campaign state. TEST-0-S2 (end-of-campaign) will compare against this baseline.

---

## 1. Channel A+B — Portal Tools (`platform/src/lib/retrieve/index.ts`)

**Tool count: 36**

Source: `RETRIEVAL_TOOLS` array in `platform/src/lib/retrieve/index.ts` (lines 89–126).

| # | Tool Name (TOOL_NAME constant) | Source File |
|---|---|---|
| 1 | msr_sql | msr_sql.ts |
| 2 | pattern_register | pattern_register.ts |
| 3 | resonance_register | resonance_register.ts |
| 4 | cluster_atlas | cluster_atlas.ts |
| 5 | contradiction_register | contradiction_register.ts |
| 6 | temporal | temporal.ts |
| 7 | query_msr_aggregate | query_msr_aggregate.ts |
| 8 | cgm_graph_walk | cgm_graph_walk.ts |
| 9 | manifest_query | manifest_query.ts |
| 10 | vector_search | vector_search.ts |
| 11 | kp_query | kp_query.ts |
| 12 | saham_query | saham_query.ts |
| 13 | divisional_query | divisional_query.ts |
| 14 | chart_facts_query | chart_facts_query.ts |
| 15 | cross_varga_dignity_query | cross_varga_dignity_query.ts |
| 16 | domain_report_query | domain_report_query.ts |
| 17 | remedial_codex_query | remedial_codex_query.ts |
| 18 | timeline_query | timeline_query.ts |
| 19 | query_signal_state | query_signal_state.ts |
| 20 | query_kp_ruling_planets | query_kp_ruling_planets.ts |
| 21 | query_varshaphala | query_varshaphala.ts |
| 22 | lel_query | lel_query.ts |
| 23 | classical_text_search | classical_text_search_tool.ts |
| 24 | classical_attribution_lookup | classical_attribution_lookup_tool.ts |
| 25 | multi_school_signal_lookup | multi_school_signal_lookup_tool.ts |
| 26 | convergence_score_lookup | convergence_score_lookup_tool.ts |
| 27 | query_ephemeris | query_ephemeris.ts |
| 28 | query_panchanga | query_panchanga.ts |
| 29 | query_transit_event | query_transit_event.ts |
| 30 | query_dasha_periods | query_dasha_periods.ts |
| 31 | query_muhurat | query_muhurat.ts |
| 32 | query_jaimini_drishti | query_jaimini_drishti.ts |
| 33 | query_v7_additions | query_v7_additions.ts |
| 34 | query_ucn_walk | query_ucn_walk.ts |
| 35 | query_cdlm_lookup | query_cdlm_lookup.ts |
| 36 | query_rm_walk | query_rm_walk.ts |

---

## 2. Channel C — MCP Registered Tools (`platform-mcp/src/server.ts`)

**Registered tool count: 43** (44 imports, minus 1 for `registerResources` which is not a tool)

Source: `import { register* }` lines in `platform-mcp/src/server.ts`.

| Tier | Tool Name | Registered via |
|---|---|---|
| 1 | chart_summary | registerChartSummaryTool |
| 2 | holistic_bundle | registerHolisticBundle |
| 2 | multi_school_bundle | registerMultiSchoolBundle |
| 3 | query_chart_facts | registerQueryChartFacts |
| 3 | query_signals | registerQuerySignals |
| 3 | query_dasha_periods | registerQueryDashaPeriods |
| 3 | query_panchanga | registerQueryPanchanga |
| 3 | query_ephemeris | registerQueryEphemeris |
| 3 | query_transit_event | registerQueryTransitEvent |
| 3 | lel_query | registerLelQuery |
| 3 | vector_search | registerVectorSearch |
| 3 | get_cgm_subgraph | registerGetCgmSubgraph |
| 3 | cross_school_lookup | registerCrossSchoolLookup |
| 3 | query_varshphal | registerQueryVarshphal |
| 3 | query_divisional_chart | registerQueryDivisionalChart |
| 3 | query_remedial_mantras | registerQueryRemedialMantras |
| 3 | muhurta_finder | registerMuhurtaFinder |
| 3 | tara_balam_for_native | registerTaraBalamForNative |
| 3 | chandra_balam_for_native | registerChandraBalamForNative |
| 3 | query_transits_over_natal | registerQueryTransitsOverNatal |
| 3 | query_yogas_active_now | registerQueryYogasActiveNow |
| 3 | get_planet_avastha | registerGetPlanetAvastha |
| 3 | get_shadbala_full | registerGetShadbalaFull |
| 3 | interpret_current_dasha | registerInterpretCurrentDasha |
| 3 | list_canonical_artifact_versions | registerListCanonicalArtifactVersions |
| 3 | query_drekkana_drishti | registerQueryDrekkanaDisthi |
| 3 | query_jaimini_chara_dasha | registerQueryJaiminiCharaDasha |
| 3 | query_planetary_period_predictions | registerQueryPlanetaryPeriodPredictions |
| 3 | query_dasamsha_career | registerQueryDasamshhaCareer |
| 3 | query_shashtiamsha | registerQueryShashtiamsha |
| 3 | query_eclipse_transits | registerQueryEclipseTransits |
| 3 | query_planet_war | registerQueryPlanetWar |
| 3 | query_remedies_prescribed | registerQueryRemediesPrescribed |
| 4 | read_asset | registerReadAsset |
| 4 | read_classical_text | registerReadClassicalText |
| 4 | list_assets | registerListAssets |
| 5 | get_trace | registerGetTrace |
| 5 | list_recent_queries | registerListRecentQueries |
| 5 | tool_health | registerToolHealth |
| 5 | data_coverage | registerDataCoverage |
| 6 | log_prediction | registerLogPrediction |
| 6 | record_outcome | registerRecordOutcome |
| 6 | flag_disagreement | registerFlagDisagreement |

---

## 3. MCP Catalog (`platform-mcp/src/tools/catalog.ts`)

**Catalog entry count: 22**

Source: `{ name: '...' }` entries in `TOOL_CATALOG` array in `catalog.ts`.

Catalog entries: chart_summary, holistic_bundle, multi_school_bundle, query_chart_facts, query_signals, query_dasha_periods, query_panchanga, query_ephemeris, query_transit_event, lel_query, vector_search, get_cgm_subgraph, cross_school_lookup, read_asset, read_classical_text, get_trace, list_recent_queries, tool_health, data_coverage, log_prediction, record_outcome, flag_disagreement

**MCP catalog gap: 21 registered tools are NOT in catalog.ts**

These 21 tools are registered in server.ts but absent from catalog.ts: query_varshphal, query_divisional_chart, query_remedial_mantras, muhurta_finder, tara_balam_for_native, chandra_balam_for_native, query_transits_over_natal, query_yogas_active_now, get_planet_avastha, get_shadbala_full, interpret_current_dasha, list_canonical_artifact_versions, query_drekkana_drishti, query_jaimini_chara_dasha, query_planetary_period_predictions, query_dasamsha_career, query_shashtiamsha, query_eclipse_transits, query_planet_war, query_remedies_prescribed, list_assets.

These were added to server.ts (post-MCPT rounds) but catalog.ts was not updated. Campaign task UDA-Q or SYNC should resolve this.

---

## 4. Manifest (`00_ARCHITECTURE/CAPABILITY_MANIFEST.json`)

**Manifest tool-related entries:**
- 35 entries with `canonical_id` containing `TOOL`
- 39 entries with a `tool_name` field (includes assets such as FORENSIC, MSR etc. that declare their serving portal tool)
- Source: `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` (189 total entries, none typed `type: "tool"` — the manifest uses canonical_id patterns for tool identification)

---

## 5. Gap Analysis

### 5a. Shared Tools (present in both portal and MCP — 13 tools)

Name normalization applied: portal names mapped to MCP canonical names for comparison.
(e.g. `chart_facts_query` → `query_chart_facts`, `cgm_graph_walk` → `get_cgm_subgraph`, etc.)

| Portal Name | MCP Name |
|---|---|
| chart_facts_query | query_chart_facts |
| query_signal_state | query_signals |
| query_varshaphala | query_varshphal |
| divisional_query | query_divisional_chart |
| remedial_codex_query | query_remedial_mantras |
| query_muhurat | muhurta_finder |
| cgm_graph_walk | get_cgm_subgraph |
| lel_query | lel_query |
| vector_search | vector_search |
| query_ephemeris | query_ephemeris |
| query_panchanga | query_panchanga |
| query_transit_event | query_transit_event |
| query_dasha_periods | query_dasha_periods |

### 5b. Portal-Only Tools (in portal, not in MCP — 23 tools)

These 23 portal tools have no MCP equivalent and are primary campaign targets for porting to MCP.

| Portal Tool | Notes |
|---|---|
| msr_sql | Core MSR signal retrieval; partially proxied by query_signals in MCP |
| pattern_register | MSR pattern layer |
| resonance_register | UCN resonance layer |
| cluster_atlas | L2.5 cluster groupings |
| contradiction_register | Contradiction tracking |
| temporal | Temporal engine |
| query_msr_aggregate | MSR aggregate query |
| manifest_query | Manifest introspection |
| kp_query | KP system queries |
| saham_query | Arabic Parts (Sahams) |
| cross_varga_dignity_query | Cross-varga dignity analysis |
| domain_report_query | Domain-specific report generation |
| timeline_query | Timeline event query |
| query_kp_ruling_planets | KP ruling planets |
| classical_text_search | Classical text FTS (broader than read_classical_text) |
| classical_attribution_lookup | Classical attribution resolution |
| multi_school_signal_lookup | Multi-school signal lookup |
| convergence_score_lookup | School convergence scores |
| query_jaimini_drishti | Jaimini Drishti computation |
| query_v7_additions | V7 additions (7th-harmonic related) |
| query_ucn_walk | UCN graph traversal |
| query_cdlm_lookup | CDLM lookups |
| query_rm_walk | Remedial Matrix walk |

### 5c. MCP-Only Tools (in MCP, not in portal — 30 tools)

These 30 MCP tools have no portal equivalent. Most are surgical primitives added in MCPT rounds. 14 are potential campaign targets for portal addition; the rest (observability, write, raw-asset tiers) are MCP-specific by design.

**Campaign-relevant MCP-only (candidate for portal addition, 14):**
chart_summary, holistic_bundle, multi_school_bundle, tara_balam_for_native, chandra_balam_for_native, query_transits_over_natal, query_yogas_active_now, get_planet_avastha, get_shadbala_full, interpret_current_dasha, query_drekkana_drishti, query_jaimini_chara_dasha, query_planetary_period_predictions, query_dasamsha_career, query_shashtiamsha, query_eclipse_transits, query_planet_war, query_remedies_prescribed

**MCP infrastructure/observability (not expected in portal):**
cross_school_lookup, list_canonical_artifact_versions, read_asset, read_classical_text, list_assets, get_trace, list_recent_queries, log_prediction, record_outcome, flag_disagreement, tool_health, data_coverage

---

## 6. Quality Delta (Per-Tool Notes for Shared Tools)

### MCP-Ahead (4 gaps — portal lags behind MCP)

| Tool | Gap |
|---|---|
| query_dasha_periods | Portal missing pratyantar (PD) and sookshma (SD) sub-period nesting; MCP supports full 5-level dasha tree |
| query_ephemeris | Portal missing `date_range` struct input, `sample_step` parameter, `return_changes_only` flag, and 1825-day guard; MCP has stricter input validation and larger range support |
| query_chart_facts | Portal missing `include_empty_counts` flag and `populated_count` metadata annotation in response; MCP response is more introspectable |
| query_signals | Portal (`query_signal_state`) missing `dasha_lord`, `valence`, `temporal_activation` filter axes; MCP (`query_signals`) exposes full MSR filter surface |

### Portal-Ahead (3 gaps — MCP lags behind portal)

| Tool | Gap |
|---|---|
| lel_query | MCP omits `chart_state` column (planetary positions at event time); uses `float` for `significance` instead of enum; portal has richer event metadata and stricter typing |
| query_varshaphala | MCP (`query_varshphal`) single Varsha year only; portal (`query_varshaphala`) supports `year_start`/`year_end` date range for multi-year varshaphala queries |
| msr_sql | MCP has no direct MSR SQL surface; `query_signals` is a partial proxy. Portal `msr_sql` includes LL.1 domain-specific confidence floors (Atmakaraka ≥ 0.75, Yoga ≥ 0.70, etc.) baked in, and calibration-layer LL.2 integration |

### At Parity (0 tools)

No shared tools are confirmed at full implementation parity at campaign start.

---

## 7. Known HAPs (High-Availability Primitives) — 6 Ahead

Per campaign planning, 6 HAPs are identified as first-class campaign targets:

| HAP | Description | Current State |
|---|---|---|
| HAP-1: query_dasha_periods | Full 5-level dasha nesting in portal | Portal has MD/AD only; MCP has MD/AD/PD/SD |
| HAP-2: query_signals | Full filter surface in portal | Portal missing 3 filter axes vs MCP |
| HAP-3: tara_balam_for_native | Port to portal | MCP-only, no portal equivalent |
| HAP-4: chandra_balam_for_native | Port to portal | MCP-only, no portal equivalent |
| HAP-5: query_transits_over_natal | Port to portal | MCP-only, no portal equivalent |
| HAP-6: query_yogas_active_now | Port to portal | MCP-only, no portal equivalent |

---

## 8. Summary Counts

| Metric | Count |
|---|---|
| Portal tools (RETRIEVAL_TOOLS) | 36 |
| MCP registered tools (server.ts) | 43 |
| MCP catalog entries (catalog.ts) | 22 |
| MCP catalog gap (registered but not cataloged) | 21 |
| Manifest tool-related entries (TOOL canonical_ids) | 35 |
| Shared tools (name-normalized intersection) | 13 |
| Portal-only tools | 23 |
| MCP-only tools | 30 |
| Quality gaps: MCP-ahead | 4 |
| Quality gaps: portal-ahead | 3 |
| Total quality gaps | 7 |

---

## 9. Target State (Campaign End)

| Metric | Target |
|---|---|
| Portal tools | 36 + 20 new Class B engines ported from MCP |
| MCP registered tools | 43 + 23 portal-only tools added |
| MCP catalog gap | 0 (all registered tools in catalog) |
| Quality gaps | 0 |
| At-parity shared tools | 13 → full intersection at campaign end |

---

*Generated by PRE-S1 diagnostic session. Source files audited: `platform/src/lib/retrieve/index.ts`, `platform-mcp/src/server.ts`, `platform-mcp/src/tools/catalog.ts`, `00_ARCHITECTURE/CAPABILITY_MANIFEST.json`. All counts verified against file content (grep/node inspection, not assumptions). See `eval-results/parity_baseline_pre_campaign.json` for machine-readable companion.*
