---
canonical_id: UNIVERSAL_PARITY_PLAN
version: 1.1
status: CURRENT
authored: 2026-05-25
authored_by: Cowork planning session
amended: 2026-05-25
amendment: Added §2.5 Quality Delta Matrix + Phase UDA-Q (Quality Backport, 8 sessions); total session count updated to 53
phase: Post-Tooling-Remediation / Pre-M5-B
---

# Universal Data Asset Parity Plan v1.1

## Purpose

Ensure every data asset and its associated retrieval mechanism is:
1. Available to **all three consumption channels** in its most enriched, production-quality form
2. **The best-available implementation of each shared tool is the version running in both channels** — no channel should be running a degraded version of a tool the other channel has enhanced
3. **Registered in CAPABILITY_MANIFEST.json** with canonical path, schema, layer, and status
4. **Rigorously tested** — every tool verified live in every channel it is registered for

This plan supersedes any prior per-workstream ad-hoc tool additions and establishes parity as a first-class governance obligation.

> **v1.1 amendment**: The original v1.0 plan addressed *presence* parity (missing tools). This amendment adds *quality* parity — ensuring the enhanced version of every shared tool is available to every channel that has it.

---

## §1 — Channel Architecture (Authoritative)

The system has **three consumption channels** sharing a single data asset layer (Postgres + GCS):

### Channel A — Portal Classic Marsys (planner path)
- Entry: `platform/src/app/api/chat/consume/route.ts` → `callPipelinePlanner()` → tool pre-fetch → LLM synthesis
- Tool registry: `platform/src/lib/retrieve/index.ts` → `RETRIEVAL_TOOLS[]` (36 tools as of 2026-05-25)
- Planner sees tools via `<manifest>` injected from `platform/src/lib/router/retrieval_capability_spec.ts`
- LLM model: Gemini Flash (planner_fast), Gemini Pro (planner_critical) — per `PLANNER_PROMPT_v2_0.md`

### Channel B — Portal Claude-style (agentic loop path, R11.F-activated)
- Entry: same `route.ts` → `runAgenticLoop()` → `executeMCPTool()` → `getTool()` from RETRIEVAL_TOOLS
- Tool registry: **same 36 RETRIEVAL_TOOLS** via `platform/src/lib/synthesis/mcp_tool_executor.ts`
- LLM sees tool schemas via `tool_catalogue.ts` → `buildChatToolsFromNames()` from RETRIEVAL_TOOLS
- LLM model: Claude Sonnet / Gemini / etc. per R11.A-E multi-provider adapter

**Key architectural fact**: Channel A and Channel B currently share the identical 36-tool RETRIEVAL_TOOLS registry. They are two consumption modes, not independent tool surfaces. `executeMCPTool` dispatches via local `getTool()`, NOT via the remote MCP sidecar.

### Channel C — MCP Sidecar (external connector)
- Entry: `amjis-mcp` Cloud Run sidecar (asia-south1) → `platform-mcp/src/server.ts`
- Tool registry: 41 tools registered in `server.ts` (post-TR bace7b45)
- Accessed by: Cowork MarsysJIS connector, Claude Code Claude-style client, any MCP-protocol consumer
- Write tools (log_prediction, record_outcome, flag_disagreement) are Channel C–only by design

---

## §2 — Current State: Three-Channel Tool Matrix

### §2.1 — Shared tools (present in ALL channels)

| Portal name | MCP name | Data surface | Notes |
|---|---|---|---|
| query_ephemeris | query_ephemeris | ephemeris_daily | Both fixed TR-P1-S2 |
| query_panchanga | query_panchanga | panchanga_daily (73K rows, enriched) | Both fixed TR-P1-S3 |
| query_transit_event | query_transit_event | transit_events table | Both fixed TR-P1-S1 |
| query_dasha_periods | query_dasha_periods | dasha_chain sidecar | Same data surface |
| lel_query | lel_query | life_events (36 events + patterns) | Same tool file |
| vector_search | vector_search | rag_chunks (4,589 classical) | Same data surface |
| chart_facts_query | query_chart_facts | chart_facts (2,717 rows) | Name differs — same data |
| divisional_query | query_divisional_chart | divisional chart tables | Different interface depth |
| query_varshaphala | query_varshphal | varshaphala/annual charts | Name differs — same data |
| remedial_codex_query | query_remedial_mantras | remedial_codex table | Partial overlap |
| classical_text_search_tool | read_classical_text | rag_chunks classical texts | Search vs read — complementary |
| multi_school_signal_lookup_tool | cross_school_lookup | school_convergence_index (574 rows) | Partial overlap |
| query_muhurat | muhurta_finder | muhurta engine | Different interface |
| cgm_graph_walk | get_cgm_subgraph | CGM v9.0 graph | Similar, different depth |
| convergence_score_lookup_tool | (cross_school_lookup) | convergence scores | Partial coverage in MCP |

**Count: 15 tools with some representation in both portal and MCP** (most with naming or schema gaps)

---

### §2.2 — Portal-only tools (MISSING from MCP Channel C)

These 21 tools are in `RETRIEVAL_TOOLS` but have **zero MCP counterpart**. Claude and Cowork users cannot invoke them.

| Tool name | Data surface | Priority |
|---|---|---|
| msr_sql | MSR v3.0 — 573 signals, confidence, domains, dasha_activation | **CRITICAL** |
| pattern_register | Pattern Register — named yogas, configurations (PAT.NNN) | HIGH |
| resonance_register | Cross-signal resonances — reinforcement clusters (RES.NNN) | HIGH |
| cluster_atlas | Meta-patterns — life-shape clusters (CLU.NNN) | HIGH |
| contradiction_register | Cross-chart tensions and resolution hints (CONT.NNN) | HIGH |
| temporal | Unified dasha + transit + eclipse + retrograde time tool | HIGH |
| query_msr_aggregate | Cross-chart MSR rollups, cohort statistics | MEDIUM |
| kp_query | KP sub-lord analysis, significators | HIGH |
| saham_query | Saham (Arabic part) positions and significance | MEDIUM |
| cross_varga_dignity_query | Cross-divisional dignity surface (CSI, D1-D60) | MEDIUM |
| domain_report_query | Compiled domain reports (career, health, etc.) | MEDIUM |
| timeline_query | Event-anchored timeline with dasha context | HIGH |
| query_signal_state | Signal activation states (active/dormant/triggered) | MEDIUM |
| query_kp_ruling_planets | KP ruling planets for a given moment | MEDIUM |
| classical_attribution_lookup_tool | Classical text attribution by planet/house/sign | MEDIUM |
| query_jaimini_drishti | Jaimini rashi drishti aspects | HIGH |
| query_v7_additions | V7 chart additions (supplementary factors) | LOW |
| query_ucn_walk | UCN v4.1 structured walk — theme resolution | HIGH |
| query_cdlm_lookup | CDLM v1.3 cross-domain linkage lookup | HIGH |
| query_rm_walk | RM v2.2 remedial matrix walk | MEDIUM |
| manifest_query | CAPABILITY_MANIFEST meta-lookup | LOW |

**Count: 21 portal-only tools**

---

### §2.3 — MCP-only tools (MISSING from portal Channels A + B)

These 12 high-value Class B engines were delivered by Tooling Remediation but are **invisible to both portal modes**. The portal planner cannot plan them; the agentic loop cannot call them.

| Tool name | Data surface | Priority |
|---|---|---|
| query_transits_over_natal | Transits over natal positions with orb filtering | **CRITICAL** |
| query_yogas_active_now | Active yoga detection at a date with strength scoring | **CRITICAL** |
| get_planet_avastha | Planet avastha states (Lajjita, Garvita, etc.) | **CRITICAL** |
| get_shadbala_full | Full 6-source shadbala roll-up with rank | **CRITICAL** |
| query_jaimini_chara_dasha | Jaimini 120-year Chara Dasha engine (full lineage) | **CRITICAL** |
| query_planetary_period_predictions | Classical MD/AD period predictions curator | **CRITICAL** |
| query_dasamsha_career | D10 career sector analysis with dignity scoring | HIGH |
| query_shashtiamsha | D60 karmic signature and kopa scoring | HIGH |
| query_eclipse_transits | Eclipse transits over natal with exact degrees | HIGH |
| query_planet_war | Graha Yuddha engine — combust/war detection | HIGH |
| query_drekkana_drishti | D3 aspect analysis and drishti resolution | MEDIUM |
| query_remedies_prescribed | Remedies prescribed archive query | MEDIUM |

Additional MCP-only support tools (lower priority for parity):
- `tara_balam_for_native`, `chandra_balam_for_native` — muhurta support
- `interpret_current_dasha`, `career_timing_audit`, `auspicious_period_finder` — composition recipes (intentionally MCP-only; not suitable for portal planner)
- `chart_summary`, `holistic_bundle`, `multi_school_bundle` — MCP composition bundles
- `read_asset`, `list_assets`, `list_canonical_artifact_versions` — meta/governance
- `get_trace`, `list_recent_queries` — observability (intentionally MCP-only)
- `log_prediction`, `record_outcome`, `flag_disagreement` — write tools (intentionally MCP-only)

**Count: 12 Class B engines are critical gaps in portal**

---

### §2.4 — CAPABILITY_MANIFEST governance gaps

CAPABILITY_MANIFEST.json currently has **169 entries, but only 17 are tool entries** — and most of those 17 have `status: null` and `path: null`. No MCP tool has any manifest entry.

Specific defects:
- 36 portal RETRIEVAL_TOOLS → 15 ungoverned (no entry at all), 7 have entries with missing status/path
- 41 MCP tools → 0 have any manifest entry
- 4 duplicate/stale entries for classical text search (RETRIEVAL_TOOL_classical_text_search, CLASSICAL_TEXT_SEARCH_TOOL, TOOL_27..., M9D_TOOL_27...)
- CAPABILITY_MANIFEST's `preferred_for[]` tags unused — no routing guidance baked in
- `catalog.ts` in `platform-mcp/src/tools/` has only 23 entries — does NOT include the 18 TR tools

---

---

## §2.5 — Quality Delta Matrix: Shared Tools

The Tooling Remediation (bace7b45) enhanced tools exclusively in `platform-mcp/src/tools/`. The portal's `platform/src/lib/retrieve/` counterparts were not touched. This creates a quality asymmetry on **every shared tool**. Separately, the portal has richer implementations for certain tools that were never carried into the MCP wrappers.

**Architectural clarity**: The data asset layer (Postgres tables) is **universally shared** — both channels read from the same `chart_facts`, `msr_signals`, `panchanga_daily`, `ephemeris_daily`, `rag_chunks`, etc. The quality delta is entirely at the **tool implementation level** (TypeScript wrappers), not the data layer. This means backports are TypeScript-only changes, not DB migrations.

---

### MCP is ahead — portal running degraded version

| Tool (portal name → MCP name) | Feature gap in portal | TR session that enhanced MCP |
|---|---|---|
| `query_dasha_periods` | **Missing PD/SD depth levels.** MCP added `level` param: "maha"\|"antar"\|"pratyantar"\|"sookshma"; computes Pratyantar and Sookshma Dasha sub_periods from Vimshottari ratios. Portal returns MD+AD only. | TR-P7-S1 |
| `query_ephemeris` | **Missing 3 enhancements.** MCP added: (1) structured `date_range: {from, to}` object; (2) `sample_step` param ("1d"\|"7d"\|"30d") for token-budget control on wide ranges; (3) `return_changes_only` boolean for change-detection queries; (4) 1825-day span guard with clean error. Portal uses flat `start_date`/`end_date` only. | TR-P1-S2 |
| `chart_facts_query` → `query_chart_facts` | **Missing introspection features.** MCP added `include_empty_counts` param and `populated_count` annotation on every returned category bucket (shows how many chart_facts rows exist per category). Portal has same 27 column categories but returns no coverage metadata. | TR-P3-S2 |
| `query_transit_event` | **Schema quality gap.** MCP uses Zod with `.enum([...]).describe()` for event_type; adds `target`/`target_sign` aliases; cleaner validation with descriptive error messages. Portal uses TypeScript interface — same logic, weaker input validation. | TR-P1-S1 |

---

### Portal is ahead — MCP running degraded version

| Tool (portal name → MCP name) | Feature gap in MCP | Severity |
|---|---|---|
| `lel_query` (portal 230 lines → MCP 90 lines) | **chart_state missing.** Portal's lel_query exposes the Swiss Ephemeris `chart_state` snapshot for every life event (the full planetary state at event time — the M4 ground-truth spine). MCP wrapper omits this field entirely. Also: portal supports significance enum ("major"\|"moderate"\|"minor") filter; MCP only supports float `min_significance`. | HIGH |
| `query_varshaphala` → `query_varshphal` | **Year range missing.** Portal supports `year`, `year_start`, `year_end` (range queries — e.g. "show me annual charts 2020–2026"). MCP wrapper accepts only a single `year` integer. Multi-year Varshaphala analysis is blocked via MCP. | HIGH |
| `msr_sql` → `query_signals` | **LL.1 calibration missing in MCP.** Portal's msr_sql applies Learning Layer calibrated confidence floors per domain (finance/wealth: 0.35 floor vs default 0.55); uses `confidence × significance` DESC ordering with LL.1 weights. MCP's query_signals returns raw un-calibrated signal rows. Conversely, MCP has `dasha_lord`, `valence`, `temporal_activation` filters that portal's msr_sql lacks. | HIGH (bidirectional) |

---

### Approximately at parity (no backport needed)

| Tool pair | Status |
|---|---|
| `query_panchanga` ↔ `query_panchanga` | Both have all 5 enrichment JSONB columns (PR #110 touched both channels) ✓ |
| `chart_facts_query` columns ↔ `query_chart_facts` columns | Both have same 27-category column set including TR-P3-S1 backfill (deity_assignment, ishta_kashta, chandra_placement, avastha) ✓ |
| `divisional_query` ↔ `query_divisional_chart` | MCP is an explicit thin wrapper over the portal engine via the primitives API; same data surface ✓ |
| Python sidecar (jaimini.py, panchang_engine) | Both channels call the same Cloud Run python-sidecar. TR enhancements (jaimini.py 197-line update) benefit both channels once sidecar redeploys ✓ |

---

## §3 — Architecture Decision: Parity Strategy

Two approaches considered:

**Option A (Selected): Dual registry with cross-porting**
- Port the 12 Class B engines to `platform/src/lib/retrieve/` so portal gains them via RETRIEVAL_TOOLS
- Port the 21 priority portal tools to `platform-mcp/src/tools/` so MCP gains them
- CAPABILITY_MANIFEST becomes the authoritative registry for both surfaces
- `executeMCPTool` continues to call local RETRIEVAL_TOOLS (no latency/auth penalty)

**Option B (Deferred): Collapse to single MCP dispatch**
- Rewire `executeMCPTool` to call the remote `amjis-mcp` sidecar
- Portal Channel B automatically gains all MCP tools
- Portal Channel A (planner) still needs local RETRIEVAL_TOOLS for performance
- Risk: network latency per tool call in the agentic loop; auth complexity; sidecar outage couples portal
- Decision: Defer to M6 or later when sidecar SLA is proven stable

**Selected: Option A** — cross-port missing tools into each channel's native registry.

---

## §4 — Part 1: Universal Data Asset Parity Campaign

### Overview
- **30 sessions** across 5 phases
- **Executor**: Claude Code in Google Antigravity IDE (Conductor-driven)
- **Branch**: `feature/universal-parity`
- **Worktree**: `/Users/Dev/Vibe-Coding/Apps/MadhavParity`
- **Commit cadence**: commit every session; push at phase boundaries
- **PR**: single squash PR to main at campaign end

---

### Phase UDA-Q — Quality Backport: Best Version Everywhere (8 sessions)

**Goal**: Every shared tool runs its most enhanced version in both channels. No channel degrades a capability that another channel has already proven in production.

**Execution order**: UDA-Q runs **before** UDA-0 so that when tools are registered in the manifest they carry the definitive enhanced schema, not an intermediate degraded one.

---

**UDA-Q-S1: query_dasha_periods — PD/SD levels backport to portal** (1 session)

Portal target: `platform/src/lib/retrieve/query_dasha_periods.ts`

Changes to port from MCP (TR-P7-S1):
- Add `level: 'maha' | 'antar' | 'pratyantar' | 'sookshma'` param (default: `'antar'`)
- Implement `computePratyantar()` — for each AD, compute 9 PD sub_periods using Vimshottari ratios: `duration_PD(P) = duration_AD × (vimshottari_years[P] / 120)`
- Implement `computeSookshma()` — same ratio applied to PD duration
- Return enriched periods with `sub_periods[]` array when level is pratyantar or sookshma
- Update `retrieval_capability_spec.ts` entry for `query_dasha_periods` to document new `level` param
- Vitest: add 4 test cases (one per level) using native chart fixture

Gate: `query_dasha_periods({level: "pratyantar"})` returns non-empty `sub_periods[]` with 9 entries per AD.

---

**UDA-Q-S2: query_ephemeris — enhancements backport to portal** (1 session)

Portal target: `platform/src/lib/retrieve/query_ephemeris.ts`

Changes to port from MCP (TR-P1-S2):
- Add `sample_step: '1d' | '7d' | '30d'` param (default: `'1d'`); implement row-thinning in SQL (WHERE MOD(row_number, step_days) = 0 or equivalent)
- Add `return_changes_only: boolean` (default: false); filter rows where planet degree moved < 1° from previous
- Add `date_range: {from: string, to: string}` as an alias for `start_date`/`end_date` (preserve backwards-compat; accept both shapes)
- Add 1825-day span guard: reject ranges > 5 years with descriptive error pointing to sample_step
- Update `retrieval_capability_spec.ts` entry to document all 3 new params
- Vitest: add 3 test cases (sample_step="30d" returns ≤ 12 rows/year; return_changes_only returns fewer rows than full scan; span > 5 years returns error)

Gate: `query_ephemeris({date_range:{from:"2020-01-01",to:"2025-12-31"}, sample_step:"30d"})` returns ≤ 75 rows (5 years × 12 months ≈ 60–75 rows).

---

**UDA-Q-S3: chart_facts_query — introspection features backport to portal** (1 session)

Portal target: `platform/src/lib/retrieve/chart_facts_query.ts`

Changes to port from MCP (TR-P3-S2):
- Add `include_empty_counts: boolean` (default: false) param
- For every returned category bucket, annotate with `populated_count: number` (SQL COUNT for that category_id in chart_facts WHERE chart_id = $1)
- When `include_empty_counts=true`, include all 27 known categories including those with 0 rows (with populated_count: 0)
- When `include_empty_counts=false` (default), only return categories with ≥1 row, each annotated with populated_count
- Update `retrieval_capability_spec.ts` entry
- Vitest: add 2 tests (include_empty=false → only non-empty categories returned; include_empty=true → all 27 categories present)

Gate: `chart_facts_query({include_empty_counts: true})` returns exactly 27 category entries; each has `populated_count` field.

---

**UDA-Q-S4: lel_query — chart_state + significance enum backport to MCP** (1 session)

MCP target: `platform-mcp/src/tools/lel_query.ts`

Changes to port from portal retrieve:
- Expose `chart_state` field in the MCP tool's output (pass through from the underlying primitives call; chart_state is already in the life_events DB row)
- Add `significance_level: 'major' | 'moderate' | 'minor'` enum param as an alternative to `min_significance` float (can co-exist; enum translates to min_significance: major→0.8, moderate→0.5, minor→0.0)
- Update tool description to document chart_state output ("Returns the Swiss Ephemeris planetary state snapshot at the time of each event — full chart positions at event date")
- Update MCP catalog.ts description for lel_query
- Vitest: add 2 tests (chart_state field present and non-null for major events; significance_level="major" returns only high-significance events)

Gate: `lel_query({significance_level: "major"})` returns events with chart_state non-null; all returned events have significance ≥ 0.8.

---

**UDA-Q-S5: query_varshphal — year range backport to MCP** (1 session)

MCP target: `platform-mcp/src/tools/query_varshphal.ts`

Changes to port from portal retrieve:
- Add `year_start: number` and `year_end: number` params for range queries (alongside existing `year` for single-year)
- Validate: either `year` or `year_start`+`year_end` must be provided; not both
- Loop years start→end inclusive, collect results per year in an array
- Return `{years: [{year: number, solar_return_utc: string, lagna: string, planet_positions: {...}}]}`
- Cap range at 20 years to prevent token explosion (configurable in constants)
- Update tool description + catalog.ts
- Vitest: range query 2020–2026 returns 7 entries; each has planet_positions

Gate: `query_varshphal({year_start: 2024, year_end: 2026})` returns 3 annual chart objects.

---

**UDA-Q-S6: msr_sql ↔ query_signals — cross-pollinate filter richness** (2 sessions)

**Session A — Portal msr_sql gets MCP's filter dimensions** (portal target: `platform/src/lib/retrieve/msr_sql.ts`):
- Add `dasha_lord: string` param — filter to signals whose `dasha_activation` JSONB array contains the specified lord (SQL: `dasha_activation @> '["<lord>"]'::jsonb`)
- Add `valence: 'positive' | 'negative' | 'mixed'` param — filter by signal valence field
- Add `temporal_activation: string` param — filter by temporal activation label
- These are the 3 MCP filter dimensions absent from portal; existing domain/confidence/planets filters are preserved
- Update `retrieval_capability_spec.ts` entry and PLANNER_PROMPT tool schema for msr_sql

**Session B — MCP query_signals gets portal's LL.1 calibration** (MCP target: `platform-mcp/src/tools/query_signals.ts`):
- Import/port the domain-specific confidence floor logic from portal msr_sql: finance/wealth domains → 0.35 floor, default → 0.55
- Apply `confidence × significance` DESC ordering (currently MCP orders by significance DESC only)
- Add `calibrated: boolean` param (default: true) — when true, apply LL.1 domain floors before the user's `min_confidence` threshold
- Add inline comment documenting the LL.1 calibration source: `ll1_weights_promoted_v1_0.json`
- Vitest: calibrated=true query on "finance" domain returns signals at confidence ≥ 0.35; same query calibrated=false respects only explicit min_confidence

Gate: `query_signals({domain: "career", calibrated: true})` returns signals ordered by confidence×significance DESC; `query_signals({domain: "finance", calibrated: true})` returns signals down to confidence 0.35.

---

**UDA-Q-S7: Data asset audit — verify enriched columns surface end-to-end** (1 session)

**Goal**: Confirm that the enriched data (chart_facts backfill, panchanga 5 JSONB cols) actually reaches the API response in both channels — not just that it's in the DB.

For each enriched asset, run a live query via portal AND MCP and assert the enriched fields are present:

1. **chart_facts enriched columns** (deity_assignment, ishta_kashta, chandra_placement, avastha):
   - Portal: `chart_facts_query({categories: ["avastha"]})` → verify rows returned for native chart ID
   - MCP: `query_chart_facts({categories: ["avastha"]})` → verify rows returned
   - If either returns 0 rows, trigger DB investigation (the backfill from TR-P3-S1 may not have run for the native chart)

2. **panchanga_daily enriched JSONB** (special_yogas, choghadiya, hora, inauspicious, auspicious):
   - Portal: `query_panchanga({date: "2026-05-25", fields: ["special_yogas","choghadiya","hora"]})` → verify non-null JSONB fields
   - MCP: same params → verify same fields present
   - Cross-check: native birth date 1984-02-05 should have FORENSIC-grounded values per Phase 4C close audit

3. **lel_query chart_state post-backport** (after UDA-Q-S4):
   - Both portal and MCP: query for all "major" events; assert chart_state non-null for events dated after LEL v1.2 Swiss Ephemeris population

4. **msr_sql/query_signals 573-signal coverage**:
   - Portal: `msr_sql({domains: ["career","relationships","spiritual"], limit: 100})` → assert results.length = 100 (i.e., ≥100 signals exist)
   - MCP: `query_signals({domains: ["career","relationships","spiritual"], limit: 100})` → same assert

Capture all results at `eval-results/data_asset_audit_post_uda_q.json`.

Gate: all 4 data asset checks return non-empty, correctly structured responses from both portal and MCP channels.

---

### Phase UDA-0 — Manifest Governance (3 sessions)

**Goal**: CAPABILITY_MANIFEST.json becomes the authoritative, complete, zero-gap registry for every tool in every channel.

**UDA-0-S1: Manifest audit + dedup** (1 session)
- Remove 4 duplicate classical text tool entries; canonicalize as one entry per tool
- Populate `status`, `path`, `layer`, `schema_fields[]` for the 17 existing tool entries that have null values
- Add entries for all 36 portal RETRIEVAL_TOOLS with: `canonical_id: RETRIEVAL_TOOL_<name>`, `layer`, `status: CURRENT`, `path: platform/src/lib/retrieve/<file>.ts`, `schema_fields` (from tool's `schema` export)
- Run `drift_detector.py` to verify no new drift introduced

**UDA-0-S2: MCP tool manifest registration** (1 session)
- Add manifest entries for all 41 MCP tools with: `canonical_id: MCP_TOOL_<name>`, `layer`, `status: CURRENT`, `path: platform-mcp/src/tools/<file>.ts`
- Add `channel: mcp` tag to distinguish from portal retrieval tools
- Add `preferred_for[]` tags (e.g., `["temporal_query", "agentic_loop"]`)
- Update `entry_count` and regenerate `fingerprint`

**UDA-0-S3: catalog.ts + planner manifest sync** (1 session)
- Update `platform-mcp/src/tools/catalog.ts` to include all 41 MCP tools (currently has only 23; missing all 18 TR tools)
- Add `query_schema` (JSON Schema) to each catalog entry so MCP consumers can introspect tool input shapes
- Verify planner `<manifest>` injection in retrieval_capability_spec.ts covers all 36 portal tools with accurate `query_schema.properties`
- Gate: `manifest_query` tool returns 41 MCP entries + 36 portal entries with non-null status

---

### Phase UDA-1 — Port 12 Class B Engines to Portal (12 sessions)

**Goal**: All 12 MCP-only Class B engines are available to both portal modes (Classic planner + Claude-style agentic loop).

**Architecture note**: Each engine already has a full Python/SQL implementation in the `amjis-mcp` sidecar. Porting to portal means:
1. Create `platform/src/lib/retrieve/<engine>.ts` that calls the same SQL/Python sidecar
2. Export `tool: RetrievalTool` conforming to the retrieve types
3. Import + register in `RETRIEVAL_TOOLS` in `index.ts`
4. Add `RetrievalCapabilityEntry` to `retrieval_capability_spec.ts`
5. Update PLANNER_PROMPT_v2_0.md tool catalogue section

**Session breakdown** (pair high-value engines per session):

| Session | Engines | Priority |
|---|---|---|
| UDA-1-S1 | query_transits_over_natal + query_yogas_active_now | CRITICAL |
| UDA-1-S2 | get_planet_avastha + get_shadbala_full | CRITICAL |
| UDA-1-S3 | query_jaimini_chara_dasha | CRITICAL (standalone — full engine) |
| UDA-1-S4 | query_planetary_period_predictions | CRITICAL (standalone — classical curator) |
| UDA-1-S5 | query_dasamsha_career + query_shashtiamsha | HIGH |
| UDA-1-S6 | query_eclipse_transits + query_planet_war | HIGH |
| UDA-1-S7 | query_drekkana_drishti + query_remedies_prescribed | MEDIUM |
| UDA-1-S8 | tara_balam_for_native + chandra_balam_for_native | MEDIUM |
| UDA-1-S9 | retrieval_capability_spec.ts — add 12 new entries with full capability specs | — |
| UDA-1-S10 | PLANNER_PROMPT v2.3 — add 12 new tool entries to <manifest>, add R-rules for new engine patterns | — |
| UDA-1-S11 | Few-shot examples for new engines in PLANNER_PROMPT (predictive, shadbala, career, eclipse) | — |
| UDA-1-S12 | Integration test — run planner on 6 test queries that require new engines; verify plan coverage | — |

**Phase gate**: `npm run test:portal-planner` — all 12 new engines return non-empty results for the native's chart; planner plan for "shadbala summary" includes `get_shadbala_full`; plan for "active yogas today" includes `query_yogas_active_now`.

---

### Phase UDA-2 — Port Priority Portal Tools to MCP (10 sessions)

**Goal**: The 14 highest-value portal-only tools gain MCP wrappers, making them available to Cowork and Claude-style MCP clients.

**Priority tier (from §2.2)**:
- Tier 1 (CRITICAL for MCP Jyotish completeness): msr_sql, temporal, kp_query, query_ucn_walk, query_cdlm_lookup, query_jaimini_drishti
- Tier 2 (HIGH — L2.5 synthesis structure): pattern_register, resonance_register, cluster_atlas, contradiction_register, query_rm_walk
- Tier 3 (MEDIUM — domain-specific): timeline_query, query_signal_state, query_kp_ruling_planets

**Session breakdown**:

| Session | Tools | Notes |
|---|---|---|
| UDA-2-S1 | msr_sql MCP wrapper | Wraps portal's MSR SQL surface with MCP schema + tier filtering |
| UDA-2-S2 | temporal MCP wrapper | Unified dasha+transit+eclipse+retrograde time tool for MCP |
| UDA-2-S3 | kp_query + query_kp_ruling_planets MCP wrappers | KP system MCP exposure |
| UDA-2-S4 | pattern_register + resonance_register MCP wrappers | L2.5 signal structure |
| UDA-2-S5 | cluster_atlas + contradiction_register MCP wrappers | L2.5 meta-structure |
| UDA-2-S6 | query_ucn_walk + query_cdlm_lookup MCP wrappers | UCN/CDLM synthesis walks |
| UDA-2-S7 | query_rm_walk + query_jaimini_drishti MCP wrappers | RM matrix + Jaimini drishti |
| UDA-2-S8 | timeline_query + query_signal_state MCP wrappers | Temporal + state tools |
| UDA-2-S9 | Register all 14 new MCP tools in server.ts + catalog.ts | Wire into server; add descriptions + query_schema |
| UDA-2-S10 | Update manifest entries for all 14 new MCP tools; update holistic_bundle to consider new tools | Governance close |

**Phase gate**: `tool_health` MCP tool returns green for all 14 new tools; `msr_sql` via MCP returns ≥10 signals for planets=["Saturn"]; `temporal` via MCP returns dasha chain for native's chart.

---

### Phase UDA-3 — Interface Normalization (3 sessions)

**Goal**: Tools that exist in both channels have consistent naming, schema alignment, and documented asymmetries.

**UDA-3-S1: Name normalization audit**
- Canonical name pairs to resolve:
  - `chart_facts_query` (portal) ↔ `query_chart_facts` (MCP): standardize to `query_chart_facts` in portal too; update imports + RETRIEVAL_TOOLS key
  - `query_varshaphala` (portal) ↔ `query_varshphal` (MCP): standardize to `query_varshphal`; update portal
  - `classical_text_search_tool` (portal) ↔ `read_classical_text` (MCP): preserve asymmetry (search vs. read) but document it in manifest `known_asymmetries[]`
- Produce `INTERFACE_NORMALIZATION_REGISTER_v1_0.md` listing every canonical pair, the chosen canonical name, and any declared asymmetries

**UDA-3-S2: Schema parity audit for shared tools**
- For each of the 15 shared tools (§2.1), compare portal `schema.properties` vs MCP Zod schema
- Flag parameter differences (extra/missing params, type mismatches, default value conflicts)
- Fix divergences where the portal schema is missing a param the MCP has (or vice versa)

**UDA-3-S3: Planner prompt alignment**
- Ensure the PLANNER_PROMPT `<manifest>` tool entries use the normalized canonical names
- Add `R-NRM.1` rule: "When a tool exists in both channels with different names, the portal planner uses the canonical portal name; the MCP consumer uses the MCP name; both names are declared in CAPABILITY_MANIFEST `alias_names[]`"
- Update `.geminirules` MP.1 mirror

---

### Phase UDA-4 — V1.3 Audit Queue Items (2 sessions)

From `V1_3_AUDIT_QUEUE_v1_0.md` (carry-forward items from M5 Coverage Campaign):

**UDA-4-S1: MSR signal-grounding gap (CF.V13.5 scoped)**
- 419/573 MSR signals lack explicit FORENSIC/LEL citations (per V1_3 audit)
- Scope: add citation scaffolds for the 50 highest-significance ungrouped signals
- Not a full campaign — just the top-50 by significance score

**UDA-4-S2: bootstrap `build_manifests` auto-registration**
- Audit `platform/python-sidecar/scripts/bootstrap_panchanga.py` for the missing auto-registration gap
- Add `INSERT INTO build_manifests(...)` at bootstrap completion — prevents the manual rollback incident (2026-05-21)
- Generalize pattern to other bootstrap scripts if applicable

---

## §5 — Part 2: Rigorous Testing Campaign

### Overview
- **15 sessions** across 4 phases
- **Executor**: Claude Code in Google Antigravity IDE (or direct shell via Conductor)
- **Infrastructure**: Uses existing `eval-results/` directory + vitest + live sidecar
- **Branch**: `feature/universal-parity` (same branch as Part 1, testing phase)

---

### Phase TEST-0 — Test Infrastructure (2 sessions)

**TEST-0-S1: Per-channel smoke harness**
- Create `platform/tests/smoke/channel_parity/` directory
- `portal_classic_smoke.ts` — invokes the portal planner programmatically for each of the 36 (then 48) tools, verifies non-empty return
- `portal_agentic_smoke.ts` — invokes executeMCPTool directly for each tool, verifies non-empty return
- `mcp_channel_smoke.ts` — calls each MCP tool via the live sidecar at `AMJIS_MCP_URL` (env-var), verifies 200 + non-empty result
- Native chart constant (`NATIVE_CHART_ID = "362f9f17-95a5-490b-a5a7-027d3e0efda0"`) as the universal test fixture

**TEST-0-S2: Data coverage baseline**
- Run `data_coverage` MCP tool and `tool_health` MCP tool against production
- Capture baseline JSON at `eval-results/parity_baseline_pre_campaign.json`
- SQL queries: count rows per data surface (chart_facts, msr_signals, rag_chunks, panchanga_daily, life_events, school_convergence_index, ephemeris_daily)
- Establish min-row thresholds for each table as hard gates in the smoke harness

---

### Phase TEST-1 — Portal Tool Verification (4 sessions)

**TEST-1-S1: L1 + L1.5 tools (9 tools)**
Verify in both portal modes: `query_ephemeris`, `query_panchanga`, `query_transit_event`, `query_dasha_periods`, `query_varshaphala` / `query_varshphal`, `query_muhurat`, `query_kp_ruling_planets`, `chart_facts_query` / `query_chart_facts`, `lel_query`

For each: assert result.results.length > 0; assert key fields present; assert no ERROR prefix.

**TEST-1-S2: L2.5 synthesis tools (11 tools)**
`msr_sql`, `pattern_register`, `resonance_register`, `cluster_atlas`, `contradiction_register`, `temporal`, `cgm_graph_walk`, `query_signal_state`, `query_ucn_walk`, `query_cdlm_lookup`, `query_rm_walk`

**TEST-1-S3: Classical + multi-school tools (7 tools)**
`classical_text_search_tool`, `classical_attribution_lookup_tool`, `multi_school_signal_lookup_tool`, `convergence_score_lookup_tool`, `cross_school_lookup` (MCP), `vector_search`, `cross_varga_dignity_query`

**TEST-1-S4: New Class B engines (12 tools — post UDA-1)**
All 12 engines ported from MCP in Phase UDA-1: verify in Classic planner, agentic loop; verify planner plans include them for relevant test queries; verify results are non-empty and structurally correct.

---

### Phase TEST-2 — MCP Tool Verification (4 sessions)

**TEST-2-S1: Core data retrieval tools (10 tools)**
Via live `amjis-mcp` sidecar (MarsysJIS connector or direct curl): `query_chart_facts`, `query_signals`, `query_dasha_periods`, `query_ephemeris`, `query_panchanga`, `query_transit_event`, `lel_query`, `vector_search`, `get_cgm_subgraph`, `cross_school_lookup`

For each: HTTP 200; `result.content[0].text` parses as JSON; key fields present.

**TEST-2-S2: TR Class B engines (12 tools)**
`query_transits_over_natal`, `query_yogas_active_now`, `get_planet_avastha`, `get_shadbala_full`, `query_jaimini_chara_dasha`, `query_planetary_period_predictions`, `query_dasamsha_career`, `query_shashtiamsha`, `query_eclipse_transits`, `query_planet_war`, `query_drekkana_drishti`, `query_remedies_prescribed`

For each: invoke with native chart ID + representative params; assert structured results.

**TEST-2-S3: MCP composition + meta tools (10 tools)**
`chart_summary`, `holistic_bundle`, `multi_school_bundle`, `interpret_current_dasha`, `read_asset`, `list_assets`, `read_classical_text`, `list_canonical_artifact_versions`, `tool_health`, `data_coverage`

**TEST-2-S4: Newly ported portal→MCP tools (14 tools — post UDA-2)**
All 14 tools ported in Phase UDA-2: `msr_sql`, `temporal`, `kp_query`, etc. Verify via live sidecar.

---

### Phase TEST-3 — Cross-Channel Parity Validation (3 sessions)

**TEST-3-S1: Result equivalence for shared tools**
For the 15 shared tools (§2.1), run the same query on both portal and MCP. Compare:
- Result row count within ±10%
- Key field presence identical
- No structural schema differences
Document any legitimate asymmetries in `INTERFACE_NORMALIZATION_REGISTER_v1_0.md`

**TEST-3-S2: Planner coverage test**
Run 12 canonical test queries (covering temporal, predictive, remedial, multi-school, career, health, relationship, Jaimini, shadbala, yogas, eclipse, and muhurta domains) through the Classic planner. Verify:
- Each query's plan includes at least one of the newly-ported Class B engines where relevant
- No plan calls a tool that doesn't exist in RETRIEVAL_TOOLS
- Planner R-rules are enforced (R-CS.1 cross-school, R-TRI.1 triangulation, R-CS.2 chart summary)

**TEST-3-S3: Calibration Sankalpa read**
Run a full Sankalpa read (the calibration sequence from the pre-TR baseline) via:
1. Portal Classic mode — capture tool trace + response quality score
2. Portal Claude-style mode — capture tool trace + response quality score
3. MCP via MarsysJIS connector (Cowork) — capture tool trace + response quality score
Compare against `eval-results/tooling_audit_baseline_20260524.json`. Record improvement delta at `eval-results/parity_calibration_post_campaign.json`.

**Phase gate**: Calibration Sankalpa read shows improvement in: tools_invoked count (baseline vs post-parity), cross-school triangulation rate, B.11 compliance rate. Baseline pass rate was 8%; target ≥25% after parity campaign.

---

### Phase TEST-4 — Live Integration Seal (2 sessions)

**TEST-4-S1: Production smoke — all three channels**
After campaign branch merges to main and sidecar redeploys:
- Run `portal_classic_smoke.ts` against production (via service account auth)
- Run `portal_agentic_smoke.ts` against production
- Run `mcp_channel_smoke.ts` against production sidecar
- All three must pass 100% of registered tools
- Capture final tool inventory at `eval-results/parity_final_inventory.json`

**TEST-4-S2: CAPABILITY_MANIFEST governance close**
- Run `drift_detector.py` — must exit 0
- Run `schema_validator.py` — must exit 0
- Verify CAPABILITY_MANIFEST `entry_count` matches actual tool counts
- Update CAPABILITY_MANIFEST `generated_at` fingerprint
- Append to `SESSION_LOG.md`; update `CURRENT_STATE_v1_0.md`

---

## §6 — Execution Architecture

### Conductor setup
```
Branch:   feature/universal-parity
Worktree: /Users/Dev/Vibe-Coding/Apps/MadhavParity
Queue:    00_ARCHITECTURE/CONDUCTOR/universal-parity/session_queue.yaml
Log:      00_ARCHITECTURE/CONDUCTOR/universal-parity/CONDUCTOR_LOG.md
```

### Session naming convention
- `UDA-Q-S1` through `UDA-Q-S8` (Quality backport — best version everywhere)
- `UDA-0-S1` through `UDA-0-S3` (Manifest governance)
- `UDA-1-S1` through `UDA-1-S12` (Portal gets Class B engines)
- `UDA-2-S1` through `UDA-2-S10` (MCP gets portal tools)
- `UDA-3-S1` through `UDA-3-S3` (Interface normalization)
- `UDA-4-S1` through `UDA-4-S2` (V1.3 queue items)
- `TEST-0-S1` through `TEST-0-S2` (Test infra)
- `TEST-1-S1` through `TEST-1-S4` (Portal verification)
- `TEST-2-S1` through `TEST-2-S4` (MCP verification)
- `TEST-3-S1` through `TEST-3-S3` (Cross-channel parity)
- `TEST-4-S1` through `TEST-4-S2` (Integration seal)

### Total sessions: 53
- Part 1 (Parity): 38 sessions
  - UDA-Q × 8 (quality backport — **new in v1.1**)
  - UDA-0 × 3 (manifest governance)
  - UDA-1 × 12 (portal gets Class B engines)
  - UDA-2 × 10 (MCP gets portal tools)
  - UDA-3 × 3 (interface normalization)
  - UDA-4 × 2 (V1.3 queue items)
- Part 2 (Testing): 15 sessions (TEST-0 × 2 + TEST-1 × 4 + TEST-2 × 4 + TEST-3 × 3 + TEST-4 × 2)

### Conductor context budget
- 20 sub-agents per orchestrator chat → **3 conductor runs** needed for 53 sessions
- Conductor Run 1: UDA-Q + UDA-0 + UDA-1 partial (8+3+9 = 20 sessions)
- Conductor Run 2: UDA-1 finish + UDA-2 + UDA-3 + UDA-4 (3+10+3+2+2 = 20 sessions) [Note: add remaining UDA-1 sessions S10-S12 here]
- Conductor Run 3: TEST-0 through TEST-4 (2+4+4+3+2 = 15 sessions) — requires sidecar redeploy first

### Commit/push cadence
- Commit: after every session
- Push to remote: at each phase boundary (end of UDA-0, UDA-1, UDA-2, UDA-3, UDA-4, TEST phases)
- PR: single squash PR to main at TEST-4-S2 close

---

## §7 — Open questions before execution (require native decision)

1. **Name normalization**: For shared tools with mismatched names (`chart_facts_query` vs `query_chart_facts`, `query_varshaphala` vs `query_varshphal`), do we rename in the portal to match MCP, or the reverse? Recommendation: standardize on MCP names (`query_` prefix convention) in the portal.

2. **temporal decomposition**: The portal's `temporal` tool is a unified mega-tool covering dasha, transit, eclipse, and retrograde. Should it be split into focused primitives when ported to MCP, or kept as a single bundle? Recommendation: keep as-is for portal; add a `query_temporal_bundle` MCP wrapper that unifies the 4 MCP time tools (query_dasha_periods + query_transit_event + query_eclipse_transits + query_ephemeris).

3. **Composition recipes in portal**: The MCP's `interpret_current_dasha`, `career_timing_audit`, `auspicious_period_finder` are LLM-orchestrated compositions (they call other MCP tools internally). Should the portal planner be allowed to plan these, or are they reserved for the MCP agentic channel? Recommendation: keep as MCP-only; they require multi-step tool orchestration that the portal planner doesn't support.

4. **Write tools in portal**: `log_prediction`, `record_outcome`, `flag_disagreement` are MCP-only write tools. Should they be available to the portal Claude-style agentic loop so the model can log predictions during portal sessions? Recommendation: yes — wire as special-cased tools in `executeMCPTool` that call the MCP sidecar for write operations. This is a separate micro-workstream (UDA-5, ~2 sessions).

---

## §8 — Dependencies and prerequisites

- [x] Tooling Remediation v1.0 COMPLETE (bace7b45 on main) — all 12 Class B engines exist in MCP; quality enhancements documented in §2.5
- [ ] `amjis-mcp` sidecar redeploy pending — must complete before UDA-Q-S4/S5 (MCP tool changes) and all TEST-2 phases
- [ ] Native decisions on §7 open questions — block start of UDA-1-S10 (PLANNER_PROMPT naming) and UDA-3-S1 (normalization)
- [ ] `feature/universal-parity` branch creation + worktree setup (Setup Prompt, analogous to tooling-remediation setup)
- [ ] UDA-Q-S6-B (MCP query_signals LL.1 calibration) depends on UDA-Q-S6-A (portal msr_sql filter expansion) completing first — share the Vimshottari/calibration logic extraction
- [ ] UDA-Q-S7 (data asset audit) should run AFTER all other UDA-Q sessions complete — it validates the backports end-to-end

---

*End of UNIVERSAL_PARITY_PLAN_v1_0.md — Cowork-authored 2026-05-25*
