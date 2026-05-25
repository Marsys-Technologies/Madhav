---
title: Interface Normalization Register
canonical_id: INTERFACE_NORMALIZATION_REGISTER
version: 1.0
status: CURRENT
authored: 2026-05-25
authored_by: UDA-3-S1
phase: Universal Parity Campaign — UDA-3
---

# Interface Normalization Register v1.0

Produced by UDA-3-S1. Lists every tool that exists in both portal (Channel A/B) and MCP (Channel C),
with the canonical name, current portal name, current MCP name, normalization status, and any
declared asymmetry notes.

**Canonical name convention**: where names differ, the MCP name is declared canonical (MCP was built
later with explicit naming discipline). Portal tools with mismatched names receive alias keys in
`RETRIEVAL_TOOLS` so `getTool(canonical_name)` resolves correctly for the agentic loop (Channel B).

---

## §1 — Tools with EXACT name match (no action required)

These 35 tools use identical names on both channels. They are listed here for completeness of the
register; no normalization action is needed.

| canonical_name | portal_name | mcp_name | status |
|---|---|---|---|
| `msr_sql` | `msr_sql` | `msr_sql` | ALIGNED |
| `pattern_register` | `pattern_register` | `pattern_register` | ALIGNED |
| `resonance_register` | `resonance_register` | `resonance_register` | ALIGNED |
| `cluster_atlas` | `cluster_atlas` | `cluster_atlas` | ALIGNED |
| `contradiction_register` | `contradiction_register` | `contradiction_register` | ALIGNED |
| `temporal` | `temporal` | `temporal` | ALIGNED |
| `kp_query` | `kp_query` | `kp_query` | ALIGNED |
| `timeline_query` | `timeline_query` | `timeline_query` | ALIGNED |
| `query_signal_state` | `query_signal_state` | `query_signal_state` | ALIGNED |
| `query_kp_ruling_planets` | `query_kp_ruling_planets` | `query_kp_ruling_planets` | ALIGNED |
| `query_jaimini_drishti` | `query_jaimini_drishti` | `query_jaimini_drishti` | ALIGNED |
| `query_ucn_walk` | `query_ucn_walk` | `query_ucn_walk` | ALIGNED |
| `query_cdlm_lookup` | `query_cdlm_lookup` | `query_cdlm_lookup` | ALIGNED |
| `query_rm_walk` | `query_rm_walk` | `query_rm_walk` | ALIGNED |
| `muhurta_finder` | `muhurta_finder` | `muhurta_finder` | ALIGNED |
| `tara_balam_for_native` | `tara_balam_for_native` | `tara_balam_for_native` | ALIGNED |
| `chandra_balam_for_native` | `chandra_balam_for_native` | `chandra_balam_for_native` | ALIGNED |
| `query_transits_over_natal` | `query_transits_over_natal` | `query_transits_over_natal` | ALIGNED |
| `query_yogas_active_now` | `query_yogas_active_now` | `query_yogas_active_now` | ALIGNED |
| `get_planet_avastha` | `get_planet_avastha` | `get_planet_avastha` | ALIGNED |
| `get_shadbala_full` | `get_shadbala_full` | `get_shadbala_full` | ALIGNED |
| `query_drekkana_drishti` | `query_drekkana_drishti` | `query_drekkana_drishti` | ALIGNED |
| `query_jaimini_chara_dasha` | `query_jaimini_chara_dasha` | `query_jaimini_chara_dasha` | ALIGNED |
| `query_planetary_period_predictions` | `query_planetary_period_predictions` | `query_planetary_period_predictions` | ALIGNED |
| `query_dasamsha_career` | `query_dasamsha_career` | `query_dasamsha_career` | ALIGNED |
| `query_shashtiamsha` | `query_shashtiamsha` | `query_shashtiamsha` | ALIGNED |
| `query_eclipse_transits` | `query_eclipse_transits` | `query_eclipse_transits` | ALIGNED |
| `query_planet_war` | `query_planet_war` | `query_planet_war` | ALIGNED |
| `query_remedies_prescribed` | `query_remedies_prescribed` | `query_remedies_prescribed` | ALIGNED |
| `query_ephemeris` | `query_ephemeris` | `query_ephemeris` | ALIGNED |
| `query_panchanga` | `query_panchanga` | `query_panchanga` | ALIGNED |
| `query_transit_event` | `query_transit_event` | `query_transit_event` | ALIGNED |
| `query_dasha_periods` | `query_dasha_periods` | `query_dasha_periods` | ALIGNED |
| `lel_query` | `lel_query` | `lel_query` | ALIGNED |
| `vector_search` | `vector_search` | `vector_search` | ALIGNED |

---

## §2 — Tools with NAME MISMATCHES (normalization required)

These tools have different names on the two channels. The MCP name is taken as canonical.
Portal tools receive alias keys in `RETRIEVAL_TOOLS` (additive — the old key is NOT removed,
so existing portal planner + tool-executor call sites continue to work unchanged).

| canonical_name | portal_name | mcp_name | status | asymmetry_note |
|---|---|---|---|---|
| `query_chart_facts` | `chart_facts_query` | `query_chart_facts` | ALIAS_ADDED — UDA-3-S1 | Canonical: MCP name. Portal alias `query_chart_facts` added to `RETRIEVAL_TOOLS` pointing to same handler. Old key `chart_facts_query` retained for backward compat. |
| `query_varshphal` | `query_varshaphala` | `query_varshphal` | ALIAS_ADDED — UDA-3-S1 | Canonical: MCP name (shorter; matches varshphal table name in DB). Portal alias `query_varshphal` added. Old key `query_varshaphala` retained for backward compat. |
| `read_classical_text` | `classical_text_search` | `read_classical_text` | ASYMMETRY_DECLARED | **Declared asymmetry**: Portal does semantic *search* (finds relevant classical passages by query string using vector similarity). MCP does exact *read* (fetches a specific text by source + chapter ID). These are complementary operations, not duplicates. Both names are correct for their respective interfaces. No alias needed; difference is intentional and documented here. |
| `cross_school_lookup` | `multi_school_signal_lookup` | `cross_school_lookup` | ASYMMETRY_DECLARED | Portal tool queries `school_convergence_index` for a specific MSR signal. MCP tool queries by school + topic key. Interface signatures differ; not aliasable without schema reconciliation (UDA-3-S2 scope). Names preserved. |
| `get_cgm_subgraph` | `cgm_graph_walk` | `get_cgm_subgraph` | ASYMMETRY_DECLARED | Portal does a *walk* (BFS/DFS from a node, depth-limited). MCP does a *subgraph fetch* (fetch node + immediate edges by node_id). Different traversal semantics; both valid for their use cases. Schema reconciliation deferred to UDA-3-S2. |
| `query_divisional_chart` | `divisional_query` | `query_divisional_chart` | ASYMMETRY_DECLARED | Portal thin wrapper calls sidecar `/divisional`. MCP tool queries `divisional_charts` DB table with richer filtering. Interface depth differs significantly. Schema reconciliation deferred to UDA-3-S2. |
| `query_remedial_mantras` | `remedial_codex_query` | `query_remedial_mantras` | ASYMMETRY_DECLARED | Portal queries `remedial_codex` structured table by domain/affliction. MCP queries by planet/house and returns mantra + ritual prescriptions. Partial overlap; different output schemas. Schema reconciliation deferred to UDA-3-S2. |
| `muhurta_finder` | `query_muhurat` | `muhurta_finder` | ASYMMETRY_DECLARED | Portal `query_muhurat` is a thin sidecar wrapper for muhurat lookups (thin interface). Portal also registers `muhurta_finder` as its own tool (both coexist in RETRIEVAL_TOOLS). MCP only has `muhurta_finder`. The `query_muhurat` portal tool predates `muhurta_finder` and is kept for backward compat with planner; planner should prefer `muhurta_finder`. |
| `convergence_score_lookup` | `convergence_score_lookup` | `(partial: cross_school_lookup)` | PORTAL_ONLY_PARTIAL | Portal tool queries by signal_id for numerical convergence score. MCP `cross_school_lookup` covers partial functionality but not a direct equivalent. Full MCP parity for this tool is a UDA-3-S2/UDA-4 item. |

---

## §3 — Portal-only tools (no MCP counterpart — channel:portal)

These tools appear in `RETRIEVAL_TOOLS` but have no MCP equivalent. Listed for completeness;
out of scope for UDA-3 normalization (UDA-2 addressed adding these to MCP).

| portal_name | notes |
|---|---|
| `query_msr_aggregate` | Cross-chart MSR rollups — no MCP equivalent |
| `saham_query` | Saham (Arabic parts) — no MCP equivalent |
| `cross_varga_dignity_query` | CSI cross-divisional dignity — no MCP equivalent |
| `domain_report_query` | Compiled domain reports — no MCP equivalent |
| `classical_attribution_lookup` | Classical attribution by planet/house/sign — no MCP equivalent |
| `query_v7_additions` | V7 supplementary factors — no MCP equivalent |
| `manifest_query` | CAPABILITY_MANIFEST meta-lookup — no MCP equivalent |
| `query_signals` | MSR signal lookup — MCP has `query_signals` (added UDA-1) |

---

## §4 — MCP-only tools (no portal counterpart — channel:mcp)

These tools are in `platform-mcp/src/server.ts` but not in `RETRIEVAL_TOOLS`.
They are intentionally MCP-only (write tools, meta tools, composition tools).

| mcp_name | notes |
|---|---|
| `chart_summary` | Tier 1 super-endpoint — composition recipe, not a raw retrieval tool |
| `holistic_bundle` | Tier 2 bundle — composition recipe |
| `multi_school_bundle` | Tier 2 bundle — composition recipe |
| `query_signals` | MSR signal structured lookup — MCP-only surgical primitive |
| `interpret_current_dasha` | Composition recipe — intentionally MCP-only |
| `read_asset` | Raw GCS asset read — governance/meta, intentionally MCP-only |
| `list_assets` | Asset listing — governance/meta, intentionally MCP-only |
| `list_canonical_artifact_versions` | Governance meta-tool, intentionally MCP-only |
| `get_trace` | Observability — intentionally MCP-only |
| `list_recent_queries` | Observability — intentionally MCP-only |
| `tool_health` | Perf/ops — intentionally MCP-only |
| `data_coverage` | Perf/ops — intentionally MCP-only |
| `log_prediction` | Write tool — intentionally MCP-only |
| `record_outcome` | Write tool — intentionally MCP-only |
| `flag_disagreement` | Write tool — intentionally MCP-only |

---

## §5 — Normalization actions taken (UDA-3-S1)

| action | detail |
|---|---|
| ALIAS_ADDED | `query_chart_facts` alias key added to `RETRIEVAL_TOOLS` in `platform/src/lib/retrieve/index.ts` pointing to `chartFactsQuery.tool` |
| ALIAS_ADDED | `query_varshphal` alias key added to `RETRIEVAL_TOOLS` in `platform/src/lib/retrieve/index.ts` pointing to `queryVarshaphala.tool` |
| DOCUMENTED | `read_classical_text` / `classical_text_search` declared asymmetry recorded in §2 |
| DOCUMENTED | `cross_school_lookup` / `multi_school_signal_lookup` declared asymmetry recorded in §2 |
| DOCUMENTED | `get_cgm_subgraph` / `cgm_graph_walk` declared asymmetry recorded in §2 |
| DOCUMENTED | `query_divisional_chart` / `divisional_query` declared asymmetry recorded in §2 |
| DOCUMENTED | `query_remedial_mantras` / `remedial_codex_query` declared asymmetry recorded in §2 |
| DEFERRED | Schema-level reconciliation for all declared asymmetries — UDA-3-S2 scope |

---

*INTERFACE_NORMALIZATION_REGISTER v1.0 — authored 2026-05-25 — UDA-3-S1*
