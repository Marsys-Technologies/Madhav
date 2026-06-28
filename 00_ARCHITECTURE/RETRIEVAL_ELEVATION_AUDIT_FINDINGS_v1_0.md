---
artifact: RETRIEVAL_ELEVATION_AUDIT_FINDINGS_v1_0.md
canonical_id: RETRIEVAL_ELEVATION_AUDIT_FINDINGS
version: 1.0
status: CURRENT
created: 2026-06-28
author: Claude Code (3-agent parallel audit: retrieval code + MCP code + live DB) — for native Abhisek Mohanty
classification: audit findings — retrieval elevation + Part 3 seam (retrieval side)
input_audit: RETRIEVAL_MCP_UNIFIED_AUDIT_AND_SYNC_CONTRACT_v1_0.md (Cowork baseline)
method: read actual code (registry, router, MARO, handlers, chat path, gateway) + live DB queries for
  DEFECT-001 orphan rate and bodha_contradictions; code/runtime wins over docs
charts_checked:
  - native: 482012f1-710e-4a25-994a-93821f5871aa
  - second: 9da866fb-8f0c-44bb-b625-1d8dfcd2f975 (0 MSR signals; not independently useful for orphan check)
  - cross-ref: 1c826d5a-41cb-4450-b4dc-59d440e5f75a (Abhinandan — 58,675 MSR signals, orphan rate not run)
changelog:
  - v1.0 (2026-06-28): First code+runtime audit. Confirms Cowork baseline on 7 of 9 items; surfaces 6 new
      findings not present in the Cowork audit; provides precise root-cause for DEFECT-001.
---

# RETRIEVAL ELEVATION AUDIT FINDINGS (v1.0)

> **Scope:** Part 1 (retrieval system 1.1–1.10) + Part 3 retrieval-side (seam + entitlement boundary).
> Strictly read-only. Code wins over docs. Live DB numbers for items 1.5 + 1.6.
> Divergences from `RETRIEVAL_MCP_UNIFIED_AUDIT_AND_SYNC_CONTRACT_v1_0.md` are flagged with ★.

---

## §1 — VERDICT TABLE

| Item | Goal | Verdict | Priority |
|---|---|---|---|
| 1.1 | Keystone — Two-surface gap | **GAP** | **P0 (both forks)** |
| 1.2 | Reasoning-units vs data-units | **PARTIAL** | P1 |
| 1.3 | Coverage vs question-space | **PARTIAL** | P1–P2 |
| 1.4 | Whole-chart-read enforced | **PARTIAL** | P1 |
| 1.5 | Contradiction/convergence first-class | **GAP** (code stubs + 0 data rows) | P1–P2 |
| 1.6 | Grounding data — DEFECT-001 orphan rate | **GAP** (91.5% confirmed, root cause known) | **P1 prerequisite** |
| 1.7 | Bundle-elasticity | **GAP** | P2 |
| 1.8 | MARO / per-model profiles | **PARTIAL** (code intact; runtime not invoked) | P2 |
| 1.9 | Resources + prompts | **GAP** (resources dead; zero prompts) | P1 |
| 1.10 | Channel-agnostic | **PARTIAL** (registry clean; MCP ignores it) | P0 (follows keystone) |
| 3.1 | Seam — path map | **GAP** (two disconnected surfaces, not one) | P0 |
| 3.2 | Entitlement — invokeTool chokepoint | **PARTIAL** (built but not wired) | P0 |
| 3.3 | Entitlement-boundary ruling implementable | **PARTIAL** (prereq: user_uid→owner_id lookup missing) | P0 |

---

## §2 — PER-ITEM FINDINGS (code-grounded)

### 1.1 — KEYSTONE: Two Surfaces

**Verdict: GAP**

The sealed registry (`platform/src/lib/retrieval/`) is real and structurally correct. The live MCP server ignores it for ~28 of 31 registered tools.

**Bypass count (tools running their own SQL or sidecar):** 28 of 31

| Route | Tool examples | Backend | Through registry? |
|---|---|---|---|
| Direct pg.Pool | `holistic_bundle_chart_facts` (`retrieval/holistic_bundle.ts`) | Own pool | ✗ |
| Direct pg.Pool | `query_remedies` + 6 siblings (`remedy_tools.ts`) | Own pool | ✗ |
| Python sidecar | `holistic_bundle` (`bo_2-8.ts`), `kala_temporal_bundle`, `event_anchors`, `phala_outlook`, `lel_query`, `record_outcome`, `query_calibration` | `PYTHON_SIDECAR_URL` | ✗ |
| Platform REST (correct path) | `resolve_entity`, `list_entities`, `asset_registry_*` (`l0_brahmagyan.ts`) | Platform REST | partial ✓ |
| `callPlatformPrimitive` → `/api/mcp/primitives` | `mitigation_map`, `muhurta_finder` | Registry path | ✓ (but 401; see 2.10) |

**The `/api/mcp/primitives` route** (`platform/src/app/api/mcp/primitives/[tool]/route.ts`) is the correct path: calls `getToolByName()` → `capability.handler`. Used by only 2 MCP tools — and both are currently broken by the `x-mcp-audience-tier` 401 bug (see §4 NEW-5).

**★ Divergence from Cowork:** Cowork said "~30 in-process tools" bypass the registry. Actual registered tool count is **31**, not ~30. The bypass is 28/31, not "nearly all" — quantified exactly.

---

### 1.2 — Reasoning-Units vs Data-Units

**Verdict: PARTIAL**

~75 `CapabilityDescriptor`s exist across waves. All return data units — structured table rows, signal sets, graph edges — not reconciled astrological judgments.

**Missing composite domain tools (none exist in registry or MCP):**
- `assess_marriage` — 7th lord + Venus kāraka + D9 + bhāvat-bhāva + afflictions + activating dasha + citations
- `assess_career` — 10th lord + Saturn kāraka + D10 + yogas + timing
- `assess_health` — 1st + 6th + 8th lords + Sun + afflictions + D1/D6
- `assess_wealth` — 2nd + 11th lords + Jupiter kāraka + dasha activation
- Yoga-activation-by-dasha bridge (which yogas are activated in the current/upcoming dasha-antardasha)

**`holistic_bundle`** (`bo_2-8.ts:278`) is the closest to a reasoning unit: returns MSR signals + CGM graph + chart_facts rows — ingredients, not a synthesis. The LLM must synthesize from the bundle; the retrieval layer does not pre-reconcile.

**★ Divergence from Cowork:** Confirmed exactly. No additions since Cowork audit.

---

### 1.3 — Coverage vs Question-Space

**Verdict: PARTIAL**

**Full capability inventory (from `platform/src/lib/retrieval/registry/index.ts` + wave files):**
- **~75 tools** (all CapabilityDescriptor entries)
- **9 resources** defined — all dead (see 1.9)
- **0 prompts** — none defined anywhere in `platform/src/lib/retrieval/`

**Layer distribution:**
- L0: ~12 capabilities (Brahmagyan, ephemeris, classical texts)
- L1: ~20 capabilities (Gaṇita fact lookups — positions, dignity, strength, dashas, divisionals)
- L2: ~25 capabilities (Bodha — MSR signals, CGM graph, CDLM, contradictions, synergy)
- L3: ~8 capabilities (Kāla — temporal, convergence, dasha timing)
- L4: ~6 capabilities (Phala — event anchors, mitigation, outlook)
- L5: ~4 capabilities (Mīmāṃsā — LEL intake, calibration)

**Semantic gaps (classically-relevant judgments the LLM cannot reach through retrieval):**
- No domain-composite assessment tools (marriage, career, health, wealth)
- No yoga-activation-by-dasha bridge
- No transit-over-natal activation surface
- No "current life-phase" reasoning entry point
- No contradiction synthesis (bodha_contradictions = 0 rows; tool is a stub over empty data)
- No classical verse citation by domain (BM25+dense hybrid retrieval not built)
- No cross-school comparison tool

---

### 1.4 — Whole-Chart-Read (B.11) Enforcement

**Verdict: PARTIAL (chat injects) / GAP (MCP, not enforced)**

Three layers of B.11 code exist with increasing quality — but the strongest is not wired:

1. **`platform/src/lib/gateway/b11_floor.ts`** — `B11_FLOOR_TOOL_NAMES` array defines the floor tool set.
2. **`platform/src/lib/gateway/invoke_tool.ts`** — implements B.11 as a **hard gate** (`GatewayError 'B11_FLOOR_MISSING'`): if no floor tool is in the planned toolsAuthorized set, execution is refused. **This is the correct architecture — but it is not wired into any route.**
3. **`platform/src/app/api/chat/consult/route.ts`** — enforces B.11 by **injection**: if no L2.5 floor tool in the plan, injects `msr_sql + cgm_graph_walk` (analytical) or `msr_sql + vector_search + pattern_register` (predictive). Orientation is forced but soft (cannot refuse; only adds).

**`platform-mcp/src/server.ts`** — zero B.11 enforcement of any kind. Any MCP client can call `event_anchors`, `kala_temporal_bundle`, or `phala_outlook` with no prior orientation call.

**★ Divergence from Cowork:** Cowork said "router biases orient-first." The code is stronger than that on the chat path (injection, not bias) but the hard gate (`invoke_tool.ts`) is real and not-wired — Cowork did not mention the gateway.

---

### 1.5 — Contradiction/Convergence as First-Class Outputs

**Verdict: GAP**

**Code status:**
- `query_contradictions` and `contradiction_register` — `CapabilityDescriptor` entries exist in the registry; handler returns rows from `bodha_contradictions`. Structurally correct.
- `synergy_cross_layer` and `synergy_pipeline` — descriptor stubs in the registry; **no real handler code** in any file under `platform/src/lib/retrieval/`.
- `traverse_chart_graph` → maps to `cgm_graph_walk` capability; real handler that walks CGM edges. Returns traversal data, not contradiction synthesis. CGM edges: **720 rows** (live).

**Live data (from DB agent):**
```
bodha_contradictions: 0 rows (total, all charts)
bodha_cgm_nodes:    280 rows
bodha_cgm_edges:    720 rows
```

The contradiction table has a fully defined 15-column schema (`contradiction_id, chart_id, signal_a_id, signal_b_id, tension_basis_jsonb, tension_class, domains_affected_array, combined_salience, resolution_hint_jsonb, …`) — but has never been populated for any chart.

**★ Divergence from Cowork:** Confirmed exactly. No change.

---

### 1.6 — Grounding Data: DEFECT-001 Orphan Rate

**Verdict: GAP — 91.5% orphan rate CONFIRMED, root cause now precisely identified**

**Live query results (native chart `482012f1`):**

| Metric | Value |
|---|---|
| bodha_msr_signals rows (native chart) | 66,738 |
| constituent_facts_array entries (native chart) | 66,832 |
| Resolved refs (resolve to real chart_facts fact_id) | 5,671 (8.5%) |
| Orphaned refs (fact_id exists nowhere in chart_facts) | 61,161 (**91.5%**) |
| Distinct orphaned fact_ids | 61,160 |
| Orphaned fact_ids existing under any chart | 0 |

**Root cause (NEW — not in Cowork audit):**

The ghost fact_ids are not a data-type or UUID mismatch — they are **genuinely dead references** from a superseded L1 build:
- `bodha_msr_signals` last built: **2026-06-20** (build `703b768e`)
- `chart_facts` current authoritative build: **2026-06-24** (build `586f4e9b`, 128,567 facts — new fact_id hashes)
- MSR was never rebuilt after the L1 rebuild on 2026-06-24

The 5,671 "resolved" refs resolve to **stale ghost builds** (`aa819e29` etc.) that still exist in `chart_facts` from pre-June-24 runs — not to the current authoritative build. They are not actually correct.

**The native's claim that "the MSR was rebuilt" is not confirmed.** The MSR signals in the DB date to 2026-06-20 and reference a fact_id namespace that was superseded four days later.

**Code path** (`platform/src/lib/retrieval/grounding/capability.ts`): `resolve_signals` → `resolveSignals()` → queries `chart_facts WHERE fact_id = $1`. Structurally correct; silently returns empty on orphaned IDs (no error thrown).

**Fix required before reasoning-unit elevation can proceed:**
1. Rebuild `bodha_msr_signals` against the current `chart_facts` build `586f4e9b`
2. Rebuild `bodha_contradictions` (still 0 rows for any chart)
3. Verify orphan rate drops to <5%

**★ Divergence from Cowork:** Cowork noted "native said MSR rebuilt — re-check live." Live check confirms the claim does not hold. Root cause is now precisely identified (build timestamp mismatch, not a code defect).

---

### 1.7 — Bundle-Elasticity

**Verdict: GAP**

- `platform/src/lib/retrieval/maro/types.ts` — `verbosity_enum: ['minimal', 'standard', 'detailed']` declared.
- Router passes `verbosity: 'concise'` in planned calls.
- **No capability handler in any tool file reads or branches on `response_format` or `verbosity`.** The params exist in the schema and type system; they are behaviorally inert.
- MARO `resolveNormalization()` applies `context_budget` shaping (token planning), but this does not change what data the handler fetches or what the response contains.

**★ Divergence from Cowork:** Confirmed exactly.

---

### 1.8 — MARO / Per-Model Profiles

**Verdict: MEETS (code + tests) / GAP (runtime not invoked on MCP channel)**

**Code status:**
- `platform/src/lib/retrieval/maro/profiles.ts` — `PROFILE_VERSION='1.1.0'`, `PROFILE_STATUS='MEASURED'`. All 4 family profiles + universal defined: `anthropic`, `gemini`, `openai`, `deepseek`.
  - Each profile: `tool_arg_format`, `cache_strategy`, `structured_output_format`, `validate_and_repair`, `reasoning_round_trip`, `mcp_transport`, `strip_mcp_constructs`, `max_active_tools`, `context_budget` (premium/standard/worker tiers).
- `platform/src/lib/retrieval/maro/normalizer.ts:291` — `resolveNormalization()` throws if `chart_id` absent (good).
- `getMcpSurfaceSpec(family)` present at `normalizer.ts:350` — returns `{family, max_tools, tool_name_pattern, requires_dual_output, strip_mcp_constructs, transport}`.
- `maro.test.ts` — 11 describe blocks, comprehensive.
- `behavioral_overrides` field on `CapabilityDescriptor` type; `applyBehavioralOverrides()` implemented. **Zero capabilities set this field.** Mechanism is inert.

**Runtime gap:**
- `platform-mcp/src/server.ts` — never calls `resolveNormalization()` or `getMcpSurfaceSpec()`.
- `getMcpSurfaceSpec()` exists (not missing as implied by one Cowork note) but is consumed by nothing at runtime.

**★ Divergence from Cowork:** `getMcpSurfaceSpec` DOES exist in the codebase — it is present at `normalizer.ts:350`. Cowork implied it may not exist ("Is getMcpSurfaceSpec consumed by anything at runtime?" — it exists but is unconsumed). Profiles are `PROFILE_STATUS='MEASURED'`, stronger than Cowork's framing of them as research-backed hypotheses. This is a positive divergence.

---

### 1.9 — Resources + Prompts

**Verdict: GAP (both dead)**

**Resources:**
- `platform-mcp/src/resources/index.ts:36` — `registerResources(server)` exports; 9 resources defined:
  `marsys://chart-snapshot`, `marsys://chart-overview`, `marsys://house-rules`, `marsys://capabilities`,
  `marsys://school-conventions`, `marsys://chart-bundle/{chart_id}`, `marsys://multi-ayanamsha/{chart_id}`,
  `marsys://classical-texts/{text_key}`, `marsys://resource/sutravali/…`
- **`registerResources()` is not called anywhere in `platform-mcp/src/server.ts`**. All 9 resources are dead at runtime.

**Prompts:**
- Zero `server.prompt()` calls anywhere in `platform-mcp/src/`.
- Zero prompt definitions in `platform/src/lib/retrieval/`.

**★ Divergence from Cowork:** Confirmed exactly.

---

### 1.10 — Channel-Agnostic Architecture

**Verdict: PARTIAL**

- The registry/router/MARO are channel-agnostic by design (`chart_id` from request context, no caller awareness, no tier awareness). The NEW registry (`platform/src/lib/retrieval/`) is clean.
- **Chat path** (`/api/chat/consult`) uses the new registry via `getToolByName()`. Same registry as `/api/mcp/primitives`. ✓
- **MCP path** (`platform-mcp/src/server.ts`) uses the new registry for 2 of 31 tools (via `callPlatformPrimitive`). The other 29 use in-process SQL/sidecar — a different retrieval stack entirely. ✗
- **Old `platform/src/lib/retrieve/`** still exists as dead code. Not deleted; not used by consult.
- **`platform/src/lib/mcp/primitives_registry.ts`** — the bridge (`getToolByName()` → `getCapability()` → `handler`) is correct and functional; underused.

**Net:** the two channels (chat vs MCP) use different retrieval stacks for the same logical operations. Channel-agnosticism is a property of an underused path, not a runtime guarantee.

---

## §3 — PART 3: THE SEAM (retrieval side)

### 3.1 — Path Map: Every Channel-to-Retrieval Path

| Channel | Path | Through registry? | Entitlement check? |
|---|---|---|---|
| Chat consult | `/api/chat/consult` → `getToolByName()` → `capability.handler` | ✓ (new registry) | ✓ (`authorizeChartAccess` — 18 callers on portal path) |
| MCP `callPlatformPrimitive` | `platform-mcp/client.ts` → `/api/mcp/primitives/[tool]` → `getToolByName()` → `capability.handler` | ✓ | ✗ (route has zero `authorizeChartAccess` calls) |
| MCP in-process direct SQL | `platform-mcp/src/tools/remedy_tools.ts`, `holistic_bundle.ts`, etc. | ✗ (bypasses entirely) | ✗ |
| MCP in-process sidecar | `platform-mcp/src/tools/bo_2-8.ts`, `kala_temporal.ts`, etc. | ✗ (bypasses entirely) | ✗ |

**The "single source" is real for chat; the MCP path violates it for 28 of 31 tools.**

### 3.2 — Entitlement: authorizeChartAccess + invokeTool chokepoint

**`authorizeChartAccess`** (`platform/src/lib/auth/authorizeChartAccess.ts`):
- 4-rule check: `super_admin → 'all'`; `owner_id match → 'all'`; `chart_grants row → 'view'`; else `'deny'`
- 18 callers on the portal/chat path — it IS the built chokepoint there.
- **Zero callers in `platform-mcp/`**.

**`invoke_tool.ts`** (`platform/src/lib/gateway/invoke_tool.ts`):
- Implements B.11 as a hard gate AND calls `authorizeChartAccess` before execution — this is exactly Option 1 (gate at channel; retrieval stays frozen).
- **Not wired into any route.** The gateway exists as implemented architecture that nobody calls.

**Missing prerequisite:** The MCP `Principal` carries only `{user_uid, key_id}`. `authorizeChartAccess` needs `owner_id`. Wiring it into MCP requires a DB lookup: `user_uid → owner_id` (via a `users` / `profiles` join). This join is not present anywhere in `platform-mcp/`.

### 3.3 — Entitlement-Boundary Ruling: Is Option 1 Implementable?

**Answer: Yes, but with one blocking prerequisite.**

Option 1 (gate at channel via `authorizeChartAccess`; retrieval stays frozen) is the correct and already-partly-built architecture. The blocker is not architectural — it is the missing `user_uid → owner_id` resolution step on the MCP path. Once that DB lookup is added to the MCP auth layer, `authorizeChartAccess` can be wired into every tool handler (or into a middleware before tool dispatch).

The retrieval layer itself stays frozen — it does not need to know about entitlement. The `invoke_tool.ts` gateway code is the correct template.

---

## §4 — NEW FINDINGS vs COWORK AUDIT

These are findings not present in `RETRIEVAL_MCP_UNIFIED_AUDIT_AND_SYNC_CONTRACT_v1_0.md`:

**NEW-1: DEFECT-001 root cause is a build timestamp mismatch, not a code defect.**
MSR signals (build 2026-06-20) reference a fact_id namespace superseded by the L1 rebuild on 2026-06-24 (build `586f4e9b`). The MSR must be rebuilt post-L1-rebuild. The 5,671 "resolved" refs are to stale ghost build rows — not authoritative. Fix: rebuild MSR after every L1 chart_facts rebuild.

**NEW-2: `invoke_tool.ts` hard gate exists but is not wired.**
The gateway (`platform/src/lib/gateway/invoke_tool.ts`) implements B.11 as a hard gate (GatewayError 'B11_FLOOR_MISSING') — stronger than what Cowork described. It is not called by any route. This is the correct B.11 mechanism; it should be the wiring target.

**NEW-3: MARO profiles are `PROFILE_STATUS='MEASURED'`, not research hypotheses.**
The four family profiles are marked MEASURED (version 1.1.0). Cowork framed them as research-backed hypotheses pending measurement. They are ahead of that — already at measured status.

**NEW-4: `getMcpSurfaceSpec()` EXISTS at `normalizer.ts:350`.**
Cowork raised doubt about its existence. It exists and returns the correct surface spec. It is unconsumed at runtime, but the function is complete.

**NEW-5: `callPlatformPrimitive` is broken — live 401 on `mitigation_map` + `muhurta_finder`.**
`platform/src/app/api/mcp/primitives/[tool]/route.ts:87` still requires `x-mcp-audience-tier` header. `platform-mcp/src/client.ts` stopped sending it (tier excision 2026-05-28). The two tools that correctly use the registry path (`mitigation_map`, `muhurta_finder`) currently 401 on every call. The "correct" MCP tools are actually the broken ones. This is a critical regression not in the Cowork audit.

**NEW-6: Registry wave wiring absent at MCP startup.**
`registry/index.ts` documents that wave registration functions must be called at application startup before `getCatalog()`. These calls are absent from `server.ts`. The registry is populated on the Next.js path via module import; the MCP server has an empty registry (irrelevant today since MCP bypasses it, but blocks the keystone fix).

**NEW-7: `msr_sql` duplicate in `SURGICAL_TOOLS`.**
`platform/src/lib/retrieval/registry/tool_name_bridge.ts` — `msr_sql` listed twice. Minor but creates inconsistency in coverage validation.

**NEW-8: Dual `holistic_bundle` registration.**
Both `holistic_bundle` (Python sidecar via `bo_2-8.ts`) and `holistic_bundle_chart_facts` (direct pg.Pool) are registered simultaneously in `server.ts`. Two overlapping B.11 floor tools with different backends, different failure modes, and different data paths. No dedup logic between them.

**NEW-9: Old `platform/src/lib/retrieve/` still exists as dead code.**
Not deleted post-migration. Not used by consult. Should be removed to prevent confusion about which retrieval system is authoritative.

---

## §5 — LIVE DATA NUMBERS

| Table | Count | Notes |
|---|---|---|
| `bodha_msr_signals` (total) | 125,413 | native: 66,738; Abhinandan `1c826d5a`: 58,675 |
| `bodha_contradictions` (total) | **0** | Table exists with 15-column schema; never populated |
| `bodha_cgm_nodes` | 280 | |
| `bodha_cgm_edges` | 720 | |
| `chart_facts` (native, current build) | 128,567 | build `586f4e9b`, 2026-06-24 |
| `chart_facts` (native, all builds) | 142,416 | includes stale ghost builds |
| **DEFECT-001 orphan rate (native chart)** | **91.5%** | 61,161 of 66,832 refs are dead |
| Resolved refs (to any chart_facts build) | 5,671 (8.5%) | Resolving to stale ghost rows — not authoritative |
| Distinct orphaned fact_ids | 61,160 | None exist anywhere in chart_facts under any chart |
| Second chart MSR signals (`9da866fb`) | 0 | Cannot compute orphan rate |

---

## §6 — TOP GAPS IN PRIORITY ORDER

| Priority | Gap | Action required |
|---|---|---|
| **P0-A** | **Keystone: MCP bypasses registry for 28/31 tools** | Wire MCP → registry path; retire in-process SQL tools. Also fix NEW-6 (wave wiring at MCP startup). |
| **P0-B** | **Live 401: `callPlatformPrimitive` broken by `x-mcp-audience-tier` mismatch** (NEW-5) | Remove the `audienceTierHeader` guard from `/api/mcp/primitives/[tool]/route.ts:87`; the tier excision was correct but the route was not updated. |
| **P0-C** | **Chart entitlement absent on MCP path** (zero calls to `authorizeChartAccess`) | Add `user_uid → owner_id` DB lookup to MCP auth; wire `authorizeChartAccess` at tool dispatch (via `invoke_tool.ts` pattern). |
| **P1-A** | **DEFECT-001: 91.5% orphan rate** (MSR not rebuilt after L1 chart_facts rebuild) (NEW-1) | Rebuild `bodha_msr_signals` against current build `586f4e9b`. Rebuild `bodha_contradictions`. Establish invariant: MSR rebuild follows every L1 rebuild. |
| **P1-B** | **`registerResources()` never called** | Add `registerResources(server)` call to `platform-mcp/src/server.ts`. |
| **P1-C** | **B.11 not enforced on MCP path** | Wire `invoke_tool.ts` gateway as the MCP tool dispatch chokepoint (already has the hard gate). |
| **P1-D** | **Domain-composite reasoning units absent** (`assess_marriage`, `assess_career`, etc.) | Build composite domain tools after data wounds (P1-A) are healed. |
| **P2-A** | **Bundle-elasticity: verbosity inert** | Implement `response_format`/verbosity branching in handlers (terse/standard/exhaustive). |
| **P2-B** | **MARO not invoked on MCP channel** | Wire `getMcpSurfaceSpec()` into MCP tool registration; wire `resolveNormalization()` into the dispatch path. |
| **P2-C** | **Synergy tools are stubs** (`synergy_cross_layer`, `synergy_pipeline`) | Build real handlers. |
| **P2-D** | **`behavioral_overrides` inert** (zero capabilities set the field) | Either implement per-capability overrides for the highest-value caps, or remove the field from the type system. |
| **P2-E** | **Zero prompts defined** | Define acharya-grade prompts for the major reading entry points (whole-chart, domain, timing). |
| **P3-A** | **Old `platform/src/lib/retrieve/` dead code** (NEW-9) | Delete after confirming zero imports. |
| **P3-B** | **`msr_sql` duplicate in `SURGICAL_TOOLS`** (NEW-7) | Fix the duplicate entry. |
| **P3-C** | **Dual `holistic_bundle` registration** (NEW-8) | Consolidate to one backend; remove the other. |

---

*End of RETRIEVAL_ELEVATION_AUDIT_FINDINGS v1.0 — code+runtime grounded, 2026-06-28.*
*Input: 3-agent parallel audit (retrieval code audit + MCP code audit + live DB checks).*
*§4 lists 9 new findings not present in the Cowork baseline audit.*
