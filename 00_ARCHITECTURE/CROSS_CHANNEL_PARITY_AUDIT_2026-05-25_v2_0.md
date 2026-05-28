# Cross-Channel Parity Audit — v2.0 (Corrected)
**Date:** 2026-05-25  
**Scope:** MCP sidecar (amjis-mcp), Portal Classic Marsys, Portal Claude Style  
**Method:** Live code inspection + live MCP tool testing  
**Supersedes:** CROSS_CHANNEL_PARITY_AUDIT_2026-05-25_v1_0.md (incorrect pipeline claim)

---

## Executive Summary

Three structural problems discovered:

1. **14 MCP tools are phantom** — registered in `server.ts` (schema-visible in Cowork connector) but absent from `primitives_registry.ts` whitelist. Every call returns a 400 validation error. This is a gap left by the Universal Parity Campaign, which added MCP tool registrations without updating the dispatcher whitelist.

2. **4 confirmed filter/param bugs** in existing whitelisted MCP tools — `forward_looking` always false, `sample_step` type mismatch, `valence` enum mismatch, `lel_query` significance mapping broken. These were never in scope for any prior campaign and remain unaddressed.

3. **Portal Classic Marsys vs Claude Style are architecturally distinct pipelines** — but the UI toggle does NOT control which runs. The server-side flag `MARSYS_FLAG_R11V2_USE_ADAPTERS=true` forces all portal queries through the adapter+agentic-loop path regardless of toggle position. The UI toggle controls R11B look-and-feel (typography/layout) only.

---

## §1 — Pipeline Architecture: Classic Marsys vs Claude Style

### Your model is architecturally correct

The two pipelines are genuinely different:

| | Classic Marsys (legacy) | Claude Style / Adapter Path |
|---|---|---|
| **Planner** | LLM planner → tool authorization list | LLM planner → tool authorization list |
| **Retrieval** | Deterministic tool execution | B.11 floor pre-execution (deterministic), then agentic loop |
| **Synthesis** | `createOrchestrator()` → `single_model_strategy` — one large LLM call with all retrieved context assembled as a bundle | Provider adapter → `runAgenticLoop()` — LLM iterates, calling tools itself up to 8 iterations |
| **LLM invocations** | Typically 2+ (planner + synthesizer) | Variable: planner + 1–8 loop iterations |
| **Context shape** | All retrieved context passed as a pre-assembled bundle to synthesizer | Tool results streamed into context incrementally as the loop runs |

### What actually controls which pipeline runs

The UI toggle (`SettingsDropdown`, `useChatShellMode`) writes to `localStorage.marsys.chatShellMode` and controls ONLY `isParityActive → r11bActive` = visual changes (typography, layout, bubble vs. no-bubble). It does NOT affect the request body sent to `/api/chat/consume`.

The actual pipeline gate is in `route.ts` line ~923:
```typescript
if (configService.getFlag('R11V2_USE_ADAPTERS')) {
  // adapter + agentic loop path
} else {
  // classic orchestrator path (legacy, not reached in production)
}
```

**Production state:** `MARSYS_FLAG_R11V2_USE_ADAPTERS=true` is set in Cloud Run. All portal requests go through the adapter path. The classic orchestrator is dead code in production.

**Implication:** The UI toggle is misleading — "Classic Marsys" and "Claude-style chat" are cosmetically different skins over the same backend pipeline. A user in "Classic Marsys" mode is running the agentic loop, not the context-assembly pipeline. This is a known deferred item (R11.F residuals).

---

## §2 — MCP Tool Execution Status

### Whitelisted tools (23 entries in `primitives_registry.ts`)

These work end-to-end via MCP. Filter fidelity issues are documented in §3.

| MCP Tool Name | Maps To (retrieval) | Status |
|---|---|---|
| query_chart_facts | chart_facts_query | ✅ Executes |
| query_signals | msr_sql | ✅ Executes (filter bugs — see §3) |
| query_dasha_periods | query_dasha_periods | ✅ Executes |
| query_panchanga | query_panchanga | ✅ Executes |
| query_ephemeris | query_ephemeris | ✅ Executes (sample_step bug — see §3) |
| query_transit_event | query_transit_event | ✅ Executes |
| lel_query | lel_query | ✅ Executes (significance bug — see §3) |
| vector_search | vector_search | ✅ Executes |
| get_cgm_subgraph | cgm_graph_walk | ✅ Executes |
| cross_school_lookup | multi_school_signal_lookup | ✅ Executes |
| read_classical_text | classical_text_search | ✅ Executes |
| query_varshphal | query_varshaphala | ✅ Executes (Class A alias) |
| query_divisional_chart | divisional_query | ✅ Executes (Class A) |
| query_remedial_mantras | remedial_codex_query | ✅ Executes (Class A) |
| muhurta_finder | query_muhurat | ✅ Executes (Class A) |
| query_varshaphala | query_varshaphala | ✅ Executes (pass-through alias) |
| divisional_query | divisional_query | ✅ Executes (pass-through alias) |
| remedial_codex_query | remedial_codex_query | ✅ Executes (pass-through alias) |
| query_muhurat | query_muhurat | ✅ Executes (pass-through alias) |
| query_tara_balam | query_tara_balam | ❌ Class B stub — retrieval tool not built |
| query_chandra_balam | query_chandra_balam | ❌ Class B stub — retrieval tool not built |
| jaimini_chara_dasha | jaimini_chara_dasha | ❌ Class B stub — retrieval tool not built |
| jaimini_chara_dasha_full | jaimini_chara_dasha_full | ❌ Class B stub — retrieval tool not built |

### Phantom tools — 14 UDA-added tools BLOCKED (400 on every call)

The UDA campaign (sessions UDA-2-S1 through UDA-2-S8) added 14 tools to `platform-mcp/src/server.ts` and created tool schemas. These appear in the Cowork MCP connector. But `primitives_registry.ts` was NOT updated. The dispatcher at `/api/mcp/primitives/[tool]/route.ts` calls `isAllowedSurgicalTool()` which returns false for all 14 names.

**Error returned:** `{"ok":false,"error":{"class":"validation","message":"Tool not in surgical whitelist: msr_sql"}}`

(Note: `msr_sql` is the MCP-facing name for one of the UDA tools — different from the portal internal name.)

| MCP Tool Name (in server.ts) | Portal Retrieval Tool | Status |
|---|---|---|
| msr_sql | msr_sql | ❌ PHANTOM — whitelist gap |
| pattern_register | pattern_register | ❌ PHANTOM — whitelist gap |
| cluster_atlas | cluster_atlas | ❌ PHANTOM — whitelist gap |
| resonance_register | resonance_register | ❌ PHANTOM — whitelist gap |
| contradiction_register | contradiction_register | ❌ PHANTOM — whitelist gap |
| query_ucn_walk | query_ucn_walk | ❌ PHANTOM — whitelist gap |
| query_cdlm_lookup | query_cdlm_lookup | ❌ PHANTOM — whitelist gap |
| query_rm_walk | query_rm_walk | ❌ PHANTOM — whitelist gap |
| query_signal_state | query_signal_state | ❌ PHANTOM — whitelist gap |
| temporal | temporal | ❌ PHANTOM — whitelist gap |
| timeline_query | timeline_query | ❌ PHANTOM — whitelist gap |
| kp_query | kp_query | ❌ PHANTOM — whitelist gap |
| query_kp_ruling_planets | query_kp_ruling_planets | ❌ PHANTOM — whitelist gap |
| query_jaimini_drishti | query_jaimini_drishti | ❌ PHANTOM — whitelist gap |

**Root cause:** `primitives_registry.ts` is the single source of truth for the dispatcher whitelist. The UDA campaign brief had scope: "register tool schemas in server.ts and ensure MCP-facing tool names exist." It did not include: "add to primitives_registry.ts." The SURGICAL_TOOLS array and MCP_TO_RETRIEVAL_TOOL map both require manual update.

**Fix:** Add all 14 to `SURGICAL_TOOLS` and `MCP_TO_RETRIEVAL_TOOL` in `primitives_registry.ts`. Redeploy amjis-web (the platform dispatcher) and amjis-mcp (the sidecar). This is a ~20-line code change.

---

## §3 — Filter Fidelity Findings (Live-Tested)

### BUG-1: `query_signals` — `forward_looking` always false

**Observed:** Sending `forward_looking: true` returns same results as no flag. Invocation_params logs `forward_looking: false`.

**Root cause:** In the primitive dispatcher route (`/api/mcp/primitives/[tool]/route.ts`), the `queryPlan` is hardcoded:
```typescript
const queryPlan = {
  domains: [],
  forward_looking: false,  // ← hardcoded, never updated from toolParams
  ...
}
```

Portal `msr_sql` builds `forwardLookingFilter` from `plan.forward_looking`, not from `params.forward_looking`. The F.2 fix (added during DAR campaign) corrected the domain fallback to read from params, but was NOT applied to `forward_looking`. The params value arrives in `toolParams` but is never read.

**Impact:** Every MCP query for forward-looking signals returns past + future signals mixed, violating the filter contract. Prospective prediction queries cannot isolate upcoming signals via MCP.

**Fix:** In `msr_sql.ts`, change:
```typescript
const forwardLookingFilter: boolean | null = plan.forward_looking ? true : null
```
to:
```typescript
const paramsForwardLooking = params?.forward_looking as boolean | undefined
const forwardLookingFilter: boolean | null = 
  paramsForwardLooking !== undefined ? (paramsForwardLooking ? true : null) : (plan.forward_looking ? true : null)
```

### BUG-2: `query_signals` — `valence` enum mismatch (0 results)

**Observed:** Sending `valence: "positive"` returns 0 results despite ~499 signals in corpus.

**Root cause:** The `msr_signals` table stores valence as `"benefic"`, `"malefic"`, `"context-dependent"`. The MSR document (v5.0) uses this vocabulary throughout. The MCP tool schema defines `valence` as `z.enum(['positive', 'negative', 'neutral'])` — a completely different vocabulary. The SQL filter `valence = ANY(['positive'])` matches zero rows.

**Impact:** The entire valence filter is non-functional. Any call using `valence: "positive"` or `"negative"` returns empty.

**Fix:** Either (a) translate in the MCP tool: `"positive" → "benefic"`, `"negative" → "malefic"`, `"neutral" → "context-dependent"` before calling callPlatformPrimitive; or (b) update the schema enum to match the DB. Option (a) is safer (no migration needed). The description already says `"positive" = benefic outcomes` so the mapping intent is clear.

### BUG-3: `query_ephemeris` — `sample_step` type mismatch (silently ignored)

**Observed:** Sending `sample_step: "7d"` for a 90-day range returns ~91 rows (full daily resolution) instead of ~13 rows. The sample_step is silently ignored.

**Root cause:** The MCP tool defines `sample_step` as `z.enum(['1d', '7d', '30d'])` and sends the string value to `callPlatformPrimitive`. The portal `QueryEphemerisInput` defines `sample_step?: number`. The portal filter is:
```typescript
if (input.sample_step !== undefined && input.sample_step > 1) {
  rows = rows.filter((_, i) => i % input.sample_step! === 0)
}
```
When `input.sample_step` is the string `"7d"`, the comparison `"7d" > 1` evaluates to `false` (NaN), so the filter never runs.

**Impact:** Wide-range ephemeris queries return full daily rows. A 1-year query returns ~9×365=3,285 rows instead of ~9×52=468. Significant token waste and slower responses.

**Fix:** In the MCP tool's `callPlatformPrimitive` call, translate the string enum to a numeric interval:
```typescript
const sampleStepMap = { '1d': 1, '7d': 7, '30d': 30 }
sample_step: sampleStepMap[args.sample_step ?? '1d'],
```

### BUG-4: `lel_query` — `significance_tier` not applied at SQL level

**Observed:** Sending `significance_tier: "major"` appears to filter correctly (all returned events are major), but this is coincidental — the native's LEL only contains major career events. Other significance levels return incorrect results.

**Root cause:** The MCP tool correctly maps `significance_tier → min_significance` (e.g. `"major" → 0.8`) and passes `min_significance` to callPlatformPrimitive. However, the portal `lel_query` reads `params?.significance` (a string enum field), not `params?.min_significance` (a float). The SQL clause is `significance = $N` (exact match), not `significance >= $N`. The `min_significance` float never reaches the SQL filter.

**Impact:** `significance_tier: "minor"` or `"moderate"` filters fail silently; all events are returned regardless of significance.

**Fix:** The portal `lel_query` should read `params?.min_significance` and map it to a tier string for the SQL, or use a numeric column comparison. The SQL should be `significance_score >= $N` if a numeric column exists, or the MCP should send the tier string directly.

### ANOMALY: `lel_query` — source_version reports v1.6, canonical is v1.7

**Observed:** Live call returned `source_version: "1.6"`.

**Root cause:** The `lel_query` tool hardcodes `source_version: '1.6'` (or derives it from data in the `life_events` table). The canonical LEL is now v1.7 (`01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md`). Either the tool's version annotation was not bumped when LEL advanced to v1.7, or the `life_events` table was not refreshed with the v1.7 data.

**Impact:** Version audit trail is inaccurate. Callers cannot distinguish v1.6 from v1.7 data via the source_version field.

**Fix:** Check `life_events` table row count and whether v1.7 events are present. Update hardcoded version annotation in `lel_query.ts`.

### NOTE (NOT a bug): `query_dasha_periods` level/invocation_params

**Earlier observation:** The live test invocation_params showed `level` absent.  
**Actual behavior:** CORRECT. The MCP `query_dasha_periods` does NOT pass `level` to `callPlatformPrimitive` — it passes only `at`, `range`, and `system`. The `enrichPeriods()` function runs entirely inside the MCP sidecar after receiving the flat platform response. `level:"pratyantar"` is handled, and each AD row in the returned `periods` array should carry a `sub_periods` array of 9 PD entries. The invocation_params not showing `level` is expected because `level` is a post-processing param, not a SQL filter. If sub_periods are absent in a live response, that is a separate issue to investigate (possibly the `enrichPeriods` function is not being reached for some input shapes).

### NOTE (misleading log, not a bug): `query_signals` domain in invocation_params

The invocation_params log shows `domains: []` because it logs `plan.domains` (from the hardcoded QueryPlan with `domains: []`), not the effective domains from `params`. The actual SQL filter uses `effectiveDomains` which reads from `params.domain` — so domain filtering IS working. The logging is misleading. This was the F.2 fix from the DAR campaign.

---

## §4 — Tool-to-Data-Asset Mapping (All 51 Portal Tools)

**Data asset version key:**
- MSR = `MSR_v5_0.md` (573 signals, table `msr_signals`)
- FORENSIC = `FORENSIC_ASTROLOGICAL_DATA_v8_0.md` (table `chart_facts`)
- LEL = `LIFE_EVENT_LOG_v1_2.md` v1.7 (table `life_events`)
- CGM = `CGM_v9_0.md` (tables `l25_cgm_nodes`, `l25_cgm_edges`)
- UCN = `UCN_v4_0.md` (in-memory / rag_chunks)
- CDLM = `CDLM_v1_1.md` v1.3 (in-memory / rag_chunks)
- RM = `RM_v2_0.md` v2.2 (in-memory / rag_chunks)
- RAG_CHUNKS = `rag_chunks` table (4,589 indexed chunks: BPHS, Jaimini, KP, Tajaka)
- EPHEMERIS = `ephemeris_daily` table (1930–2100)
- PANCHANGA = `panchanga_daily` table (1900–2100, 73,414 rows)
- KP_SUBLORDS = `kp_sublords` table (chart_facts KP columns)
- VARSHAPHALA = `varshaphala` table
- SIGNAL_STATES = `signal_states` table

| # | Tool Name | Primary Table(s) / Asset | Asset Version | Full Asset Leverage? |
|---|---|---|---|---|
| 1 | msr_sql | `msr_signals` | MSR v5.0 (573 signals) | ⚠️ forward_looking bug; valence mismatch |
| 2 | pattern_register | `rag_chunks` (pattern type) | PATTERN_REGISTER_v1_0 | ✅ |
| 3 | resonance_register | `rag_chunks` (resonance type) | RESONANCE_REGISTER_v1_0 | ✅ |
| 4 | cluster_atlas | `rag_chunks` (cluster type) | CLUSTER_ATLAS_JSON | ✅ |
| 5 | contradiction_register | `rag_chunks` (contradiction type) | CONTRADICTION_REGISTER_v1_0 | ✅ |
| 6 | temporal | Sidecar `/dasha_chain` endpoint | EPHEMERIS (sidecar) | ✅ |
| 7 | query_msr_aggregate | `msr_signals` (aggregate) | MSR v5.0 | ✅ |
| 8 | cgm_graph_walk | `l25_cgm_nodes`, `l25_cgm_edges` | CGM v9.0 | ✅ |
| 9 | manifest_query | CAPABILITY_MANIFEST.json schemas | Manifest current | ✅ |
| 10 | vector_search | `rag_embeddings` + `rag_chunks` | RAG_CHUNKS (4,589 chunks) | ✅ |
| 11 | kp_query | `chart_facts` (KP columns) | FORENSIC v8.0 | ✅ |
| 12 | saham_query | `chart_facts` | FORENSIC v8.0 | ✅ |
| 13 | divisional_query | `chart_facts` | FORENSIC v8.0 | ✅ |
| 14 | chart_facts_query | `chart_facts` | FORENSIC v8.0 | ✅ |
| 15 | cross_varga_dignity_query | `chart_facts` (D1/D9/D10) | FORENSIC v8.0 | ✅ |
| 16 | domain_report_query | `rag_chunks` (domain_report type) | DOMAIN_REPORT | ✅ |
| 17 | remedial_codex_query | `rag_chunks` (l4_remedial type) | REMEDIAL_CODEX_v2_0 | ✅ |
| 18 | timeline_query | `rag_chunks` (l5_timeline type) | LIFE_EVENTS / LEL | ✅ |
| 19 | query_signal_state | `signal_states` | SIGNAL_STATES | ✅ |
| 20 | query_kp_ruling_planets | `kp_sublords`, `chart_facts` | KP_SUBLORDS / FORENSIC v8.0 | ✅ |
| 21 | query_varshaphala | `varshaphala`, `chart_facts` (sidecar) | VARSHAPHALA | ✅ |
| 22 | lel_query | `life_events` | LEL v1.7 (reports v1.6 — see §3) | ⚠️ significance bug; version mismatch |
| 23 | classical_text_search_tool | `rag_chunks` (classical type) | RAG_CHUNKS (BPHS/Jaimini/KP/Tajaka) | ✅ |
| 24 | classical_attribution_lookup_tool | `rag_chunks` (classical type) | RAG_CHUNKS | ✅ |
| 25 | multi_school_signal_lookup_tool | `school_signal_coverage` | school_signal_coverage | ✅ |
| 26 | convergence_score_lookup_tool | `convergence_scores` | school convergence_scores | ✅ |
| 27 | query_ephemeris | `ephemeris_daily` | EPHEMERIS_DAILY (1930–2100) | ⚠️ sample_step bug |
| 28 | query_panchanga | `panchanga_daily` | PANCHANGA_DAILY (73,414 rows) | ✅ |
| 29 | query_transit_event | `ephemeris_daily`, `chart_facts` | EPHEMERIS_DAILY / FORENSIC v8.0 | ✅ |
| 30 | query_dasha_periods | `chart_facts` (dasha categories) | FORENSIC v8.0 | ✅ level handled in MCP |
| 31 | query_muhurat | `panchanga_daily` | PANCHANGA_DAILY | ✅ |
| 32 | query_jaimini_drishti | `chart_facts` (sidecar) | FORENSIC v8.0 | ✅ |
| 33 | query_v7_additions | `chart_facts` (sidecar v7 endpoints) | FORENSIC v8.0 | ✅ |
| 34 | query_ucn_walk | UCN in-memory / rag_chunks | UCN v4.1 | ✅ |
| 35 | query_cdlm_lookup | CDLM in-memory / rag_chunks | CDLM v1.3 | ✅ |
| 36 | query_rm_walk | RM in-memory / rag_chunks | RM v2.2 | ✅ |
| 37 | query_transits_over_natal | `ephemeris_daily`, `chart_facts` | EPHEMERIS_DAILY / FORENSIC v8.0 | ✅ |
| 38 | query_yogas_active_now | `chart_facts` | FORENSIC v8.0 | ✅ |
| 39 | get_planet_avastha | `chart_facts` (dignity columns) | FORENSIC v8.0 | ✅ |
| 40 | get_shadbala_full | `chart_facts` (shadbala columns) | FORENSIC v8.0 | ✅ |
| 41 | query_jaimini_chara_dasha | `chart_facts` (sidecar) | FORENSIC v8.0 | ✅ |
| 42 | query_planetary_period_predictions | `rag_chunks` + vector_search | RAG_CHUNKS / FORENSIC v8.0 | ✅ |
| 43 | query_dasamsha_career | `chart_facts` (D10) | FORENSIC v8.0 | ✅ |
| 44 | query_shashtiamsha | `chart_facts` (D60) | FORENSIC v8.0 | ✅ |
| 45 | query_eclipse_transits | `ephemeris_daily` | EPHEMERIS_DAILY | ✅ |
| 46 | query_planet_war | `ephemeris_daily` | EPHEMERIS_DAILY | ✅ |
| 47 | query_drekkana_drishti | `chart_facts` (sidecar) | FORENSIC v8.0 | ✅ |
| 48 | query_remedies_prescribed | `rag_chunks` (l4_remedial) | REMEDIAL_CODEX_v2_0 | ✅ |
| 49 | tara_balam_for_native | `panchanga_daily`, `ephemeris_daily` | PANCHANGA_DAILY / FORENSIC v8.0 | ✅ |
| 50 | chandra_balam_for_native | `panchanga_daily`, `ephemeris_daily` | PANCHANGA_DAILY / FORENSIC v8.0 | ✅ |
| 51 | muhurta_finder | `panchanga_daily` | PANCHANGA_DAILY | ✅ |

**Summary:** 47/51 tools fully leverage their data assets. 4 tools have confirmed filter/param bugs (tools #1, #22, #27, and implicitly #1 again for valence).

---

## §5 — Planner Visibility Analysis

### How planner visibility works

The portal planner uses `compressManifest()` from `manifest_compressor.ts`, which filters `CAPABILITY_MANIFEST.json` entries to those with `expose_to_planner === true`. Additionally, B.11 floor tools are force-injected post-planning regardless of planner exposure.

### Tools with `expose_to_planner: true` (25 in manifest)

| Tool | Linked Asset | Category |
|---|---|---|
| msr_sql | MSR | Core synthesis |
| pattern_register | PATTERN_REGISTER | Core synthesis |
| resonance_register | RESONANCE_REGISTER | Core synthesis |
| cluster_atlas | CLUSTER_ATLAS | Core synthesis |
| contradiction_register | CONTRADICTION_REGISTER | Core synthesis |
| query_transits_over_natal | EPHEMERIS_DAILY | Transit |
| get_cgm_subgraph / cgm_graph_walk | CGM | Holistic |
| manifest_query | CAPABILITY_MANIFEST | Meta |
| vector_search | RAG_CHUNKS | Classical |
| kp_query | KP_SUBLORDS | KP system |
| saham_query | FORENSIC | Tajaka |
| chart_facts_query | FORENSIC | Core facts |
| cross_varga_dignity_query | FORENSIC | Divisional |
| domain_report_query | DOMAIN_REPORT | Domain reports |
| remedial_codex_query | REMEDIAL_CODEX | Remedial |
| lel_query | LEL | Life events |
| query_signal_state | SIGNAL_STATES | Signal state |
| query_kp_ruling_planets | KP_SUBLORDS | KP |
| query_varshaphala | VARSHAPHALA | Annual chart |
| multi_school_signal_lookup | school_signal_coverage | Multi-school |
| convergence_score_lookup | convergence_scores | Multi-school |
| query_ucn_walk | UCN | L2.5 |
| query_cdlm_lookup | CDLM | L2.5 |
| query_rm_walk | RM | L2.5 |
| muhurta_finder | PANCHANGA_DAILY | Muhurta |

### B.11 floor tools (force-injected regardless of planner)

From `route.ts` hardcoded post-planning injection: `msr_sql`, `cgm_graph_walk`, `pattern_register`, `vector_search`, `chart_facts_query`. These 5 are always executed.

### Tools NOT planner-visible (not expose_to_planner, not B.11 floor)

The following 26 tools are available in RETRIEVAL_TOOLS but reachable only if the planner explicitly selects them or they are called via the agentic loop:

`temporal`, `query_msr_aggregate`, `divisional_query`, `kp_query`, `timeline_query`, `classical_text_search_tool`, `classical_attribution_lookup_tool`, `query_ephemeris`, `query_panchanga`, `query_transit_event`, `query_dasha_periods`, `query_muhurat`, `query_jaimini_drishti`, `query_v7_additions`, `query_transits_over_natal` (has expose_to_planner), `query_yogas_active_now`, `get_planet_avastha`, `get_shadbala_full`, `query_jaimini_chara_dasha`, `query_planetary_period_predictions`, `query_dasamsha_career`, `query_shashtiamsha`, `query_eclipse_transits`, `query_planet_war`, `query_drekkana_drishti`, `query_remedies_prescribed`, `tara_balam_for_native`, `chandra_balam_for_native`, `saham_query` (has expose_to_planner)

### Is there harm in making all tools planner-visible?

Not from a security or data perspective — all tools are already available. The cost is planner prompt bloat. The planner's context window has limited space; adding 26 more tool descriptions increases the chance of the planner making poor selection choices due to cognitive overload. The current 25 + B.11 floor 5 = ~30 tool references already represent a substantial prompt. Exposing all 51 would likely degrade planner precision.

**Recommendation:** The current selection is well-calibrated. The 26 non-exposed tools cover highly specific use cases (eclipse detection, Graha Yuddha, D60, Drekkana Drishti) that are rarely the top-priority tool for a general query. The planner should stay narrow; the agentic loop can call them when needed.

---

## §6 — Why Filter Issues Persist Despite the DAR and Universal Parity Campaigns

### Campaign scope was never "fix filter bugs"

Each prior campaign had a specific, bounded scope:

| Campaign | Scope | Did it include filter fixes? |
|---|---|---|
| DAR (27 sessions) | Data asset reconciliation — clean up ephemeris gaps, verify table schema, ensure data quality, reconcile FORENSIC/LEL/MSR ground truth | ❌ No — code quality was out of scope |
| Universal Parity Campaign UDA-1 (8 sessions) | Portal retrieval tool count 36→51, add 15 new UDA tool implementations | ❌ No — existing tool behavior was out of scope |
| Universal Parity Campaign UDA-2 (10 sessions) | MCP tool count 26→40, add 14 MCP tool registrations in server.ts | ❌ No — and critically: no scope to update primitives_registry.ts |
| Tooling Remediation v1.0 (PR #159) | Add TR Wave Class A MCP primitives (query_varshphal, etc.) | Partial — added new primitives but existing filter bugs untouched |

### The filter bugs predate all these campaigns

The `forward_looking` routing bug, `sample_step` type mismatch, and `valence` enum mismatch were all present before DAR or UDA started. They have never been in any campaign's acceptance criteria. No session has ever been given the brief: "verify that every parameter of every MCP tool actually filters the SQL as documented."

### The F.2 fix was partial

The DAR campaign introduced a F.2 fix to `msr_sql.ts` that corrected the `domain` filter to read from `params.domain` rather than only `plan.domains`. This was a targeted fix for one specific symptom. It was not extended to `forward_looking` (same pattern) or `valence` (different problem).

### No regression test coverage

There are no automated tests that send `forward_looking: true` via MCP and assert the returned signals are all `is_forward_looking = true`. Without test coverage, these bugs survive every refactor and every merge. They are invisible until a deep audit like this one.

---

## §7 — Prioritized Fix List

### P0 — Fix immediately (broken functionality)

| ID | Fix | File | Effort |
|---|---|---|---|
| FIX-1 | Add 14 UDA tools to `primitives_registry.ts` SURGICAL_TOOLS + MCP_TO_RETRIEVAL_TOOL | `platform/src/lib/mcp/primitives_registry.ts` | ~20 lines, 1 hour |
| FIX-2 | Fix `forward_looking` param routing: read from `params.forward_looking` in `msr_sql.ts` | `platform/src/lib/retrieve/msr_sql.ts` | ~5 lines, 30 min |
| FIX-3 | Fix `valence` enum: translate "positive"→"benefic", "negative"→"malefic", "neutral"→"context-dependent" | `platform-mcp/src/tools/query_signals.ts` | ~5 lines, 30 min |
| FIX-4 | Fix `sample_step` type: translate "7d"→7, "30d"→30, "1d"→1 before callPlatformPrimitive | `platform-mcp/src/tools/query_ephemeris.ts` | ~5 lines, 30 min |
| FIX-5 | Fix `lel_query` significance: send `significance` string directly, not `min_significance` float, to callPlatformPrimitive | `platform-mcp/src/tools/lel_query.ts` | ~5 lines, 30 min |

### P1 — Fix soon (data accuracy / audit trail)

| ID | Fix | File | Effort |
|---|---|---|---|
| FIX-6 | Update `lel_query` source_version annotation to v1.7 | `platform/src/lib/retrieve/lel_query.ts` | ~1 line |
| FIX-7 | Fix invocation_params logging in `msr_sql.ts` to log the params-derived effectiveDomains, not plan.domains | `platform/src/lib/retrieve/msr_sql.ts` | ~5 lines |

### P2 — Address before next audit

| ID | Fix | Rationale |
|---|---|---|
| FIX-8 | Wire UI toggle to pipeline selection — currently "Classic Marsys" mode runs the adapter path | The toggle is cosmetic-only; the stated behavior ("Familiar interface with full Marsys branding") implies a different pipeline, which is misleading |
| FIX-9 | Add E2E tests for filter fidelity: query_signals with forward_looking:true should assert all results have is_forward_looking=true | Prevents regression |
| FIX-10 | Add valence filter coverage test: query_signals with valence:"benefic" should return non-empty | Confirms enum alignment post-fix |

---

## §8 — Channel Parity Summary

| Capability | MCP | Portal (both modes) | Gap |
|---|---|---|---|
| Chart facts (37 categories) | ✅ query_chart_facts | ✅ chart_facts_query | None |
| 573 MSR signals | ✅ query_signals (with bugs) | ✅ msr_sql | forward_looking + valence bugs in MCP path |
| Life event log | ✅ lel_query (with bugs) | ✅ lel_query | significance bug in MCP path |
| Ephemeris (1930–2100) | ✅ query_ephemeris (with bugs) | ✅ query_ephemeris | sample_step bug in MCP path |
| Dasha periods (sub-period) | ✅ query_dasha_periods | ✅ query_dasha_periods | None (MCP does enrichment client-side) |
| Panchanga daily | ✅ query_panchanga | ✅ query_panchanga | None |
| CGM graph walk | ✅ get_cgm_subgraph | ✅ cgm_graph_walk | None |
| Vector search | ✅ vector_search | ✅ vector_search | None |
| Classical text (BPHS/Jaimini/KP/Tajaka) | ✅ read_classical_text | ✅ classical_text_search_tool | None |
| Multi-school lookup | ✅ cross_school_lookup | ✅ multi_school_signal_lookup_tool | None |
| Varshaphala | ✅ query_varshphal | ✅ query_varshaphala | None |
| Divisional charts | ✅ query_divisional_chart | ✅ divisional_query | None |
| Remedial codex | ✅ query_remedial_mantras | ✅ remedial_codex_query | None |
| Muhurta finder | ✅ muhurta_finder | ✅ query_muhurat | None |
| CGM pattern/resonance/contradiction/cluster | ❌ PHANTOM (14 tools) | ✅ all 4 tools work | Major MCP gap |
| L2.5 structural (UCN/CDLM/RM walk) | ❌ PHANTOM | ✅ query_ucn_walk, query_cdlm_lookup, query_rm_walk | Major MCP gap |
| Timeline query / signal state | ❌ PHANTOM | ✅ works | MCP gap |
| KP ruling planets | ❌ PHANTOM | ✅ works | MCP gap |
| Jaimini Drishti | ❌ PHANTOM | ✅ works | MCP gap |
| Temporal sidecar | ❌ PHANTOM | ✅ works | MCP gap |
| UDA-1 tools (transits/yogas/avastha/shadbala/D10/D60/eclipse/planet_war/drekkana/remedies/tara/chandra) | Available but NOT in primitives_registry | ✅ portal | MCP phantom gap |

**Bottom line:** Portal has all 51 tools functional. MCP has 15 fully working, 4 with Class B stubs (not yet built), 14 phantom (whitelist gap), and 4 with filter bugs in otherwise-functional tools.

---

*End of audit. v2.0 supersedes v1.0. Primary corrections: pipeline architecture characterization (§1), phantom tool discovery (§2), root-cause analysis for each filter bug (§3), full tool-to-asset mapping (§4), campaign scope explanation (§6).*
