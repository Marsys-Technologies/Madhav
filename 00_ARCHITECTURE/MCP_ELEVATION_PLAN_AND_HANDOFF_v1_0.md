---
canonical_id: MCP_ELEVATION_PLAN_AND_HANDOFF
version: 1.0
status: CURRENT — paste into a fresh Cowork conversation to drive the MCP elevation workstream
created: 2026-06-28
author: Cowork (planning) — handoff for the MCP elevation conversation, for native Abhisek Mohanty
classification: MCP elevation plan + complete conversation handoff (the MCP fork)
grounded_in:
  - MCP_ELEVATION_AUDIT_FINDINGS_v1_0.md (Claude Code LIVE audit — MCP side)
  - RETRIEVAL_MCP_UNIFIED_AUDIT_AND_SYNC_CONTRACT_v1_1 (the FROZEN seam this fork obeys — §4)
pairs_with: RETRIEVAL_ELEVATION_PLAN_v1_0 (built in the other Cowork session) — both obey the frozen §4 contract
changelog:
  - v1.0 (2026-06-28): MCP elevation plan + paste-ready handoff. Grounded in the live audit; locked to the frozen sync contract; carries the P0 fixes + the multi-user/portal-equivalent vision.
---

# MCP ELEVATION — PLAN + CONVERSATION HANDOFF (paste this to start the MCP conversation)

> **How to use this.** Paste this whole document as the first message of a new Cowork conversation for the MCP
> elevation workstream. It carries the full inheritance: the project frame, the live-verified MCP state, the
> FROZEN retrieval↔MCP contract this fork must obey, the elevated multi-user vision, the P0 fixes, and the
> phased plan. The retrieval fork is being built in a separate Cowork session; the §A contract keeps the two
> in sync. Cowork plans + briefs; Claude Code in Antigravity implements.

---

## §0 — Project frame (one paragraph)

MARSYS-JIS is an LLM-operated Jyotish instrument. Six layers (L0–L5), ~81 Postgres assets, fronted by a
retrieval system serving TWO channels — an external MCP server and an internal chat engine — across four LLM
families (Anthropic/Gemini/OpenAI/DeepSeek). The retrieval system is sealed (D0–D8) and is being ELEVATED in a
parallel Cowork session (reasoning-unit tools, bundle-elasticity, etc.). THIS workstream elevates the MCP into
a multi-user, multi-chart, portal-equivalent product. Governance: heavy + deliberate (reverse-citation gate on
deletions, prod-only data plane, chart-agnostic principle #14). Cowork plans + briefs; Claude Code implements.

## §A — THE FROZEN SYNC CONTRACT (obey this; it keeps MCP in sync with retrieval)

From `RETRIEVAL_MCP_UNIFIED_AUDIT_AND_SYNC_CONTRACT_v1_1 §4`. This is LAW for the MCP fork:
1. **Retrieval is chart-agnostic + FROZEN.** It takes `chart_id` as a required param, never a default, and has
   ZERO entitlement awareness. The MCP must NOT push entitlement into retrieval.
2. **Entitlement lives at the CHANNEL (Option 1, ruled).** Every chart-scoped MCP call MUST call
   `authorizeChartAccess(principal, chart_id)` (the portal's existing helper:
   `platform/src/lib/auth/authorizeChartAccess.ts` → owner/super_admin='all', view-grant='view', else 'deny')
   and deny BEFORE any chart-keyed `retrieve()`. The built chokepoint `invokeTool`
   (`platform/src/lib/gateway/invoke_tool.ts`) is the Option-1 pattern to follow.
3. **Single source.** Both channels invoke the SAME registry capabilities via the platform seam
   (`/api/mcp/primitives/[tool]` → `getToolByName` → `tool.retrieve`). The MCP must NOT run its own chart SQL.
4. **MCP consumes from retrieval:** the registry capabilities; `getMcpSurfaceSpec(family)` for per-model
   surfaces; the `response_format` (minimal/standard/detailed) elasticity parameter; the contract fields
   (archetype/traversal_level/tool_role/drill_children) for umbrella-vs-drill presentation.
5. **Direction of dependency:** retrieval wins on conflict; MCP adapts. If the MCP needs a seam change, it is
   requested from the retrieval fork (which owns the contract), not made unilaterally.

## §B — LIVE-VERIFIED MCP STATE (from the Claude Code audit — what you inherit)

**Security/correctness P0s (fix first):**
- **P0-1 — `callPlatformPrimitive` is broken (live regression).** `/api/mcp/primitives` still requires the
  `x-mcp-audience-tier` header the client stopped sending (2026-05-28 tier excision). The two tools that
  CORRECTLY use the registry (`mitigation_map`, `muhurta_finder`) **401 on every call**. **One-line fix:**
  remove `audienceTierHeader` from the `if (!userUid || !audienceTierHeader || !keyId)` guard in the route.
  *This unblocks the keystone (registry-served MCP) for both forks — do it first.*
- **P0-2 — No chart entitlement (security hole).** Any valid key can read ANY chart_id. No `authorizeChartAccess`
  on the MCP path. Per §A.2, wire it at the channel.
- **P0-3 — Native contamination.** `kala_temporal.ts:156–341` hardcodes native FORENSIC fallback → non-native
  charts silently get Abhisek's dasha/obstruction data when the sidecar is down. (Also in the retrieval fork's
  R1; coordinate so it's fixed once.)

**Elevated-vision gaps (the build):**
- Identity = bare uid, no role; chart entitlement ABSENT; chart-selection ABSENT; session state STATELESS;
  conversation memory ABSENT; chart-switch isolation ABSENT.
- OAuth is in-memory scaffold (issues `anonymous` tokens, dies on restart, one hardcoded test_client) — NOT
  production-real for Claude/ChatGPT/Gemini connectors.
- Per-model declared profile ABSENT (universal surface only) — BUT `getMcpSurfaceSpec()` exists ready to wire,
  and MARO profiles are already MEASURED v1.1.0 (good news — exposure not build).
- 31 registered tools (health stale-reports 13); `bo_2-7` dead code; 17/31 sidecar tools no rate limiting;
  resources DEFINED but `registerResources()` never called (dead in prod); zero prompts.
- Deployed Cloud Run `amjis-mcp`, Streamable HTTP (no SSE); verify deployed revision vs main.

**Shared data gate (with retrieval):** the MSR/grounding seal is **reported but pending live confirmation** —
the retrieval fork's R0 confirms the orphan rate is healthy. Reasoning-unit quality the MCP serves depends on
it; not an MCP build blocker, but the MCP go-live experience depends on it being green.

## §C — THE ELEVATED MCP VISION (what to build)

A portal-equivalent experience over MCP: a user authenticates → resolves to their portal identity → can choose
among the charts they're ENTITLED to → query with portal-grade richness → with session continuity, conversation
memory, chart-switch advisory, and a surface adapted to their specific LLM. Multi-client (Claude first; provision
ChatGPT/Gemini/DeepSeek). (Full brainstorm + native rulings are in the conversation that produced this; the
phased plan below encodes them.)

## §D — THE PHASED MCP ELEVATION PLAN

### PHASE M0 — P0 FIXES (do first; unblock + secure)
- M0.1 — Fix `callPlatformPrimitive` 401 (P0-1, one-line).
- M0.2 — Wire `authorizeChartAccess` entitlement gate on every chart-scoped MCP path (P0-2) per §A.2.
- M0.3 — Fix `kala_temporal` native fallback contamination (P0-3; coordinate with retrieval R1).
- M0.4 — Fix the latent role/header bugs (MCP principal carries no role for authorizeChartAccess; stale
  x-mcp-audience-tier read; regenerate stale /health + tool_list.json).
- Acceptance: registry-path tools return 200; no key can read an unentitled chart (test ≥2 users × 2 charts);
  no native data reachable by a non-native chart.

### PHASE M1 — IDENTITY + ENTITLEMENT FOUNDATION
- M1.1 — Identity core: MCP user → full portal identity (uid + role), one resolver all auth front-doors map to.
- M1.2 — Chart entitlement resolution reusing the portal model (owner + view-grants); `getEntitledCharts(uid)`.
- M1.3 — Entitlement enforced on every call (built on M0.2).
- Acceptance: a user's reachable chart set == their portal entitlement; cross-user isolation proven.

### PHASE M2 — CHART SELECTION (the "like the portal" experience)
- M2.1 — `list_my_charts` tool (names, not raw UUIDs).
- M2.2 — `select_chart` / active-chart mechanism (carried as param + session record).
- M2.3 — Charts as MCP resources (native chart-picker UI on compatible clients).
- Acceptance: a user can list + choose among entitled charts; subsequent calls operate on the chosen chart.

### PHASE M3 — SESSION STATE + MEMORY
- M3.1 — Session state store (per-user/per-session active chart + state). *(Store location: assess existing
  conversation infra first; recommend in this fork's design — likely a new MCP session table.)*
- M3.2 — Conversation memory (durable, per-user/per-chart) + `recall_session`/`list_my_sessions` tools.
- M3.3 — Per-chart session continuity.
- Acceptance: a returning user can resume; memory scoped per (user × chart).

### PHASE M4 — CHART-SWITCH ISOLATION (advisory, ruled)
- M4.1 — Detect active-chart change; return a clear "start a new conversation to avoid mixing charts" advisory
  (advisory only per native ruling — warns, does not hard-block).
- Acceptance: switching charts surfaces the advisory.

### PHASE M5 — MULTI-CLIENT AUTH (Claude first; provision the rest)
- M5.1 — Auth architecture: one identity core, many front-doors.
- M5.2 — Production OAuth: DB-backed token/code/client store (replace in-memory Maps), real Firebase identity
  binding (fix the `anonymous` token bug), dynamic client registration.
- M5.3 — Claude custom-connector path end-to-end.
- M5.4 — Provision ChatGPT (connector/OAuth), Gemini (Remote MCP / Streamable HTTP, no `-` in names), DeepSeek
  (no MCP → plain-backend path). Designed now, built as taken up.
- Acceptance: Claude connector works end-to-end with real identity + entitlement; OAuth survives restart + multi-instance.

### PHASE M6 — PER-MODEL DECLARED PROFILE
- M6.1 — Declaration mechanism (client declares model family — config/OAuth-scope/per-key/client-hint; decide in design).
- M6.2 — Consume `getMcpSurfaceSpec(family)` (exists) → serve declared→profiled / undeclared→universal-best.
- Acceptance: a declared Claude connector gets the Claude-profiled surface; undeclared gets universal-best.

### PHASE M7 — RICHNESS (resources + prompts) — consumes retrieval R5
- M7.1 — Register the resources (call `registerResources()` — currently dead) + the chart catalog/vocab/schema.
- M7.2 — Expose the retrieval fork's guided-reading prompts (R5.2) as MCP prompts.
- Acceptance: resources served live; guided-reading prompts available.

### PHASE M8 — PRODUCTION-GRADE + PROVE
- M8.1 — Rate limiting (17/31 tools currently none) + observability (tracing in the request path).
- M8.2 — Deployment + revision verification (deployed == sealed main).
- M8.3 — End-to-end connector test: real Claude, multiple users × charts, verifying access control + selection
  + isolation + no native/cross-chart bleed.
- M8.4 — Completeness audit (live): every asset reachable through the connector.
- Acceptance: production-grade + the end-state experience verified live.

## §E — SYNC POINTS WITH THE RETRIEVAL FORK (the frozen seam in practice)
- **P0-1 (the 401 fix)** is MCP-owned (M0.1) but the retrieval keystone (R2: registry-served surface) depends
  on it — do it first and tell the retrieval fork it's green.
- **kala_temporal contamination** appears in both (M0.3 / retrieval R1) — fix once, coordinate.
- **`getMcpSurfaceSpec`** (M6) + **`response_format` elasticity** (consumes retrieval R4.1) are seam outputs the
  retrieval fork owns — consume, don't redefine.
- **Entitlement stays at the channel** (M0.2/M1) — never pushed into retrieval (keeps it frozen).
- **The MSR/grounding seal** (retrieval R0) gates the *quality* of what MCP serves — confirm green before go-live.

## §F — EXECUTION MODEL
Per-phase Claude Code briefs (M0…M8), worktree-isolated, reverse-citation gate on every removal, prod-verify
after merge, chart-agnostic gate green throughout. M0 first (P0 fixes — security + unblock). M1→M2→M3 are the
core portal-equivalent experience; M5 (OAuth) can parallelize with M2/M3. Consider the autonomous-swarm charter
pattern for the build if desired.

## §G — FIRST ACTIONS FOR THE NEW CONVERSATION
1. Read the two audit findings + the frozen contract (§A) + this plan.
2. Confirm the live state still matches (re-grep the P0s).
3. Author the M0 Claude Code brief (P0 fixes) first — it's security + it unblocks the keystone for both forks.
4. Proceed through M1→M8, coordinating the §E seam points with the retrieval fork.

*End of MCP_ELEVATION_PLAN_AND_HANDOFF v1.0 — paste into a fresh Cowork conversation. Obeys the frozen §A
contract; pairs with the retrieval elevation plan.*
