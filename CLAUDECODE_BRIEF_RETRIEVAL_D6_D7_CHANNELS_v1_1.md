---
canonical_id: CLAUDECODE_BRIEF_RETRIEVAL_D6_D7_CHANNELS
version: 1.1
status: RESOLVED — all parameterized markers filled; ready for D6/D7 implementation
created: 2026-06-27
updated: 2026-06-28
author: Cowork (planning) — detail-pass by Claude Code (DETAIL-PASS agent, 2026-06-28)
classification: CLAUDECODE_BRIEF — D6 synergy + D7 channel integration (MCP + chat over MARO)
session_type: implementation — whole-corpus synergy + the two-channel surface
parent_design: RETRIEVAL_SYSTEM_DESIGN_APPROACH_v1_4 (waves D6, D7; §A channel asymmetry)
depends_on: D1–D5 + D-PROFILES
detail_pass_sources:
  - CLAUDECODE_BRIEF_RETRIEVAL_D5_FANOUT_v1_1.md (§1.0–§1.4 — complete tool roster)
  - CLAUDECODE_BRIEF_RETRIEVAL_DPROFILES_MARO_v1_1.md (§0.1–§0.2 — MARO core + declaration mechanisms)
  - platform-mcp/src/server.ts (current MCP wiring — 13 tools, Streamable HTTP, no SSE)
  - platform/src/lib/retrieval/registry/ (registry API, types, parity_check, chart_agnostic_gate)
  - platform/src/app/api/chat/consult/route.ts (chat engine — getTool() from lib/retrieve/index.ts)
  - platform/src/lib/retrieve/index.ts (old toolset — RETRIEVAL_TOOLS array, msr_sql-family)
  - 00_ARCHITECTURE/RETRIEVAL_GROUNDTRUTH_CODE_VALIDATION_v1_0.md §H (contamination findings)
prereq_reading:
  - RETRIEVAL_SYSTEM_DESIGN_APPROACH_v1_0.md (waves D6/D7; §A.3 channel asymmetry; §C.1.1 build-on-new-registry)
  - RETRIEVAL_GROUNDTRUTH_CODE_VALIDATION_v1_0.md (§H native contamination in old MCP tools — remediation list)
  - RETRIEVAL_GROUNDTRUTH_LLM_PROVIDER_SPEC_v1_0.md (B.i MCP-channel obligations)
hard_constraints:
  - single source of query logic (the registry) → MCP↔chat drift impossible by construction
  - old platform-mcp/src/tools/ remediation ONLY under the reverse-citation gate (destructive safety)
  - chart-agnostic (#14) enforced on every channel surface; declared→profiled / undeclared→universal MCP
acceptance_criteria: see §4
changelog:
  - v1.0 (2026-06-27): Parameterized brief — structure set; specifics pending D5 roster + MARO core.
  - v1.1 (2026-06-28): Detail-pass — all [resolved from …] markers filled with concrete
    implementation details from D5 v1.1, D-PROFILES v1.1, server.ts, registry/, route.ts, retrieve/,
    and §H contamination findings. Sections §1–§3 expanded with actionable specifics.
---

# CLAUDE CODE BRIEF — D6 SYNERGY + D7 CHANNELS (v1.1 — RESOLVED)

> D6 designs the whole-corpus synergy (the system being more than its assets); D7 wires both channels
> over the shared MARO + registry so they cannot drift, and remediates the contaminated old MCP tools.
> RESOLVED: all parameterized placeholders filled from upstream sources.

---

## §0 — Resolved inputs (was: parameterized)

### §0.1 — [resolved from D5] — Final tool roster

Source: `CLAUDECODE_BRIEF_RETRIEVAL_D5_FANOUT_v1_1.md §1.0–§1.4`.

The full D5 tool roster collapses 81 assets into ≤35 capabilities, organized as follows.

**Already implemented (DO NOT re-implement):**

| Layer | Count | Capability names |
|---|---|---|
| L0 Brahmagyan | 15 | `resolve_entity`, `list_entities`, `query_classical_texts`, `query_yoga_catalog`, `query_dosha_catalog`, `query_remedy_corpus`, `query_planet_transit`, `query_planet_position`, `query_aspects_at_time`, `query_retrograde_periods`, `ephemeris_cache_year`, `ephemeris_cache_native_lifetime`, `intent_classify`, `asset_registry_all`, `asset_registry_l0` |
| L1 Gaṇita | 19 | `get_positions`, `get_strength`, `get_ashtakavarga`, `get_bhava_bala`, `get_aspects`, `get_yoga_dosha`, `get_argala`, `get_dispositors`, `get_sade_sati`, `get_panchanga`, `get_sensitive_points`, `get_karakas`, `get_dignity`, `get_avasthas`, `get_tajik`, `get_tara_chandra_bala`, `get_eclipse_flags`, `get_dashas`, `get_divisionals` |
| L2 Bodha | 1 | `query_ucd` (umbrella; drill_children declared but not yet built) |
| L5 Mīmāṃsā | 2 | `query_insights`, `query_calibration` (STUBBED-PENDING-DATA) |

**D5-new tools to be built (gaps for D5 wave; D6/D7 compose over them):**

| Layer | Tools to build | Notes |
|---|---|---|
| L2 Bodha | `query_domain_reading`, `query_signals`, `traverse_chart_graph`, `query_contradictions`, `query_remedies`, `query_quality_scorecard` | 5 drill/leaf/graph tools + 1 quality; all per_chart |
| L3 Kāla | `query_temporal_activation` (umbrella), `query_convergence_windows`, `query_life_arc`, `query_projections`, `query_obstruction_periods` (STUBBED), `query_temporal_view` (STUBBED), `call_transit_search`, `call_ephemeris_at_t`, `call_dasha_eligibility`, `call_muhurta_score`, `call_priority_ranking` | 6 data + 5 service wrappers |
| L4 Phala | `query_predictive_anchors` (umbrella), `query_domain_result`, `query_auspicious_windows`, `query_spillover_cascades`, `query_falsifiers`, `query_anomaly_flags`, `query_remedy_program`, `query_cleansed_anchors`, `query_rectification` | 9 tools |
| L5 Mīmāṃsā | `query_predictions`, `query_signal_families`, `query_manifestation_grammar` | 3 additional |

**Roster facts for D6/D7 composition:**
- Registered entry points for Whole-Chart-Read: `query_ucd` (L-ORIENT umbrella, bo_samvada/vw_chart_digest); `intent_classify` (L0 routing); `asset_registry_all` (L-OVERVIEW)
- Graph traversal: `traverse_chart_graph` (bo_bimba/bo_karanajala, CGM, 140 nodes / 360 edges — relationship_basis 100% NULL, do not filter by it)
- Cross-domain / contradiction: `query_contradictions` (bo_sangati/bo_anveshana; bodha_contradictions currently 0 rows — graceful-empty)
- Temporal / convergence: `query_temporal_activation` → `query_convergence_windows` → `query_life_arc` chain (L3)
- Calibration spine: `query_falsifiers`, `query_anomaly_flags`, `query_quality_scorecard`, `query_calibration` (L4–L5)
- Total tool count at D6/D7 surface: ~35 tools (well within MCP 10–15 consolidated target when workflow-shaped)

**Critical data notes for D6 composition:**
- `signature_tier`: 100% 'background' on 66,738 signals — all ranking MUST use `computed_salience` only
- `lel_origin=true`: 0 rows currently — LEL toggle safe to wire; returns empty until LEL rebuild
- DEFECT-001: 91.5% of `constituent_facts_array` refs are orphan — any F3 path to L1 provenance MUST handle empty joins gracefully
- `vw_chart_digest` (bo_samvada): 5 rows; top_convergence_domains = career(12,334 signals), relationship(7,357), character(6,580), spirituality(3,527), wealth(2,512), health(903)

---

### §0.2 — [resolved from D-PROFILES] — MARO core + behavioral profiles

Source: `CLAUDECODE_BRIEF_RETRIEVAL_DPROFILES_MARO_v1_1.md §0–§3`.

**MARO core location:** to be built as a new module (e.g., `platform/src/lib/retrieval/maro/`) consumed by BOTH `platform-mcp/src/server.ts` and `platform/src/app/api/chat/consult/route.ts`. Single source — no per-channel duplication.

**Four behavioral families (from D-PROFILES v1.1 §0.1):**

| Family | Pinned worker / mid / premium | tool_arg_format | structured_output | context_budget | MCP reach |
|---|---|---|---|---|---|
| anthropic | claude-haiku-4-5 / claude-sonnet-4-6 / claude-opus-4-7 | object (no JSON.parse) | json_schema + strict=true | 200K / 1M / 1M | HTTPS only |
| gemini | gemini-2.5-flash-lite / gemini-2.5-flash / gemini-2.5-pro | object (no JSON.parse) | gemini_response_schema, validate values | 8K out / 1M in / 2M in | Streamable HTTP, no `-` in names |
| openai | gpt-4.1-nano / gpt-4.1-mini / gpt-4.1 | JSON.parse(arguments) | json_schema strict, optionals as null union | 1M / 1M / 1M | Streamable HTTP or SSE |
| deepseek | deepseek-chat (worker) / deepseek-v4-pro (premium) | JSON.parse(arguments) | json_object only, validate+retry MANDATORY | ~128K / 1M | NONE — plain tool backend only |

**NVIDIA NIM:** inherits openai profile + `cache_strategy: none`; no fifth profile.

**`behavioral_overrides` field** on `CapabilityDescriptor` (already in `platform/src/lib/retrieval/registry/types.ts`):
```typescript
behavioral_overrides?: {
  anthropic?: Record<string, unknown>
  gemini?: Record<string, unknown>
  openai?: Record<string, unknown>
  deepseek?: Record<string, unknown>
}
```
MARO reads `capability.behavioral_overrides[activeFamily]` for per-capability overrides. Most capabilities leave this unset.

**Per-family normalization axes MARO must implement:**
1. Tool-arg decode: object passthrough (anthropic/gemini) vs `JSON.parse(arguments)` (openai/deepseek)
2. Tool-result wire: `tool_result_block` (anthropic) / `functionResponse+exact_id` (gemini) / `function_call_output|role:tool` (openai) / `role:tool` (deepseek)
3. Caching: explicit breakpoints ≤4 (anthropic) / `caches.create` handle preferred (gemini) / automatic no-code-change (openai) / automatic 64-tok min unit (deepseek)
4. Structured-output: grammar-guaranteed strict (anthropic/openai) / validate-values (gemini) / validate+retry mandatory (deepseek)
5. Reasoning round-trip: `thinking`/`redacted_thinking` UNMODIFIED (anthropic) / `thought_signature` per Part UNMODIFIED (gemini) / `encrypted_content` or `previous_response_id` (openai) / `reasoning_content` MUST be passed back on V4 tool turns (deepseek) — 400 error otherwise
6. Prompt structure: stable prefix first for all four; Gemini puts large common content at beginning

**DeepSeek on MCP:** DeepSeek has no MCP support (`mcp_servers` ignored; MCP content blocks unsupported). If declared family is deepseek on the MCP channel, MARO serves as plain tool-calling backend — no MCP-specific constructs exposed.

**Tool name cross-family compliance:** snake_case, no hyphens, ≤64 chars. This satisfies Anthropic `^[a-zA-Z0-9_-]{1,64}$` and Gemini `[A-Za-z0-9_.]` simultaneously when hyphens are avoided.

---

### §0.3 — [resolved from D7 decision] — MCP declaration mechanism + multi-model substrate

Source: `CLAUDECODE_BRIEF_RETRIEVAL_DPROFILES_MARO_v1_1.md §0.2`; `RETRIEVAL_SYSTEM_DESIGN_APPROACH_v1_0.md §A.4`; `platform-mcp/src/server.ts`.

**Current MCP substrate (from server.ts):**
- Transport: Streamable HTTP (POST /mcp only; `GET /mcp` → 405, stateless, `sessionIdGenerator: undefined`)
- Auth: Bearer API key via `validateMcpKeyFromHeader` + OAuth 2.0 (`validateAccessToken`) — both paths produce a `Principal`
- No SSE. Any plan text citing "SSE streaming on MCP" is wrong.
- Currently wires ~13 tool groups (health endpoint self-reports `tools: 13`); ~14 additional tool files in `platform-mcp/src/tools/` are written-but-unregistered

**Multi-model substrate decision:** NOT a LiteLLM-style self-hosted proxy. The existing model registry at `platform/src/lib/models/registry.ts` already provides 5 provider families (anthropic/google/deepseek/openai/nvidia) with pinned model IDs and quirks. MARO reads from this registry — no proxy layer needed. MARO is a thin orchestration module, not a new inference proxy.

**MCP declaration mechanism (four candidates from §A.4; pick one or priority-ordered combination in-wave):**
1. **Config declaration** — model family stated in MARO config / environment (operator-set)
2. **OAuth scope** — model family encoded in the OAuth scope string at auth time (MCP already has OAuth flow: `handleAuthorize`, `handleToken`, `validateAccessToken`)
3. **Per-key binding** — API key issued per model family; MARO reads family from key metadata (key store is already in `validateMcpKeyFromHeader`)
4. **Client hint** — connecting client sends a header or initial tool-call parameter identifying the model family

Mandatory: undeclared → `family: 'universal'` → consolidated cross-model surface (~10–15 workflow tools).

**Recommendation for implementation:** Per-key binding (option 3) is the cleanest path given the existing `Principal` shape from `validateMcpKeyFromHeader`. Fall back to client hint (option 4) as a secondary. Universal is the default when neither is present. This is a decision to make in-wave.

---

## §1 — D6: whole-corpus synergy

Compose the umbrella + graph + grounding spine into Whole-Chart-Read answers: convergence +
contradiction surfacing across domains/layers (CDLM + CGM), layered hydration (L2→L1→L0).

### §1.1 — F1/F3 composition orchestration

**Entry point:** `query_ucd` (L-ORIENT, bo_samvada/vw_chart_digest) is the mandatory first call.
- Returns: msr_signal_count, top_convergence_domains (career/relationship/character/spirituality/wealth/health), contradiction_count, weakest_graha, top_priority_class
- drill_children declared: `['marsys://tool/L2/query_domain_reading', 'marsys://tool/L2/query_signals', 'marsys://tool/L2/traverse_chart_graph']`

**De-duplication rule (F1):** The router + umbrella assembly must de-duplicate by signal_id across all tool results before synthesis. `query_ucd` returns signal_id references, not restated facts. Downstream drill tools return signal_id refs back to bo_laksana. The composition layer resolves each signal_id exactly once.

**Cross-domain contradiction surfacing (CDLM + CGM):**
- CDLM path: `query_domain_reading` → bodha_cdlm_cells (70 rows, bo_sangati) → cross-domain pair cells
- CGM path: `traverse_chart_graph` → bodha_cgm_nodes (140) + bodha_cgm_edges (360) — relationship_basis 100% NULL; traverse all edges, annotate null basis in output
- Contradiction path: `query_contradictions` → bodha_contradictions (currently 0 rows, graceful-empty) + bodha_discoveries (1,505 rows, novelty-ranked)

**Layered hydration (F3, layer-resolution-DOWN):**
- L2 signals → `constituent_facts_array` → L1 `chart_facts.fact_id` (WARNING: DEFECT-001, 91.5% orphan; handle empty join gracefully)
- L1 facts → `citation_id` → L0 `classical_sources_jsonb` / bg_texts citation
- Every tool with `grounds_to: {l1_fact_ids: true}` participates in the F3 chain

**Multi-vantage reconciliation (D5 §0.4 mandate):**
Every domain reading must return house + kāraka + varga perspectives. `query_domain_reading` MUST return a reconciled multi-vantage view per F1 (one entry, perspectives attached). Temporal tools (L3 `query_temporal_activation`, `query_convergence_windows`) MUST accept `ayanamsha_id` as a filter and anchor to D1 + Moon per the traversal model.

### §1.2 — D6 composition sequence (F1/F3 end to end)

```
1. query_ucd(chart_id)
     → orientation digest (5 rows vw_chart_digest)
     → top domains by convergence score
     → drill_children list

2. query_domain_reading(chart_id, domain, ayanamsha_id)   [for each top domain]
     → bodha_cdlm_cells (CDLM cell for domain pair)
     → bodha_question_lenses (domain lens — bo_drishti)
     → signal_id references → [query_signals drill]

3. query_signals(chart_id, ayanamsha_id, filters)
     → ranked by computed_salience DESC (NOT signature_tier — 100% background)
     → signal_id, signal_summary_text, constituent_facts_array (DEFECT-001: graceful-empty)
     → classical_sources_jsonb (L0 citation refs)

4. traverse_chart_graph(chart_id, seed_signal_ids, depth, mode)
     → CGM subgraph (neighbors/paths/cluster)
     → node centrality + edges (relationship_basis annotated as null)
     → surfaces convergence/divergence structure not visible per signal

5. query_contradictions(chart_id)
     → bodha_contradictions (0 rows — graceful-empty array)
     → bodha_discoveries ranked by novelty_score (1,505 rows)

6. [temporal enrichment when query_class=predictive|holistic]
     query_temporal_activation → query_convergence_windows → query_life_arc
     → kala_convergence (19,482) / kala_jivana_parva (739) / kala_bhavishya (50)

7. [calibration when requested]
     query_quality_scorecard → synthesis_quality_scorecard (2 rows)
     NOTE: unresolved_constituent_facts_count=0 is a FALSE PASS per DEFECT-001
```

**Output shape:** de-duplicated, cited, multi-vantage answer. Every claim traces to signal_id → fact_id → citation_id. Contradictions surfaced where bodha_discoveries has them; CGM structure annotates the relationships.

---

## §2 — D7: channel integration

### §2.1 — Consolidated MCP tool set (rebuilt over the registry)

**Target:** ~10–15 workflow-shaped tools replacing the current ~13-tool ad-hoc wiring.

The new tools are `CapabilityDescriptor` registrations in `platform/src/lib/retrieval/registry/` following the D1 frozen contract. The MCP server (`platform-mcp/src/server.ts`) reads them from the registry via the `mcp_capability_bridge.ts` → registered URIs mapping. The bridge currently has only 5 mappings (`resolve_entity`, `list_entities`, `intent-classify`, `asset-registry-all`, `asset-registry-L0`) — it must be extended for the full consolidated set.

**Provider-spec obligations (from RETRIEVAL_GROUNDTRUTH_LLM_PROVIDER_SPEC_v1_0.md B.i):**
- `outputSchema` + `structuredContent` + text fallback (dual output per MCP spec)
- Cursor pagination on list/search tools (all tools returning >1 row)
- `response_format`/`verbosity` enum parameter on umbrella tools (for undeclared/universal surface)
- UUIDs resolved to names in output (never expose raw UUIDs to the LLM without context)
- Tool names: snake_case, no hyphens, ≤64 chars (cross-family compliance — satisfies Anthropic + Gemini constraints)
- Transport: Streamable HTTP only (matches current `server.ts` — no SSE to add)

**Consolidated MCP tool surface (~12 workflow tools):**

| MCP Tool Name | Registry URI(s) composed | Workflow role |
|---|---|---|
| `get_chart_orientation` | `marsys://tool/L2/query_ucd` | L-ORIENT entry; always first call |
| `get_domain_reading` | `marsys://tool/L2/query_domain_reading` | domain drill; chart+domain |
| `get_signals` | `marsys://tool/L2/query_signals` | signal filter/rank |
| `traverse_graph` | `marsys://tool/L2/traverse_chart_graph` | CGM neighbor/path/cluster |
| `get_positions` | `marsys://tool/L1/get_positions` | L1 graha positions |
| `get_dashas` | `marsys://tool/L1/get_dashas` | Vimshottari chain |
| `get_temporal_windows` | `marsys://tool/L3/query_temporal_activation` + `marsys://tool/L3/query_convergence_windows` | temporal activation + convergence |
| `get_projections` | `marsys://tool/L3/query_projections` | probabilistic forward projections |
| `get_classical_citation` | `marsys://tool/L0/query_classical_texts` | L0 prose/verse |
| `get_remedies` | `marsys://tool/L2/query_remedies` | remedy prescriptions |
| `get_chart_quality` | `marsys://tool/L2/query_quality_scorecard` + `marsys://tool/L4/query_falsifiers` | calibration/trust |
| `list_assets` | `marsys://resource/asset-registry/all` | asset catalog |

**Declared→profiled / undeclared→universal:**
- **Declared** (family known via per-key binding or client hint): MARO serves that family's profiled surface. Tool bundles shaped per behavioral profile (bundle size, arg format, structured-output mode, caching headers).
- **Undeclared**: MARO serves the universal surface above — consolidated tools, `response_format`/`verbosity` param, dual structuredContent+text output, snake_case names with no hyphens.
- **DeepSeek declared on MCP**: strip MCP-specific constructs; serve as plain tool-calling backend (no resources, no prompts, no content blocks).

### §2.2 — Chat engine convergence (retire lib/retrieve dependency)

**Current state (from route.ts):**
- `platform/src/app/api/chat/consult/route.ts` imports `getTool` from `@/lib/retrieve/index` (line 76) and `buildChatToolsFromNames` from `@/lib/retrieve/tool_catalogue` (line 77)
- `getTool(toolName)` returns a `RetrievalTool` from `RETRIEVAL_TOOLS` array in `lib/retrieve/index.ts`
- `lib/retrieve/` still carries `audience_tier` in its types and uses the msr_sql-family tools
- The B.11 floor enforcement in route.ts names `msr_sql`, `cgm_graph_walk`, etc. — these are old `lib/retrieve` names

**Target state (D7 convergence):**
- `/api/chat/consult` calls `getCapability(uri)` from `@/lib/retrieval/registry` instead of `getTool()` from `@/lib/retrieve`
- The planner's `tool_calls[].tool_name` maps to registry URIs (e.g., `msr_sql` → `marsys://tool/L2/query_signals`; `cgm_graph_walk` → `marsys://tool/L2/traverse_chart_graph`)
- `executeWithCache(t, queryPlan, cache, ...)` adapts to call `capability.handler(args, ctx)` returning `ToolResult`
- B.11 floor enforcement updated: `msr_sql` floor → `marsys://tool/L2/query_signals`; `cgm_graph_walk` floor → `marsys://tool/L2/traverse_chart_graph`
- `lib/retrieve/` is NOT deleted immediately — it is retired by making route.ts route through the registry; `lib/retrieve` becomes a dead import with a deprecation notice. Deletion is a D8 cleanup gate item.

**Parity proof (single query source = no drift):**
The existing `parity_check.ts` (`platform/src/lib/retrieval/registry/parity_check.ts`) compares `listCapabilityUris()` (Consume Chat registry) against `listMcpCapabilityUris()` (bridge). Both channels call the same `CapabilityDescriptor.handler`. Parity test proves identical filter behavior: same handler invoked on both channels → drift structurally impossible.

`mcp_capability_bridge.ts` must be extended: add a `registerMcpToolUri(toolName, uri)` call for every consolidated MCP tool. Then `runParityCheck()` will validate both channels share the same registry URIs.

**MARO consumption on chat channel:**
Chat calls MARO with `family` = resolved from `selectedStack` (from `STACK_ROUTING` / `DEFAULT_STACK_ID='gemini'`). MARO shapes bundle size, prompt structure, caching headers, arg-decode, and output validation per the active family profile. No per-channel duplication of family logic.

### §2.3 — Old MCP tools remediation (DESTRUCTIVE — reverse-citation gate mandatory)

Source: `00_ARCHITECTURE/RETRIEVAL_GROUNDTRUTH_CODE_VALIDATION_v1_0.md §H`.

**The contaminated surface:** `platform-mcp/src/tools/` (the old tools). The new `platform/src/lib/retrieval/registry/` is CLEAN. Build on the new registry; treat old tools as a remediation target.

**Reverse-citation gate (mandatory before any removal):** For each old tool file, run a reverse-citation grep to find all imports/registrations. Produce a citation report. Only remove after confirming zero active callers OR after the caller has been migrated. Include citation report in PR.

**CRITICAL findings (§H.2) — remediation list:**

| Severity | Finding | File(s) | Remediation |
|---|---|---|---|
| CRITICAL | `chart_id ?? NATIVE_CHART_ID` default fallback | `platform-mcp/src/tools/retrieval/kala_temporal.ts:45,466`; `retrieval/holistic_bundle.ts:56,280`; `l0_brahmagyan.ts:23,218` | Make `chart_id` required; error-if-missing (no fallback) |
| CRITICAL | `.default(NATIVE_CHART_ID)` on schema | `platform-mcp/src/tools/kala_temporal.ts:39,571` | Remove `.default()`; set as required field |
| CRITICAL | `date_range.start ?? '1984-02-05'` (native lifespan as default) | `kala_convergence.ts:154` | Remove default; make `date_from` required or error |
| CRITICAL | `l0_brahmagyan.ts` stamps native id on every classify call | `l0_brahmagyan.ts:23,218` | Scrub native id; use caller-supplied chart_id or error |
| HIGH | `lel_query` in `mimamsa_lel_intake.ts` — no chart_id param; description names native + "57 events" | `mimamsa_lel_intake.ts` | Add required `chart_id`; scrub native name + count from description |
| HIGH | Native computed dāśā tables embedded as literal fallback | `kala_period_snapshot.ts:50`, `kala_timeline.ts:54,314`, `retrieval/kala_temporal.ts:159` | Remove embedded native data; require caller-supplied chart_id |
| MEDIUM | Native-as-fixture tests (one asserts description must contain "Abhisek Mohanty") | `__tests__/kala_temporal*.test.ts`, `phala_muhurta.test.ts:243` | Rewrite tests to use a generic chart fixture |
| LOW | Native ids in ~21 LLM-visible `.describe()`/JSDoc strings | `bo_2-5/6`, `bodha_bo22`, `get_cgm_subgraph`, `phala_*`, etc. | Scrub to `<chart_uuid>` placeholder |
| LOW | `?? 'default'` cache-key bucket (cross-chart collision) | `bundle_adapters.ts:229+`, `bundles/holistic_bundle.ts:295` | Replace with `chart_id`-scoped cache key |

**Remediation approach per item:**
1. Run reverse-citation grep (gate). Log results in PR.
2. If old tool is being replaced by a new registry capability: migrate callers first, then remove the old tool.
3. If old tool is being kept temporarily: apply the specific fix (remove `?? NATIVE_CHART_ID`, add required chart_id, scrub description).
4. Re-run `chart_agnostic_gate.ts` to confirm no violations remain.
5. Re-run `runParityCheck()` to confirm both channels still align.

**chart_agnostic_gate.ts enforces (DO NOT weaken):**
- RULE-1: per_chart scope → `chart_id` in `required_inputs`
- RULE-2: no literal `482012f1-…` or `362f9f17` in description/name/uri
- RULE-3: no native identifiers (`Abhisek Mohanty`, `1984-02-05`, `Bhubaneswar`) in description
- RULE-4: no `default` value on `chart_id` input_schema field
- RULE-5: no native UUID in `input_schema.chart_id.description`
- RULE-6: global scope must NOT have `chart_id` in required_inputs
- RULE-7: all D1 contract fields must be present (scope, archetype, traversal_level, tool_role, emits_references, lel_capable)

---

## §3 — What this is NOT

Not the eval/seal (D8). Not new tools (composes the D5 roster — that roster is defined in D5 v1.1).
No removal of old tools without the citation gate. Not a new LLM inference proxy (MARO reads the
existing `platform/src/lib/models/registry.ts`; no new proxy layer). Not a new auth mechanism
(MCP OAuth and key validation already exist in `platform-mcp/src/server.ts`).

---

## §4 — Acceptance criteria

1. **D6 composition:** `query_ucd` → domain drill → signal ranking by `computed_salience` (NOT signature_tier) → CGM traversal → contradiction/discovery surfacing; produces de-duplicated, cited, multi-vantage Whole-Chart-Read answers. F1 (reference-don't-repeat) and F3 (layer-resolution-DOWN to L1 fact_ids/L0 citation_ids) both verified. DEFECT-001 graceful-empty handling on constituent_facts_array confirmed.

2. **Consolidated MCP tool set:** ~10–15 workflow-shaped tools over the registry; all D1 contract fields present; `outputSchema` + `structuredContent` + text fallback; cursor pagination; `response_format`/`verbosity` enum; UUIDs resolved to names; tool names snake_case, no hyphens, ≤64 chars. Chart-agnostic gate green on all new tools.

3. **MCP↔chat parity:** `runParityCheck()` passes — both channels share registry URIs via the bridge. `route.ts` no longer calls `getTool()` from `lib/retrieve`; calls `getCapability(uri)` from the registry. A parity test proves identical handler invocation on both channels.

4. **MARO:** Core implemented; reads `selectedStack` → family → behavioral profile; shapes bundle size, arg decode, structured-output mode, caching, reasoning round-trip per profile. Consumed by both `server.ts` (MCP) and `route.ts` (chat). Declared→profiled / undeclared→universal MCP behavior live. DeepSeek-on-MCP exception (plain tool backend) implemented.

5. **Old MCP tool remediation:** Every CRITICAL/HIGH finding from §H.2 remediated. Reverse-citation gate run before any removal; citation report in PR. `chart_agnostic_gate.ts` passes on the old tools surface post-remediation (zero RULE-1 through RULE-7 violations). `?? 'default'` cache-key bucket fixed to chart_id-scoped keys.

6. **No destructive op without citation report.** No op that removes any file from `platform-mcp/src/tools/` without a confirmed-zero-callers report in the PR.

---

## §5 — Detail-pass log: resolved markers

| Marker | Resolved from | Resolution |
|---|---|---|
| `[resolved from D5]` — final tool roster | `CLAUDECODE_BRIEF_RETRIEVAL_D5_FANOUT_v1_1.md §1.0–§1.4` | 15+19+1+2 existing capabilities; 6+11+9+3 to-build. Full roster with archetype/role/data-notes in §0.1 |
| `[resolved from D-PROFILES]` — MARO core + profiles | `CLAUDECODE_BRIEF_RETRIEVAL_DPROFILES_MARO_v1_1.md §0.1–§3` | 4 families (anthropic/gemini/openai/deepseek), pinned model IDs, 6 normalization axes, behavioral_overrides field shape. NVIDIA inherits openai profile. MARO is a module, not a new inference proxy |
| `[resolved from D7 decision]` — MCP declaration mechanism | `CLAUDECODE_BRIEF_RETRIEVAL_DPROFILES_MARO_v1_1.md §0.2`; `server.ts` | 4 candidate mechanisms enumerated. Per-key binding recommended (existing Principal shape); client hint as fallback; universal mandatory when undeclared |
| `[resolved from D7 decision]` — multi-model substrate | `platform-mcp/src/server.ts`; `platform/src/lib/models/registry.ts` | NOT a LiteLLM proxy. MARO reads existing registry.ts (5 families, pinned IDs, quirks). No new proxy layer |
| `[resolved from server.ts]` — current MCP wiring | `platform-mcp/src/server.ts` | ~13 tool groups wired; Streamable HTTP POST only (GET /mcp → 405, no SSE); Bearer + OAuth auth; Cloud Run `asia-south1` |
| `[resolved from route.ts + lib/retrieve]` — chat convergence target | `platform/src/app/api/chat/consult/route.ts:76-77`; `lib/retrieve/index.ts` | `getTool()` from lib/retrieve is the current source; replace with `getCapability(uri)` from registry; B.11 floor tool names need URI remapping; lib/retrieve retired (not deleted) |
| `[resolved from §H contamination]` — old MCP tools remediation list | `RETRIEVAL_GROUNDTRUTH_CODE_VALIDATION_v1_0.md §H.2` | 5 CRITICAL + 2 HIGH + 1 MEDIUM + 2 LOW findings; specific file:line evidence; remediation steps in §2.3 |
| `[resolved from parity_check.ts]` — parity mechanism | `platform/src/lib/retrieval/registry/parity_check.ts`; `mcp_capability_bridge.ts` | `runParityCheck()` + `checkParity()` infrastructure exists. Bridge currently has 5 tool→URI mappings; must be extended for consolidated MCP set |
| `[resolved from chart_agnostic_gate.ts]` — gate mechanism | `platform/src/lib/retrieval/registry/chart_agnostic_gate.ts` | 7 rules (RULE-1 through RULE-7); FROZEN; run via `npm run registry:chart-agnostic-gate`; wire into CI post-D7 |

*End of CLAUDECODE_BRIEF_RETRIEVAL_D6_D7_CHANNELS v1.1 (detail-pass 2026-06-28).*
