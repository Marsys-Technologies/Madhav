---
canonical_id: RETRIEVAL_D7_GAP_REPORT
version: 1.0
status: CURRENT
created: 2026-06-28
author: Claude Code (GAP ANALYSIS + PORT agent — D7 Chat-Channel Migration §2)
parent: CLAUDECODE_BRIEF_RETRIEVAL_D7_CHAT_MIGRATION_v1_0 §2
scope: Gap analysis and port of lib/retrieve capabilities lacking registry equivalents.
       Read-only on lib/retrieve; adds capabilities to register_d7_channel.ts only.
chart_agnostic_gate: PASS (17 capabilities, 0 violations)
test: src/lib/retrieval/registry/layers/__tests__/register_d7_channel.gate.test.ts (8/8)
---

# RETRIEVAL D7 GAP REPORT v1.0

Gap analysis for §2 of the D7 chat-channel migration: for each piece of `lib/retrieve`
logic the chat path needs, verify a registry equivalent exists; add one where it does not.

---

## §1 — Methodology

**Source of truth for "what the chat path needs":**
- `src/app/api/chat/consult/route.ts` — B.11 floor injection + `getTool(toolName)` dispatch loop
- `src/lib/pipelines/shared/b11_floor_inject.ts` — floor injection pipeline
- `src/lib/retrieve/index.ts` `RETRIEVAL_TOOLS` array — tools the `getTool()` lookup resolves
- `src/lib/retrieve/remedy_tools.ts` `REMEDY_TOOLS` — 7 remedy sub-tools exported into RETRIEVAL_TOOLS
- `src/lib/retrieve/sutravali_tools.ts` `SUTRAVALI_RETRIEVAL_TOOLS` — 4 sutravali tools

**Registry checked against:**
- `src/lib/retrieval/registry/layers/L0_brahmagyan/` — 15 capabilities
- `src/lib/retrieval/registry/layers/L1_ganita/` — 19 capabilities
- `src/lib/retrieval/registry/layers/L2_bodha/` — 7 capabilities
- `src/lib/retrieval/registry/layers/register_d7_channel.ts` — prior D7 wave (5 gap-fills already present)

---

## §2 — Coverage matrix (pre-migration state)

| lib/retrieve tool name | Registry URI | Status |
|---|---|---|
| `msr_sql` | `marsys://tool/L2/query_signals` | **COVERED** — D5 wave, full filter parity |
| `chart_facts_query` | (none) | **GAP** — B.11 floor-injected; type stub in lib/retrieve; no registry cap |
| `read_classical_text` | `marsys://tool/L0/query_classical_texts` | **COVERED** — keyword + source filter path |
| `search_classical_texts` | `marsys://tool/L0/query_classical_texts` | **COVERED** — same cap, alias behavior |
| `read_chapter` | (none) | **GAP** — chapter fetch distinct from keyword search |
| `list_classical_texts` | (none) | **GAP** — text roster; no registry cap |
| `find_verses_about` | (none) | **GAP** — embedding-similarity path; distinct from ILIKE search |
| `query_rules` | `marsys://tool/L0/query_sutravali_rules` | **COVERED** — prior D7 wave |
| `query_rules_for_planet` | `marsys://tool/L0/query_sutravali_rules_for_planet` | **COVERED** — prior D7 wave |
| `read_rule` | `marsys://tool/L0/read_sutravali_rule` | **COVERED** — prior D7 wave |
| `list_rules_by_text` | `marsys://tool/L0/list_sutravali_rules_by_text` | **COVERED** — prior D7 wave |
| `classical_attribution_lookup` | `marsys://tool/L2/classical_attribution_lookup` | **COVERED** — prior D7 wave |
| `compute_natal_positions` | `marsys://tool/L1/get_positions` | **COVERED** — L1 wave |
| `query_dasha_periods` | `marsys://tool/L1/get_dashas` | **COVERED** — L1 wave |
| `query_special_lagnas` | `marsys://tool/L1/get_sensitive_points` | **COVERED** — L1 wave |
| `query_remedies` | `marsys://tool/L0/query_remedy_corpus` | **COVERED** — generic graha+category filter |
| `query_remedies_for_chart` | (none) | **GAP** — per-chart affliction lookup; not in registry |
| `list_remedies_by_category` | (none) | **GAP** — category-scoped list; not in registry |
| `read_remedy` | (none) | **GAP** — single remedy by UUID; not in registry |
| `query_tantric_remedies` | (none) | **GAP** — tantric sub-corpus + deity filter; not in registry |
| `query_remedies_by_planet` | (none) | **GAP** — all-category planet filter; not in registry |
| `query_mantras` | (none) | **GAP** — mantra sub-corpus; not in registry |
| `classical_disclosure_filter` | RETIRED (file self-marked) | **NO-OP** — tier gating moved to serve-time; no registry cap needed |
| `normalizeInputSchema` helper | Move file location only | **NO-OP** — pure utility, not a retrieval dispatch |
| `buildChatToolsFromNames` helper | `@/lib/contract/registry` already | **NO-OP** — delegates to contract registry; no registry cap needed |

**Non-RETRIEVAL_TOOLS planner strings dispatched through `getTool()` — resolve to undefined, skipped:**
- `vector_search`, `pattern_register`, `cgm_graph_walk`, `resonance_register`, `cluster_atlas`,
  `contradiction_register` — these are contract tool names injected by the planner/B.11 into
  `toolsAuthorized`; `getTool()` returns `undefined` for them today. They are NOT in RETRIEVAL_TOOLS
  and are out of scope for this §2 port (they require separate planner-side migration in §3).

---

## §3 — Real gaps found: 11

| # | Gap name | Old lib/retrieve code | Scope | New registry URI |
|---|---|---|---|---|
| G1 | `chart_facts_query` | `chart_facts_query.ts` (TYPE STUB) + B.11 floor inject | per_chart | `marsys://tool/L1/chart_facts_query` |
| G2 | `query_remedies_for_chart` | `remedy_tools.ts::queryRemediesForChart` | per_chart | `marsys://tool/L0/query_remedies_for_chart` |
| G3 | `list_remedies_by_category` | `remedy_tools.ts::listRemediesByCategory` | global | `marsys://tool/L0/list_remedies_by_category` |
| G4 | `read_remedy` | `remedy_tools.ts::readRemedy` | global | `marsys://tool/L0/read_remedy` |
| G5 | `query_tantric_remedies` | `remedy_tools.ts::queryTantricRemedies` | global | `marsys://tool/L0/query_tantric_remedies` |
| G6 | `query_remedies_by_planet` | `remedy_tools.ts::queryRemediesByPlanet` | global | `marsys://tool/L0/query_remedies_by_planet` |
| G7 | `query_mantras` | `remedy_tools.ts::queryMantras` | global | `marsys://tool/L0/query_mantras` |
| G8 | `read_chapter` | `index.ts CLASSICAL_TOOLS::read_chapter` | global | `marsys://tool/L0/read_chapter` |
| G9 | `list_classical_texts` | `index.ts CLASSICAL_TOOLS::list_classical_texts` | global | `marsys://tool/L0/list_classical_texts` |
| G10 | `find_verses_about` | `index.ts CLASSICAL_TOOLS::find_verses_about` | global | `marsys://tool/L0/find_verses_about` |
| G11 | (previously covered by prior D7 wave) | sutravali × 4 + classical_attribution | — | already in D7_CAPABILITY_URIS |

Non-gaps confirmed (no action needed):
- `classical_disclosure_filter.ts` — RETIRED in-file; tier stripped at serve-time; no cap needed
- `normalizeInputSchema`, `buildChatToolsFromNames` — utility helpers, not retrieval dispatch calls

---

## §4 — Ported capabilities (all added to register_d7_channel.ts)

### G1 — `marsys://tool/L1/chart_facts_query`

- **Old code:** `src/lib/retrieve/chart_facts_query.ts` (TYPE STUB — implementation removed in legacy-teardown)
  plus B.11 floor injection in route.ts line 511 and `b11_floor_inject.ts` line 74.
  Contract alias: `is_alias: true, alias_of: 'query_chart_facts'` per `tool_metadata.ts` line 348.
- **D1 contract:** scope=`per_chart`, chart_id required, emits_references=true (returns fact_id refs),
  archetype=`flat_fact`, traversal_level=`L-SIGNAL`, tool_role=`umbrella`.
- **Tier stripping:** no `audience_tier` parameter; universal access.
- **Handler:** delegates to Python sidecar `/api/ganita/chart_facts/query` (POST).
- **Gate:** PASS (Rule 1 — chart_id in required_inputs; Rule 7 — all D1 fields present).

### G2 — `marsys://tool/L0/query_remedies_for_chart`

- **Old code:** `src/lib/retrieve/remedy_tools.ts::queryRemediesForChart` — matches affliction ILIKE
  against both `planet` and `domain` columns, returns top_k by confidence.
- **D1 contract:** scope=`per_chart` (chart_id anchors the query context), chart_id required,
  emits_references=false, archetype=`flat_fact`, traversal_level=`L-DOMAIN`, tool_role=`drill`.
- **Tier stripping:** `audience_tier` removed from handler; no gating.
- **Handler:** direct pg Pool query against `brahma_remedy_corpus`.
- **Gate:** PASS.

### G3 — `marsys://tool/L0/list_remedies_by_category`

- **Old code:** `src/lib/retrieve/remedy_tools.ts::listRemediesByCategory`.
- **D1 contract:** scope=`global`, category required (enum), emits_references=false.
- **Gate:** PASS.

### G4 — `marsys://tool/L0/read_remedy`

- **Old code:** `src/lib/retrieve/remedy_tools.ts::readRemedy` — single remedy by remedy_id.
- **D1 contract:** scope=`global`, remedy_id required, emits_references=false, tool_role=`leaf`.
- **Gate:** PASS.

### G5 — `marsys://tool/L0/query_tantric_remedies`

- **Old code:** `src/lib/retrieve/remedy_tools.ts::queryTantricRemedies` — category=tantric filter
  with optional deity ILIKE and planet filters.
- **D1 contract:** scope=`global`, no required_inputs (all optional), emits_references=false.
- **Gate:** PASS.

### G6 — `marsys://tool/L0/query_remedies_by_planet`

- **Old code:** `src/lib/retrieve/remedy_tools.ts::queryRemediesByPlanet`.
- **D1 contract:** scope=`global`, planet required, emits_references=false.
- **Gate:** PASS.

### G7 — `marsys://tool/L0/query_mantras`

- **Old code:** `src/lib/retrieve/remedy_tools.ts::queryMantras` — category=mantras filter.
- **D1 contract:** scope=`global`, planet optional, emits_references=false.
- **Gate:** PASS.

### G8 — `marsys://tool/L0/read_chapter`

- **Old code:** `src/lib/retrieve/index.ts CLASSICAL_TOOLS::read_chapter` — delegates to
  `@/lib/tools/classical_text_tools::read_chapter`.
- **D1 contract:** scope=`global`, text_id + chapter required, archetype=`prose_citation`,
  tool_role=`leaf`, grounds_to={l0_citation_ids:true}.
- **Gate:** PASS.

### G9 — `marsys://tool/L0/list_classical_texts`

- **Old code:** `src/lib/retrieve/index.ts CLASSICAL_TOOLS::list_classical_texts` — delegates to
  `@/lib/tools/classical_text_tools::list_classical_texts`.
- **D1 contract:** scope=`global`, no required_inputs, archetype=`flat_fact`, tool_role=`umbrella`.
- **Gate:** PASS.

### G10 — `marsys://tool/L0/find_verses_about`

- **Old code:** `src/lib/retrieve/index.ts CLASSICAL_TOOLS::find_verses_about` — embedding-similarity
  verse discovery (distinct from keyword ILIKE in `query_classical_texts`).
- **D1 contract:** scope=`global`, topic required, archetype=`prose_citation`,
  tool_role=`hybrid_retrieval`, grounds_to={l0_citation_ids:true}.
- **Tier stripping:** no `audience_tier`; universal access.
- **Gate:** PASS.

---

## §5 — Chart-agnostic gate result

```
D7 capabilities: 17 / 17 expected
[chart_agnostic_gate] PASS — no violations found
```

All 17 D7 capabilities (2 wiring + 15 gap-fill) pass all 7 gate rules:
- Rule 1 (per_chart → chart_id required): 3 per_chart caps all include chart_id
- Rule 2 (no native chart_id in description/name/URI): PASS
- Rule 3 (no native identifiers in LLM-visible description): PASS
- Rule 4 (no default on chart_id input field): PASS
- Rule 5 (no native id in chart_id field description): PASS
- Rule 6 (global scope must not require chart_id): PASS
- Rule 7 (all D1 contract fields present): PASS

---

## §6 — Test added

File: `src/lib/retrieval/registry/layers/__tests__/register_d7_channel.gate.test.ts`

8 tests — all PASS:
1. Registers all 17 D7 URIs
2. All D7 capabilities pass the chart-agnostic gate (7 rules)
3. per_chart caps require chart_id in required_inputs
4. global caps do not require chart_id
5. No native identifiers in any D7 description or URI
6. Wave C — chart_facts_query is per_chart, emits_references, L1
7. Wave D — query_remedies_for_chart is per_chart
8. Wave E — find_verses_about is global, prose_citation archetype

---

## §7 — What remains for §3 (caller repoint)

This report covers §2 only (gap analysis + port). The following are deferred to §3:

1. Caller repoint: `consult/route.ts`, `mcp_tool_executor.ts`, `run_adapter_dispatch.ts` still import
   from `lib/retrieve` and use `getTool()`. Each needs repointing to `getCapability(uri)` with
   parity testing on ≥2 charts.
2. Type migration: `ToolBundle` → `ToolResult` in 5 type-only callers (#6-#10 per caller map).
3. `primitives_registry` fold: 4 callers need MCP whitelist migrated to registry URI checks.
4. Planner-only tool names (`vector_search`, `pattern_register`, `cgm_graph_walk`) currently resolve
   to `undefined` in `getTool()` — these need registry caps + planner-side name→URI mapping.
5. Reverse-citation retirement gate: run grep for zero citations before deleting `lib/retrieve/`.

*End of RETRIEVAL_D7_GAP_REPORT v1.0.*
*Generated 2026-06-28 by GAP ANALYSIS + PORT agent — register_d7_channel.ts modified; no other files changed.*
