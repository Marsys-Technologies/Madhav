---
canonical_id: RETRIEVAL_MCP_UNIFIED_AUDIT_AND_SYNC_CONTRACT
version: 1.1
status: CURRENT — LIVE-VERIFIED foundation for the parallel retrieval-elevation + MCP-build forks
created: 2026-06-28
author: Cowork (3 parallel code-grounded audits, synthesized) — for native Abhisek Mohanty
classification: unified audit + frozen retrieval↔MCP interface contract
purpose: ground both the retrieval-elevation (built in THIS Cowork session) and the MCP build (handed off to a
  separate conversation) in one shared reality + one frozen seam, so the two forks build in parallel WITHOUT drift.
method: read actual code (registry, MCP server, chat path, portal auth); code wins over docs.
changelog:
  - v1.0 (2026-06-28): Unified audit of retrieval + MCP + the seam. Keystone finding: two disconnected retrieval surfaces. Entitlement-boundary RULED (Option 1, evidence-based). Frozen sync contract defined.
  - v1.1 (2026-06-28): Verified against LIVE code+data by a Claude Code audit (RETRIEVAL_ELEVATION_AUDIT_FINDINGS + MCP_ELEVATION_AUDIT_FINDINGS). All 9 Cowork findings CONFIRMED + 14 new. **Corrections that change priority:** (1) DEFECT-001 orphan rate is REAL — root cause = build-timestamp mismatch (MSR built 2026-06-20, chart_facts rebuilt 2026-06-24, MSR never re-run); the native's "MSR rebuilt" is NOT confirmed by data; an MSR re-run is now a PREREQUISITE to reasoning-unit elevation. (2) NEW P0 LIVE REGRESSION: callPlatformPrimitive 401s because /api/mcp/primitives still requires x-mcp-audience-tier header the client stopped sending (2026-05-28) — the two registry-path tools (mitigation_map, muhurta_finder) are broken; one-line fix. (3) NEW native-contamination bug: kala_temporal.ts:156-341 hardcoded native FORENSIC fallback → non-native charts get Abhisek's data when sidecar down. (4) 31 registered tools (not ~30); bo_2-7 dead code; 17/31 sidecar tools no rate limiting. (5) POSITIVE: MARO profiles already MEASURED v1.1.0; getMcpSurfaceSpec exists ready-to-wire.
---

# UNIFIED AUDIT + FROZEN SYNC CONTRACT — RETRIEVAL ↔ MCP (v1.0)

> Three parallel code-grounded audits (retrieval, MCP, seam) synthesized into one foundation. Both forks —
> the retrieval elevation (this Cowork session) and the MCP build (separate conversation) — build on THIS.
> The §4 sync contract is FROZEN and owned by the retrieval side; the MCP fork adapts to it.

---

## §1 — THE KEYSTONE FINDING (read first; it reframes everything)

**There are TWO disconnected retrieval surfaces, and the rich one is not the one the MCP serves.**

- **The sealed registry** (`platform/src/lib/retrieval/`) — ~75 typed `CapabilityDescriptor`s with the full D1
  contract (archetype, traversal_level, tool_role, drill_children, emits_references, grounds_to, lel_capable),
  a router, a grounding spine, and MARO (4 family profiles). This is what the design docs describe. The chat
  path (`/api/chat/consult`) AND the `/api/mcp/primitives` route consume it (the genuine "single source").
- **The live MCP server** (`platform-mcp/src/server.ts`) — registers ~30 **hand-rolled in-process tools** that
  open their own `pg.Pool` and run raw SQL, **bypassing the registry, the router, MARO, AND the entitlement
  gate**. The MCP channel does not mount the sealed registry.

**Consequence:** nearly every elevated capability (whole-chart-read enforcement, bundle-elasticity, per-model
MARO shaping, channel-agnosticism, the grounding spine) **exists but is unreachable through MCP**. The "is it
ready?" doubt traces entirely to this: the *sealed* system and the *served* system are different systems.

→ **The #1 convergence action (both forks depend on it): the MCP must serve the registry path, and the
in-process tools must be retired/repointed.** This is the keystone both the retrieval elevation and the MCP
build are organized around.

---

## §2 — RETRIEVAL SYSTEM — current state vs elevated goals

| Goal | Verdict | Evidence / gap |
|---|---|---|
| Astrological reasoning-units | PARTIAL | `query_domain_reading` returns pre-computed lens rows + CDLM cells (ingredients), not a reconciled marriage/career verdict. No `assess_marriage`/`assess_career`. |
| Coverage vs question-space | PARTIAL | ~75 caps cover tables; gaps are *judgment* tools (no yoga-activation-by-dasha bridge; no domain-keyed composite verdict). |
| Whole-chart-read enforced | PARTIAL | Router *biases* orient-first; nothing *requires* it; MCP bypasses the router entirely. |
| Contradiction/convergence first-class | PARTIAL code / GAP data | Tools exist (`query_contradictions`, `traverse_chart_graph`, `synergy_cross_layer`) but `bodha_contradictions` = 0 rows; synergy tools are descriptor stubs. |
| Richness (resources/prompts/descriptions) | PARTIAL | Descriptions rich; 9 resources defined; **0 prompts** anywhere. |
| Bundle-elasticity (terse/standard/exhaustive) | GAP | `verbosity_enum` defined in MARO types; **no handler implements `response_format`/verbosity** — router sends `concise`, every handler ignores it. |
| MARO / per-model adaptation | PARTIAL | MARO + 4 profiles real + tested; not invoked by the MCP channel; `behavioral_overrides` defined but set by nobody. |
| Channel-agnostic core | MEETS (registry) but not load-bearing | Registry/router/MARO are channel-clean; MCP doesn't use them, so it's an untested property of an unused path. |

**Two data wounds (block astrological correctness, not retrieval code):**
- `bodha_contradictions` = **0 rows** (writer rebuild pending) → contradiction surface is empty.
- `constituent_facts_array` **91.5% orphan rate** (DEFECT-001 in `query_domain_reading.ts`) → reasoning units
  can't resolve to L1 facts. **NOTE: native reported the MSR was rebuilt — this 91.5% must be re-checked live;
  if still high, the rebuild did not take and is a prerequisite to the reasoning-unit elevation.**

**Top retrieval elevation gaps (priority):** (1) wire MCP→registry [keystone]; (2) build domain reasoning-unit
tools (`assess_*`); (3) implement bundle-elasticity; (4) heal the contradiction + orphan data; (5) add prompts;
(6) make synergy tools real; (7) use or drop `behavioral_overrides`.

---

## §3 — MCP SYSTEM — current state vs elevated (multi-user/portal-equivalent) goals

| Goal | Verdict | Evidence / gap |
|---|---|---|
| Identity (user→portal identity) | PARTIAL | Resolves only a bare `Principal {user_uid, key_id}`; no roles/profile. |
| Chart entitlement | **ABSENT (security)** | **Any valid key reads any chart_id** — no `WHERE owner`/grant check anywhere on the MCP path. |
| Chart selection (list/select) | ABSENT | No `list_my_charts`/`select_chart`/active-chart concept. |
| Session state | STATELESS by design | `sessionIdGenerator: undefined`; no session store. |
| Conversation memory | ABSENT | No durable record; no recall tools. |
| Chart-switch isolation | ABSENT | No detection; statelessness makes it impossible without new state. |
| Multi-client auth | PARTIAL/scaffold | Bearer key works; **OAuth is in-memory Maps, issues `anonymous` tokens, dies on restart, one hardcoded test_client** — not production-real for Claude/ChatGPT/Gemini connectors. |
| Per-model declared profile | ABSENT | Universal surface only. |
| Resources & prompts | PARTIAL/dead | 9 resources defined but **`registerResources()` never called** in server.ts (dead in prod); 0 prompts. |
| Deployment/transport/rate-limit/observability | PARTIAL | Cloud Run `amjis-mcp`, Streamable HTTP (no SSE); **no rate limiting, no real observability**; `/health` self-report stale (says 13 tools/min-1; reality ~30 tools/min-0). |

**Top MCP gaps:** entitlement boundary (security, P0), chart-selection layer, production OAuth (DB-backed +
real identity), register the resources, the session/memory store (reverses D10), per-model profile, rate-limit
+ observability.

---

## §4 — THE FROZEN RETRIEVAL↔MCP SYNC CONTRACT (the linchpin; owned by retrieval, MCP adapts)

This is the seam both forks obey. Frozen; neither side changes it unilaterally; if retrieval must change it,
the change is published back and the MCP fork is notified before it lands.

### §4.1 — The layering (who owns what)
- **Retrieval registry** (`platform/src/lib/retrieval/`) owns: capabilities, the `marsys://` URI scheme,
  `retrieve(plan, params)` execution, chart-data SQL, the router, the grounding spine, MARO. It is
  **chart-agnostic and FROZEN** (principle #14 / DG3) — it takes `chart_id` as a required param, never a
  default, and has **zero entitlement awareness**. It does not know who calls it.
- **Channel adapters** (MCP server; chat engine) own: auth, identity/principal resolution, **entitlement
  enforcement**, session/memory, chart-selection UX, per-model surface declaration, envelope shaping.
- **The single source rule:** both channels invoke the SAME registry capabilities. No channel re-implements
  retrieval or runs its own chart SQL. (This is exactly what the in-process MCP tools violate today.)

### §4.2 — THE ENTITLEMENT-BOUNDARY RULING (evidence-based): **Option 1.**
The per-user chart-access check lives in the **channel/gateway layer, NOT in retrieval.** Rationale (all
code-grounded): the portal already has the centralized helper `authorizeChartAccess`
(`platform/src/lib/auth/authorizeChartAccess.ts` → owner/super_admin = `'all'`, view-grant = `'view'`, else
`'deny'`; 18 callers) AND a built chokepoint `invokeTool` (`platform/src/lib/gateway/invoke_tool.ts`) that does
exactly Option 1: authorize, then call a chart-agnostic executor. The chat path already calls the helper; the
MCP path does not. So Option 1 is already the chosen, partly-built architecture — and it keeps retrieval FROZEN.
**Contract:** every channel MUST call `authorizeChartAccess(principal, chart_id)` and deny before any
chart-keyed `retrieve()`. Retrieval stays chart-agnostic forever.

### §4.3 — What the MCP fork consumes from retrieval (the interface)
- The set of registry **capabilities** (tools/resources/prompts) via the platform seam
  (`/api/mcp/primitives/[tool]` → `getToolByName` → `tool.retrieve`), NOT via in-process SQL.
- The **MARO surface spec** per declared model family (`getMcpSurfaceSpec(family)`) to shape which tools +
  name patterns + verbosity the connecting model sees.
- The capability **contract fields** (archetype/traversal_level/tool_role/drill_children/output_schema) to
  drive umbrella-vs-drill presentation + resources/prompts.
- Bundle-elasticity via the `response_format`/verbosity parameter (once retrieval implements it).

### §4.4 — What the MCP fork must NOT do
- MUST NOT run its own chart SQL or re-implement retrieval (retire the in-process tools).
- MUST NOT push entitlement into retrieval (keep it at the channel boundary).
- MUST NOT bypass the registry/router/MARO (the keystone fix forbids the current bypass).

### §4.5 — Direction of dependency
Retrieval is the foundation; MCP consumes it. On any conflict, **retrieval's contract wins and MCP adapts.**
The chat engine (built last) consumes the SAME contract identically.

---

## §5 — HOW THE TWO FORKS PROCEED IN SYNC

- **This Cowork session (retrieval elevation):** audit→elevate the registry per §2 (reasoning-units, elasticity,
  prompts, whole-chart-read enforcement, heal data wounds, make synergy real), implement the keystone
  registry-serving path the MCP will mount, and implement bundle-elasticity + the MARO surface spec the MCP
  consumes. Keeps the contract (§4) frozen; if it must extend the seam, it publishes the change.
- **The separate MCP conversation:** gets a handoff = the §3 MCP gaps + the §4 FROZEN contract + the full
  multi-user vision. Builds the channel product (identity, entitlement via `authorizeChartAccess`,
  chart-selection, session/memory, production OAuth, per-model declared profile, resources+prompts registration,
  rate-limit+observability) — all over the registry path, never re-implementing retrieval.
- **Sync guarantee:** the only shared surface is §4, it's frozen, and it's owned by retrieval. The two forks
  cannot drift on the thing that matters because the seam is fixed and single-owned.

---

## §6 — CROSS-CUTTING + DATA PREREQUISITES
- **Re-check the 91.5% orphan rate live** (native said MSR was rebuilt) — if still high, healing it is a
  prerequisite to reasoning-unit elevation. The `bodha_contradictions` writer rebuild is similarly a data
  prerequisite to the contradiction surface.
- **Latent auth bug** to fix during MCP work: the primitives route still reads `x-mcp-audience-tier` the client
  no longer sends (a 401 risk), and the MCP principal carries no role for `authorizeChartAccess` — resolve the
  principal→role mapping.
- **Stale self-description**: `/health` + `tool_list.json` are stale — regenerate from the live registration.

*End of RETRIEVAL_MCP_UNIFIED_AUDIT_AND_SYNC_CONTRACT v1.0 — the shared foundation. §4 is the frozen seam both
forks build against.*
