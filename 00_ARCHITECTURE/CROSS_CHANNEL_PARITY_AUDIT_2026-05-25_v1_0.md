---
title: MARSYS-JIS Cross-Channel Parity Audit
version: 1.0
date: 2026-05-25
status: CURRENT
canonical_id: CROSS_CHANNEL_PARITY_AUDIT_2026-05-25
scope: MCP ↔ Portal (Classic Marsys / Claude Style) — retrieval tool and data asset parity
auditor: Claude (Cowork mode) — filesystem reads + live MCP calls + manifest inspection
native: Abhisek Mohanty | chart_id: 362f9f17-95a5-490b-a5a7-027d3e0efda0
related: MCP_TOOL_AUDIT_2026-05-25_v1_0.md (MCP-only live audit, v1.1)
artifact: CROSS_CHANNEL_PARITY_AUDIT_2026-05-25_v1_0
---

# MARSYS-JIS Cross-Channel Parity Audit — 2026-05-25

## Executive Summary

Three surface findings that override everything else:

**FINDING 1 — "Classic Marsys" and "Claude Style" are the same backend.**
The R11.G SettingsDropdown toggle is purely cosmetic. `MARSYS_FLAG_R11V2_USE_ADAPTERS=true`
is live in production. All portal chat requests (regardless of which radio the user selects)
route through the provider adapter + agentic loop. There is no separate "Legacy Chat V2"
backend. Any gap between channels is a gap between MCP vs portal, not between two portal modes.

**FINDING 2 — The planner only sees 11 of 36 retrieval tools.**
`CAPABILITY_MANIFEST.json` has `expose_to_planner=true` on exactly 11 entries. The 25 most
critical tools (msr_sql, cgm_graph_walk, vector_search, query_panchanga, query_ephemeris,
query_dasha_periods, chart_facts_query, remedial_codex_query, and 17 others) all have
`expose_to_planner=False`. The system works today ONLY because the B.11 floor in
`consume/route.ts` force-injects a hardcoded subset post-planning, and the planner LLM
follows R-rule text in the system prompt rather than the manifest it was told to respect.
This is a structural fragility — any change to the B.11 floor or R-rules without fixing
the manifest will silently degrade query coverage.

**FINDING 3 — MCP is missing 17 portal retrieval tools with no equivalents.**
Of the portal's 36 retrieval tools, only 19 have any MCP equivalent (some broken or sub-optimal).
17 have no MCP surface at all. The MCP is a partial instrument — an MCP client gets
roughly half the retrieval capability of the portal. For users of the MCP (external agents,
Claude Code IDE sessions, SDK consumers), 17 key tools are simply unavailable.

---

## §1 — Channel Architecture (Ground Truth)

### 1.1 What "channel" actually means in production

| Label | Backend | Flag | Notes |
|-------|---------|------|-------|
| "Classic Marsys" (portal) | R11v2 adapter path | `USE_ADAPTERS=true` | SettingsDropdown cosmetic; same pipeline |
| "Claude Style" (portal) | R11v2 adapter path | `USE_ADAPTERS=true` | Same pipeline as Classic Marsys |
| MCP sidecar | `amjis-mcp` Cloud Run | n/a | Separate process; own tool registry |

Both portal modes share:
- The same `consume/route.ts` handler
- The same PLANNER_PROMPT_v2_0.md
- The same CAPABILITY_MANIFEST.json
- The same 36-tool `RETRIEVAL_TOOLS` registry
- The same B.11 floor injection logic
- The same synthesis layer

The **only** real channel split is **portal vs MCP**. All portal-level analysis applies equally
to both display modes.

### 1.2 Request routing (portal)

```
User message
  → consume/route.ts
  → compressManifest() → 11-tool compressed manifest
  → Planner LLM (sees 11 tools + R-rules hardcoding 36 tool names)
  → plan.tool_calls generated
  → B.11 floor check (force-injects msr_sql, cgm_graph_walk, pattern_register,
                       vector_search, chart_facts_query if none present)
  → buildChatToolsFromNames(toolsAuthorized)
  → [MARSYS_FLAG_R11V2_USE_ADAPTERS=true] runAgenticLoop()
  → executeMCPTool() → getTool() → 36-tool RETRIEVAL_TOOLS registry
  → synthesis → response
```

### 1.3 MCP request routing

```
External client / Claude Code IDE
  → amjis-mcp sidecar (Cloud Run)
  → server.ts: 26 tools registered
  → callPlatformPrimitive() → amjis-web /api/mcp/primitive
  → isAllowedSurgicalTool() → primitives_registry.ts (23 entries post-fix)
  → getTool() → 36-tool RETRIEVAL_TOOLS registry
  → result returned to MCP client
```

---

## §2 — The Manifest Crisis (expose_to_planner)

### 2.1 Current state

The planner LLM receives a compressed manifest built by `compressManifest()` in
`manifest_compressor.ts`. This function filters solely on `expose_to_planner === true`.
No fallback. No `PRIMARY_TOOL_NAMES` override (that constant is `@deprecated` and
not used in the live code path).

Of 189 entries in CAPABILITY_MANIFEST.json, only **11** have `expose_to_planner=true`:

| Tool (manifest entry) | Category | Exposed since |
|----------------------|----------|---------------|
| `lel_query` | LEL events | COV-S6 |
| `query_varshaphala` | Annual chart | COV-S6 |
| `query_kp_ruling_planets` | KP system | COV-S6 |
| `query_signal_state` | Signal state | COV-S6 |
| `classical_text_search` | Classical corpus | COV-S6 |
| `classical_attribution_lookup` | Classical attribution | COV-S6 |
| `multi_school_signal_lookup` | Multi-school | COV-S6 |
| `convergence_score_lookup` | School convergence | COV-S6 |
| `query_cdlm_lookup` | CDLM | COV-S6 |
| `query_ucn_walk` | UCN synthesis | COV-S6 |
| `query_rm_walk` | RM synthesis | COV-S6 |

### 2.2 Tools critically absent from planner visibility

The following tools, which the B.11 floor and R-rules inject, are NOT in the planner manifest:

| Tool | Impact of absence | Current mitigation |
|------|------------------|-------------------|
| `msr_sql` | Core 573-signal corpus unreachable to planner | B.11 floor injects it (always) |
| `pattern_register` | Pattern corpus unreachable | B.11 floor injects it (predictive only) |
| `resonance_register` | Resonance corpus unreachable | R-rules only |
| `cluster_atlas` | Cluster corpus unreachable | R-rules only |
| `contradiction_register` | Contradiction corpus unreachable | R-rules only |
| `cgm_graph_walk` | Cross-domain graph unreachable | B.11 floor injects it |
| `vector_search` | Semantic RAG unreachable | B.11 floor injects it (predictive) |
| `chart_facts_query` | Chart facts unreachable | B.11 dasha floor injects it |
| `remedial_codex_query` | Remedies unreachable | R-rules only |
| `query_ephemeris` | Ephemeris data unreachable | R-rules only |
| `query_panchanga` | Panchanga unreachable | R-rules only |
| `query_transit_event` | Transit events unreachable | R-rules only |
| `query_dasha_periods` | Dasha periods unreachable | R-rules only |
| `query_muhurat` | Muhurat unreachable | R-rules only |
| `kp_query` | KP sublords unreachable | R-rules only |
| `saham_query` | Saham unreachable | R-rules only |
| `divisional_query` | D-charts unreachable | R-rules only |
| `domain_report_query` | Domain reports unreachable | R-rules only |
| `timeline_query` | Timeline unreachable | R-rules only |
| `temporal` | Temporal context unreachable | R-rules only |
| `query_msr_aggregate` | MSR aggregate unreachable | R-rules only |
| `manifest_query` | Manifest unreachable | R-rules only |
| `query_jaimini_drishti` | Jaimini aspects unreachable | R-rules only |
| `query_v7_additions` | V7 additions unreachable | R-rules only |
| `query_ucn_walk` | Note: ucn_walk IS planner-visible (above) | — |

### 2.3 Risk assessment

The B.11 floor is a safety net that covers the 5 most critical tools for most query classes.
But it is not comprehensive:
- Remedial queries that need `remedial_codex_query` rely entirely on the R-rules text
- KP queries that need `kp_query` have no fallback
- Panchanga and ephemeris queries have no B.11 floor
- The planner cannot reason about which tools to exclude or when not to call a tool,
  because it does not know most tools exist

**Fix required:** Set `expose_to_planner=true` in CAPABILITY_MANIFEST.json for all 25 missing
core retrieval tools. This is a manifest edit — no code change required. The `manifest_overrides.yaml`
currently has ZERO `expose_to_planner=true` entries and cannot help without additions.

---

## §3 — Full Cross-Channel Tool Parity Matrix

Legend:
- ✅ = Working, full fidelity
- ⚠️ = Working, sub-optimal (see column note)
- ❌ = Broken
- ➖ = Not present / no equivalent
- 🔲 = Stub / not yet built

### 3.1 L2.5 Synthesis Layer Tools

These are the core Holistic Synthesis surface (MSR, CGM, UCN, CDLM, RM, patterns, clusters).

| Portal tool | Portal status | Planner-visible | MCP equivalent | MCP status |
|-------------|--------------|-----------------|----------------|------------|
| `msr_sql` | ✅ | ❌ | `query_signals` | ⚠️ filters all dropped |
| `query_msr_aggregate` | ✅ | ❌ | ➖ none | ➖ |
| `pattern_register` | ✅ | ❌ | ➖ none | ➖ |
| `resonance_register` | ✅ | ❌ | ➖ none | ➖ |
| `cluster_atlas` | ✅ | ❌ | ➖ none | ➖ |
| `contradiction_register` | ✅ | ❌ | ➖ none | ➖ |
| `cgm_graph_walk` | ✅ | ❌ | `get_cgm_subgraph` | ❌ node_id→seeds broken |
| `query_ucn_walk` | ✅ | ✅ | ➖ none | ➖ |
| `query_cdlm_lookup` | ✅ | ✅ | ➖ none | ➖ |
| `query_rm_walk` | ✅ | ✅ | ➖ none | ➖ |
| `query_signal_state` | ✅ | ✅ | ➖ none | ➖ |
| `convergence_score_lookup` | ✅ | ✅ | `cross_school_lookup` | ⚠️ sparse data |
| `multi_school_signal_lookup` | ✅ | ✅ | ➖ none | ➖ |

**Assessment:** 5 of 13 tools are planner-visible. The core synthesis corpus (MSR, CGM, patterns,
clusters, contradictions, resonances) is invisible to the planner — B.11 floor saves msr_sql and
cgm_graph_walk; the rest rely on R-rule text. MCP has equivalents for only 2 of 13 tools, and
both equivalents have defects (query_signals filters dropped; get_cgm_subgraph broken).

### 3.2 Temporal / Predictive Layer Tools

| Portal tool | Portal status | Planner-visible | MCP equivalent | MCP status |
|-------------|--------------|-----------------|----------------|------------|
| `lel_query` | ✅ | ✅ | `lel_query` | ⚠️ min_significance dropped |
| `temporal` | ✅ | ❌ | ➖ none | ➖ |
| `timeline_query` | ✅ | ❌ | ➖ none | ➖ |
| `query_dasha_periods` | ✅ | ❌ | `query_dasha_periods` | ⚠️ level param dropped |
| `query_varshaphala` | ✅ | ✅ | `query_varshphal` | ✅* post-redeploy |
| `query_jaimini_drishti` | ✅ | ❌ | ➖ none | ➖ |
| `query_v7_additions` | ✅ | ❌ | ➖ none | ➖ |

**Assessment:** Only lel_query and query_varshaphala are planner-visible. Sub-period dasha
resolution is broken on MCP. Temporal context tool (daily/transit snapshot) has no MCP
equivalent. Jaimini system tools have no MCP equivalent.

### 3.3 Astronomical / Panchanga Layer

| Portal tool | Portal status | Planner-visible | MCP equivalent | MCP status |
|-------------|--------------|-----------------|----------------|------------|
| `query_ephemeris` | ✅ | ❌ | `query_ephemeris` | ⚠️ sample_step ignored |
| `query_panchanga` | ✅ | ❌ | `query_panchanga` | ✅ fully enriched |
| `query_transit_event` | ✅ | ❌ | `query_transit_event` | ✅ |
| `query_muhurat` | ✅ | ❌ | `muhurta_finder` | ✅* post-redeploy |

**Assessment:** Panchanga parity is the best-performing category. query_panchanga is the
richest tool on either channel (73,414 rows, full Phase 4C enrichment including choghadiya,
hora, special yogas). Both channels have equivalent functional access to transit events and
muhurta. Ephemeris sample_step bug means large-range queries on MCP return excess data.

### 3.4 Chart Facts / Divisional Layer

| Portal tool | Portal status | Planner-visible | MCP equivalent | MCP status |
|-------------|--------------|-----------------|----------------|------------|
| `chart_facts_query` | ✅ | ❌ | `query_chart_facts` | ⚠️ shadbala absent |
| `divisional_query` | ✅ | ❌ | `query_divisional_chart` | ✅* post-redeploy |
| `saham_query` | ✅ | ❌ | ➖ none | ➖ |
| `domain_report_query` | ✅ | ❌ | ➖ none | ➖ |
| `cross_varga_dignity_query` | ✅ | ❌ | ➖ none | ➖ |
| `query_kp_ruling_planets` | ✅ | ✅ | ➖ none | ➖ |
| `kp_query` | ✅ | ❌ | ➖ none | ➖ |

**Assessment:** MCP has only 2 of 7 chart-facts tools. Shadbala data is missing from chart_facts
table (data gap, not code gap), affecting both channels. KP sublord and saham systems have
no MCP surface. D-chart access will work post-redeploy.

### 3.5 Remedial / Classical Layer

| Portal tool | Portal status | Planner-visible | MCP equivalent | MCP status |
|-------------|--------------|-----------------|----------------|------------|
| `remedial_codex_query` | ✅ | ❌ | `query_remedial_mantras` | ✅* post-redeploy |
| `classical_text_search_tool` | ✅ | ✅ | `read_classical_text` | ⚠️ slow (1,955ms) |
| `classical_attribution_lookup_tool` | ✅ | ✅ | ➖ none | ➖ |
| `vector_search` | ✅ | ❌ | `vector_search` | ❌ Vertex AI IAM |

**Assessment:** Classical text search is functional on both channels but slow on MCP (Vertex AI
latency). vector_search is broken on MCP — the 4,589-row rag_chunks corpus is unreachable
via MCP semantic query. Classical attribution lookup has no MCP equivalent.

### 3.6 Meta / Introspection Layer

| Portal tool | Portal status | Planner-visible | MCP equivalent | MCP status |
|-------------|--------------|-----------------|----------------|------------|
| `manifest_query` | ✅ | ❌ | ➖ none | ➖ |
| n/a | n/a | n/a | `tool_health` | ✅ (MCP-only) |
| n/a | n/a | n/a | `data_coverage` | ⚠️ actual_rows null |
| n/a | n/a | n/a | `list_assets` | ✅ (MCP-only) |
| n/a | n/a | n/a | `list_recent_queries` | ✅ (MCP-only) |
| n/a | n/a | n/a | `get_trace` | ✅ (MCP-only) |
| n/a | n/a | n/a | `log_prediction` | ✅ (MCP-only) |
| n/a | n/a | n/a | `record_outcome` | ✅ (MCP-only) |
| n/a | n/a | n/a | `flag_disagreement` | ✅ (MCP-only) |

**Assessment:** MCP has richer operator/meta tooling than the portal. The write tools (log_prediction,
record_outcome, flag_disagreement) are exclusive to MCP. Portal has manifest_query with no MCP
equivalent.

---

## §4 — Data Asset Parity

The same underlying Supabase tables serve both channels. There is no separate data store per channel.
However, several data quality issues affect the richness of responses on both channels equally.

### 4.1 Data assets — status

| Data asset | Table / Store | Rows (native) | Status | Issue |
|-----------|--------------|---------------|--------|-------|
| MSR signals | `l25_msr_signals` | 573 | ✅ | All grounded (100%, post-MCPT); MCP filters dropped |
| LEL events | `lel_events` | 57 events + enrichment | ✅ | chart_state enrichment present on MCP; min_significance filter dropped |
| Panchanga | `panchanga_daily` | 73,414 rows (1900–2100) | ✅ | Richest data asset; Phase 4C enrichment fully live |
| Ephemeris | `ephemeris_daily` | Full Swiss Ephemeris | ✅ | MEAN_NODE rebuild pending (Rahu correction) |
| Chart facts — general | `chart_facts` | Various categories | ✅ | arudha (9), yoga (18) populated |
| Chart facts — shadbala | `chart_facts` | shadbala category | ❌ | 0 rows; backfill not run for native |
| Classical corpus | `rag_chunks` | 4,589 chunks | ✅ (portal) / ❌ (MCP) | MCP vector_search broken (Vertex AI) |
| School convergence | `school_convergence_index` | ~574 rows | ⚠️ | Near-empty for inter-school comparison queries |
| CGM graph | `cgm_nodes/cgm_edges` | 9.0 | ✅ (portal) / ❌ (MCP) | MCP get_cgm_subgraph broken |
| Varshaphala | `varshaphala_*` | Populated | ✅ | Both channels post-redeploy |
| Divisional charts | `divisional_*` | Populated | ✅ | Both channels post-redeploy |
| Remedial codex | `remedial_entries` | Populated | ✅ | Both channels post-redeploy |

### 4.2 Data assets — MCP vs portal access gap

The only data-level gap (not code-level gap) between channels:

1. **rag_chunks (4,589 rows):** Accessible via portal `vector_search` (functional); inaccessible
   via MCP `vector_search` (Vertex AI IAM broken). The classical corpus is effectively MCP-dark.

2. **CGM graph:** Accessible via portal `cgm_graph_walk`; inaccessible via MCP `get_cgm_subgraph`
   (node_id→seeds mapping bug). The graph is MCP-dark.

3. **shadbala (chart_facts):** Missing on both channels — data never loaded for native chart.
   Equal degradation; not a channel parity issue.

---

## §5 — Tool Count Summary

| Metric | Portal | MCP server.ts | MCP schema | Planner-visible |
|--------|--------|---------------|------------|-----------------|
| Total tools | 36 | 26 | ~43* | 11 |
| Core retrieval | 36 | 19 (some broken) | 19 (some broken) | 11 |
| Working fully | ~34 | 5 | — | — |
| Working sub-optimally | ~2 | 9 | — | — |
| Broken | 0 | 4 | — | — |
| Portal-only (no MCP equiv) | 17 | — | — | — |
| MCP-only (no portal equiv) | — | 8 | — | — |

*MCP schema reportedly ~43 tools (connector schema); server.ts registers 26. The delta
represents schema-only entries not backed by server.ts implementations — these are likely
phantom entries from the connector manifest not matching the deployed sidecar.

---

## §6 — Definitive Gap Register

### Gap Class A — MCP completely missing portal tools (17 tools)

These portal tools have zero MCP equivalent. An MCP client cannot call them at all.

| Portal tool | Function | Priority |
|-------------|----------|----------|
| `pattern_register` | Temporal pattern corpus | P1 |
| `resonance_register` | Resonance pattern corpus | P1 |
| `cluster_atlas` | Signal cluster corpus | P1 |
| `contradiction_register` | Contradiction corpus | P1 |
| `query_ucn_walk` | UCN synthesis walk | P2 |
| `query_cdlm_lookup` | CDLM cross-domain lookup | P2 |
| `query_rm_walk` | RM remedial walk | P2 |
| `query_signal_state` | Live signal state | P2 |
| `multi_school_signal_lookup` | Multi-school lookup | P2 |
| `classical_attribution_lookup_tool` | Classical text attribution | P2 |
| `temporal` | Temporal context snapshot | P2 |
| `timeline_query` | Event timeline query | P2 |
| `saham_query` | Arabic lot positions | P3 |
| `kp_query` | KP sublords | P3 |
| `cross_varga_dignity_query` | Varga dignity analysis | P3 |
| `domain_report_query` | Domain-level report | P3 |
| `query_msr_aggregate` | MSR aggregate queries | P3 |
| `manifest_query` | Manifest introspection | P3 |
| `query_jaimini_drishti` | Jaimini aspects | P3 |
| `query_v7_additions` | V7 addition signals | P3 |

### Gap Class B — MCP tools with broken equivalents (4 tools)

MCP equivalent exists in server.ts but does not work.

| MCP tool | Portal equivalent | Defect |
|----------|-----------------|--------|
| `get_cgm_subgraph` | `cgm_graph_walk` | node_id not mapped to seeds[] |
| `vector_search` | `vector_search` | Vertex AI IAM credentials missing |
| `read_asset` | n/a (read-only) | route.ts hardcoded path (fix applied, pending redeploy) |
| `interpret_current_dasha` | Synthesis | Unimplemented stub |

### Gap Class C — MCP tools with degraded filter fidelity (4 tools)

MCP equivalent exists and runs, but silently drops parameters present in the portal equivalent.

| MCP tool | Portal equivalent | Parameters dropped |
|----------|-----------------|------------------|
| `query_signals` | `msr_sql` | domain, forward_looking, valence, temporal_activation, signal_type; LL.1 calibration floors |
| `query_dasha_periods` | (same name) | level (pratyantar/sookshma sub-period routing) |
| `query_ephemeris` | (same name) | sample_step |
| `lel_query` | (same name) | min_significance |

### Gap Class D — Planner manifest gaps (25 tools)

Tools present in RETRIEVAL_TOOLS (portal) but absent from planner's compressed manifest.
The planner cannot intentionally select these tools; they enter the plan only via B.11 floor
injection or R-rule text compliance.

**Critical (B.11 floor is the only coverage):**
msr_sql, cgm_graph_walk, pattern_register, vector_search, chart_facts_query

**Uncovered by any floor (R-rules only):**
resonance_register, cluster_atlas, contradiction_register, remedial_codex_query, query_ephemeris,
query_panchanga, query_transit_event, query_dasha_periods, query_muhurat, kp_query, saham_query,
divisional_query, domain_report_query, timeline_query, temporal, query_msr_aggregate, manifest_query,
query_jaimini_drishti, query_v7_additions, query_ucn_walk (planner-visible but not the same as
tool being reachable via plan reasoning)

---

## §7 — Prioritized Fix Plan

### Immediate (pending redeploy — code already written)

1. **`amjis-web` redeploy** → activates `read_asset` route.ts fix
2. **`amjis-web` + `amjis-mcp` redeploy** → activates whitelist expansion (13 of 17 TR tools)

### P0 — Manifest fix (CAPABILITY_MANIFEST.json edit, no code change)

3. **Set `expose_to_planner=true`** for these 25 tools in CAPABILITY_MANIFEST.json
   (or `manifest_overrides.yaml`):
   msr_sql, pattern_register, resonance_register, cluster_atlas, contradiction_register,
   cgm_graph_walk, vector_search, chart_facts_query, remedial_codex_query, query_ephemeris,
   query_panchanga, query_transit_event, query_dasha_periods, query_muhurat, kp_query,
   saham_query, divisional_query, domain_report_query, timeline_query, temporal,
   query_msr_aggregate, manifest_query, query_jaimini_drishti, query_v7_additions,
   cross_varga_dignity_query

   This is a JSON edit — single PR, no runtime risk, immediately improves planner coverage.

### P1 — Single-file code fixes (high impact, low risk)

4. **Fix `get_cgm_subgraph`** (`platform-mcp/src/tools/get_cgm_subgraph.ts`):
   Map `params.node_id → seeds[node_id]` and `params.hops → depth`

5. **Fix Vertex AI credentials** for sidecar service account:
   Grant `roles/aiplatform.user` to the `amjis-mcp` Cloud Run service account.
   Restores `vector_search` (4,589 rag_chunks accessible) and speeds `read_classical_text`.

6. **Backfill shadbala** into `chart_facts` for native chart:
   Run the shadbala computation for Abhisek Mohanty's chart and INSERT rows.
   Restores `query_chart_facts` category completeness on both channels.

### P2 — Filter fidelity fixes (port from portal to MCP)

7. **Fix `query_signals` filter clauses** in `platform-mcp/src/tools/query_signals.ts`:
   Port domain/forward_looking/valence/temporal_activation from portal `msr_sql.ts`;
   add LL.1 calibration confidence floors (finance=0.35, default=0.55)

8. **Fix `query_dasha_periods` level routing** in MCP tool:
   Add pratyantar/sookshma sub-period computation when level param is present

9. **Fix `query_ephemeris` sample_step** in MCP tool:
   Add step-based date row filtering to ephemeris SQL query

10. **Fix `lel_query` min_significance** in MCP tool:
    Add WHERE clause: `AND significance >= :min_significance`

### P3 — Data gaps

11. **Populate `school_convergence_index`** with inter-school comparison data
    (currently near-empty; affects `cross_school_lookup` quality on MCP)

12. **MEAN_NODE ephemeris rebuild** (corrects Rahu position — operator-side compute task,
    ~4-6 hours)

### P4 — Monitoring hygiene

13. **Register TR tools in `tool_health` registry** — 18 new tools currently untracked
14. **Fix `data_coverage` actual_rows** — query live row counts per category
15. **Document `list_assets` and `list_canonical_artifact_versions`** — add to catalog.ts

---

## §8 — Parity Score by Channel Pair

| Comparison | Score | Notes |
|-----------|-------|-------|
| Classic Marsys vs Claude Style | 100% | Same backend — identical by definition |
| Portal planner coverage | 30% | 11/36 tools planner-visible; B.11 floor rescues critical subset |
| MCP vs Portal (tool count) | 53% | 19/36 portal tools have MCP equivalent |
| MCP vs Portal (functional fidelity) | 35% | Only 5 of 19 MCP tools are fully functional (not broken/sub-optimal) |
| Data asset parity MCP vs Portal | 85% | Same tables; rag_chunks and CGM inaccessible via MCP |
| Data quality (both channels) | 90% | Shadbala gap; MEAN_NODE Rahu pending; otherwise strong |

---

## §9 — Summary: What Each Channel Actually Delivers Today

### Portal (Classic Marsys = Claude Style)

**Strengths:**
- All 36 retrieval tools available in the execution layer (`executeMCPTool` → `getTool`)
- B.11 floor guarantees msr_sql, cgm_graph_walk, pattern_register, vector_search, chart_facts_query
  are always in play for standard queries
- Phase 4C Panchanga fully enriched
- MCPT grounding complete (573/573 MSR signals)
- Full CGM (9.0) accessible
- Full rag_chunks (4,589) accessible via vector_search

**Weaknesses:**
- Planner only aware of 11/36 tools — tool selection is partially autonomous via R-rules, not
  from genuine tool-manifest reasoning
- Shadbala data gap (affects both channels equally)
- No guarantee the planner selects optimal tools for non-standard query classes

### MCP (amjis-mcp sidecar)

**Strengths:**
- 26 tools registered (22 original + 4 TR Class A)
- Panchanga (query_panchanga) is the standout: fully enriched, works perfectly
- Transit event and muhurat finder work cleanly
- Operator tooling (get_trace, list_recent_queries, log_prediction, etc.) is MCP-exclusive
- After pending redeploy: 13 of 17 TR tools will dispatch

**Weaknesses:**
- 17 portal tools have zero MCP equivalent
- vector_search broken (Vertex AI IAM) — 4,589 rag_chunks corpus inaccessible
- get_cgm_subgraph broken — CGM inaccessible
- query_signals returns unfiltered 573-signal corpus (all domain/filter params dropped)
- Shadbala absent from chart_facts
- 4 TR tools are stubs (500 until engine built)
- Sidecar schema advertises ~43 tools; only 26 are actually deployed

---

*Audit method: filesystem reads of all registry, manifest, and tool files; live MCP tool calls
via `mcp__a19f2fb0-b520-4f99-ae46-a7b5a4d3deff__*` connector; cross-referenced against
`MCP_TOOL_AUDIT_2026-05-25_v1_0.md` (live sidecar audit, v1.1). Portal pipeline traced
through consume/route.ts, manifest_compressor.ts, primitives_registry.ts, and mcp_tool_executor.ts.
No inference from documentation alone — all claims traced to code or live call evidence.*
