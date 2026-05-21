---
artifact: CLAUDECODE_BRIEF_MCP_3_S1_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: PENDING
authored_by: Claude Code sub-agent (MCP-0-AUTHOR)
authored_at: 2026-05-21
session_id: MCP-3-S1
session_name: MCP-3-S1 — 10 surgical primitives + /api/mcp/primitives/[tool] dispatcher
executor: Claude Code sub-agent (general-purpose, spawned by MCP Conductor)
execution_mode: single autonomous session, --dangerously-skip-permissions
worktree:
  name: MadhavMCP
  branch: feature/mcp-server
  base: main
  path_absolute: /Users/Dev/Vibe-Coding/Apps/MadhavMCP
governing_plan: 00_ARCHITECTURE/BRIEFS/MCP_BRIEF_v1_0.md
reference_brief: 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCP_1_S1_v1_0.md
predecessor_session: MCP-2-S2 (tool descriptions + resources)
next_session_anticipated: MCP-3-S2 (read_asset, get_trace, list_recent_queries + rate limiting)
---

# CLAUDECODE_BRIEF — MCP-3-S1
## 10 surgical primitives + /api/mcp/primitives/[tool] dispatcher

---

## §0 — How to start this session

You are a sub-agent spawned by the MCP Conductor. Your context is fresh.
You are in the MadhavMCP worktree at `/Users/Dev/Vibe-Coding/Apps/MadhavMCP`
on branch `feature/mcp-server`. The Conductor has already pasted your
session prompt; you are now reading this brief.

This session implements the **Tier 3 surgical primitives**: a server-side
dispatcher on the platform (`/api/mcp/primitives/[tool]/route.ts`) that
exposes 10 of the existing 30 retrieval tools as MCP-callable endpoints,
and 10 corresponding MCP tool wrappers in `platform-mcp/src/tools/`.

Surgical primitives bypass the planner and B.11 floor. They are tagged
`surgical: true` in the epistemics block. This session works in two halves:
platform side (dispatcher + whitelist registry + tests), then MCP side
(10 tool wrappers with §4.6 descriptions).

---

## §1 — Session identity

| Field | Value |
|---|---|
| Session ID | MCP-3-S1 |
| Branch | `feature/mcp-server` |
| Worktree path | `/Users/Dev/Vibe-Coding/Apps/MadhavMCP` |
| Execution mode | Single autonomous session, `--dangerously-skip-permissions` |
| Predecessor | MCP-2-S2 (tool descriptions + resources complete) |
| Anticipated next | MCP-3-S2 (read_asset + get_trace + rate limiting) |

---

## §2 — Mandatory reads at session open (in order)

1. `CLAUDE.md` (§C mandatory list — full read)
2. `00_ARCHITECTURE/BRIEFS/MCP_BRIEF_v1_0.md` — **focus on §4.1 Tier 3
   (the 10 primitives and their underlying retrieval tools), §5.3 (data
   flow for primitives), §7.3 (Phase MCP-3 scope and acceptance criteria)**
3. `platform/src/lib/retrieve/index.ts` — read to understand which
   retrieval tools are available and their function signatures; the 10
   primitives must map to real tool names in this index
4. `platform/src/app/api/mcp/execute/route.ts` — read to understand the
   `getTool(toolName)` and `tool.execute()` pattern you will replicate in
   the primitives dispatcher
5. `platform/src/lib/mcp/auth.ts` — read to understand how to call
   `validateMcpKey` in the dispatcher handler
6. `platform/src/lib/mcp/epistemics.ts` — read to understand how to build
   a `surgical: true` epistemics block

Skim only:
- One or two existing retrieval tool implementations under
  `platform/src/lib/retrieve/` to understand the `tool.execute()` calling
  convention and return shape

---

## §3 — Scope (5 items — execute in order; commit after each)

### Item 1 — Primitives whitelist registry (`platform/src/lib/mcp/primitives_registry.ts`)

**What:** Author `platform/src/lib/mcp/primitives_registry.ts` that exports:

```typescript
export const SURGICAL_TOOLS = [
  'chart_facts_query',
  'msr_sql',
  'query_dasha_periods',
  'query_panchanga',
  'query_ephemeris',
  'query_transit_event',
  'lel_query',
  'vector_search',
  'cgm_graph_walk',
  'multi_school_signal_lookup',
] as const;

export type SurgicalToolName = typeof SURGICAL_TOOLS[number];

// MCP-facing names map to underlying retrieval tool names
export const MCP_TO_RETRIEVAL_TOOL: Record<string, SurgicalToolName> = {
  'query_chart_facts':    'chart_facts_query',
  'query_signals':        'msr_sql',
  'query_dasha_periods':  'query_dasha_periods',
  'query_panchanga':      'query_panchanga',
  'query_ephemeris':      'query_ephemeris',
  'query_transit_event':  'query_transit_event',
  'lel_query':            'lel_query',
  'vector_search':        'vector_search',
  'get_cgm_subgraph':     'cgm_graph_walk',
  'cross_school_lookup':  'multi_school_signal_lookup',
};

export function isAllowedSurgicalTool(mcpToolName: string): mcpToolName is keyof typeof MCP_TO_RETRIEVAL_TOOL {
  return mcpToolName in MCP_TO_RETRIEVAL_TOOL;
}
```

**AC.MCP_3_S1.1:** `primitives_registry.ts` exports all three items; maps
all 10 MCP-facing names to their underlying retrieval tool names; includes
the `isAllowedSurgicalTool` guard; `npx tsc --noEmit` passes in `platform/`.

**Why:** Single source of truth for the surgical whitelist. The dispatcher
calls `isAllowedSurgicalTool` to reject tool names not in the whitelist
with a `{ok: false, error: {class: "validation"}}` envelope. This ensures
MCP cannot call internal tools not intended for external exposure.

Commit: `feat(mcp): MCP-3-S1 item 1 — primitives_registry.ts whitelist`

---

### Item 2 — Primitives dispatcher (`platform/src/app/api/mcp/primitives/[tool]/route.ts`)

**What:** Author `platform/src/app/api/mcp/primitives/[tool]/route.ts`
(Next.js dynamic route) — a POST handler that:

1. Validates the service-to-service identity token (same pattern as
   `/api/mcp/execute`).
2. Reads `X-MCP-User`, `X-MCP-Audience-Tier`, `X-MCP-Key-Id` headers.
3. Reads `params.tool` from the URL segment.
4. Calls `isAllowedSurgicalTool(params.tool)`. If false → returns
   `buildErrorEnvelope({error_class: "validation", message: "Tool not in
   surgical whitelist: " + params.tool, remediation: "Use ask_madhav for
   full-pipeline queries."})` with HTTP 400.
5. Calls `getTool(MCP_TO_RETRIEVAL_TOOL[params.tool])` to get the retrieval
   tool instance.
6. Calls `tool.execute({ queryPlan: {audience_tier}, plannerParams: body.params })`.
7. Builds a trace step entry tagged `{source: "mcp_primitive", surgical: true}`.
8. Returns `buildEnvelope({ ok: true, trace_id, audience_tier, result: toolResult,
   epistemics: buildEpistemicsBlock({ surgical: true, confidence_band: "high",
   horizon_days: null, falsifier: null }) })`.

Error handling: any exception in `tool.execute()` returns
`buildErrorEnvelope({error_class: "orchestrator_error", message: err.message})`.

**AC.MCP_3_S1.2:** Dispatcher file exists at the correct path; handles
whitelist check; calls `getTool` + `tool.execute`; stamps `surgical: true`
in epistemics; integration test (Item 4) covers auth-fail, whitelist-fail,
happy-path flows; `npx tsc --noEmit` passes.

**Why:** This is the server-side entry point for all 10 primitives. A
single dispatcher with a whitelist is more maintainable than 10 separate
route files and eliminates the risk of accidentally exposing non-whitelisted
tools.

Commit: `feat(mcp): MCP-3-S1 item 2 — /api/mcp/primitives/[tool] dispatcher`

---

### Item 3 — 10 MCP tool wrappers (`platform-mcp/src/tools/`)

**What:** Author one TypeScript file per primitive under `platform-mcp/src/tools/`.
Each file:
- Registers the tool with a §4.6-standard description (≥100 words, all 5
  blocks — "What it does", "When to prefer", "Input shape hints", "Output
  shape preview", "Inline example").
- Defines an appropriate JSON input schema.
- In the handler: calls `callPlatformPrimitive(mcpToolName, params, principal)`.
- Exports `register<ToolName>(server: McpServer, getPrincipal: () => Principal)`.

The 10 files and their key schema properties:

**`query_chart_facts.ts`**
- Input: `{ category: string, planet?: string, house?: number, as_of_date?: string, limit?: number }`
- Description focus: 795-row parametric chart-fact lookup; use for single fact
  questions (shadbala, dignity, nakshatra, aspect) without synthesis overhead.

**`query_signals.ts`**
- Input: `{ domain?: string, planet?: string, dasha_lord?: string, min_confidence?: number, forward_looking?: boolean, limit?: number }`
- Description focus: MSR signal corpus (499+ signals); prefer over ask_madhav
  when you need raw signal data rather than synthesized prose.

**`query_dasha_periods.ts`**
- Input: `{ at?: string, range?: { start: string, end: string }, system?: string }`
- Description focus: dasha schedule lookup; surgical for "what dasha is active
  on date X?" without running a full synthesis.

**`query_panchanga.ts`**
- Input: `{ date: string, observer?: { lat?: number, lon?: number } }`
- Description focus: daily panchang (5 limbs, sunrise-anchored); returns tithi,
  vara, nakshatra, yoga, karana, hora, choghadiya, muhurat windows.

**`query_ephemeris.ts`**
- Input: `{ planet: string, date_range: { start: string, end: string } }`
- Description focus: date-indexed planetary position lookup from the ephemeris
  table; use for exact degree / sign transit questions.

**`query_transit_event.ts`**
- Input: `{ planet: string, target: string, date_range: { start: string, end: string } }`
- Description focus: transit event search ("when does Saturn enter Aquarius?");
  returns the exact date(s) within the range.

**`lel_query.ts`**
- Input: `{ category?: string, date_range?: { start: string, end: string }, min_significance?: number }`
- Description focus: Life Event Log ground-truth retrieval; 36 events + 5
  period summaries + 6 chronic patterns with confidence scores.

**`vector_search.ts`**
- Input: `{ text: string, doc_type?: string[], top_k?: number }`
- Description focus: semantic search over RAG chunks via Vertex AI 768-dim
  embeddings; use when you need "documents similar to X" rather than a
  structured query.

**`get_cgm_subgraph.ts`**
- Input: `{ node_id: string, hops?: number, edge_types?: string[] }`
- Description focus: CGM topology traversal; returns a subgraph of the
  Cross-Domain Linkage Matrix up to N hops from the starting node.

**`cross_school_lookup.ts`**
- Input: `{ claim: string, schools?: string[] }`
- Description focus: cross-school convergence on an astrological claim;
  checks Parashara, Jaimini, KP, Tajaka positions and returns where they
  agree, disagree, or are silent.

Update `platform-mcp/src/server.ts` to import and call all 10
`register<ToolName>` functions alongside the existing 3.

**AC.MCP_3_S1.3:** All 10 files exist; each carries a §4.6-standard
description (verifiable by grep for "What it does" and "When to prefer"
in each file); each registers with an appropriate JSON schema; `server.ts`
calls all 10 register functions; `npx tsc --noEmit` passes in `platform-mcp/`.

**Why:** 10 surgical primitives are the Tier 3 surface of the MCP tool
taxonomy. Each must have a high-quality description so Claude selects the
right tool without falling back to `ask_madhav` for single-fact queries.

Commit: `feat(mcp): MCP-3-S1 item 3 — 10 surgical primitive tool wrappers in platform-mcp/src/tools/`

---

### Item 4 — Jest tests for dispatcher

**What:** Author `platform/src/lib/__tests__/mcp/primitives.test.ts`
covering:
1. **Auth test**: request without `X-MCP-User` header → HTTP 401 (mock
   service-to-service token check)
2. **Whitelist enforcement**: POST to `/api/mcp/primitives/pattern_register`
   (not in whitelist) → `{ok: false, error: {class: "validation"}}` with
   HTTP 400
3. **Surgical flag**: happy-path call to whitelisted tool → response has
   `epistemics.surgical === true`
4. **Trace step log**: happy-path call → trace step written with
   `source: "mcp_primitive"` (verify via mock or spy on the trace logger)
5. **All 10 tools reachable**: for each tool in `SURGICAL_TOOLS`, verify
   `isAllowedSurgicalTool(MCP_TOOL_NAME)` returns true (unit test, no HTTP)

Minimum: ≥5 tests. Prefer Jest mocks for `getTool` to avoid needing a live
database connection.

**AC.MCP_3_S1.4:** Test file exists; all tests pass (`npx jest
--testPathPattern="mcp/primitives" --passWithNoTests`); ≥5 tests.

**Why:** The whitelist enforcement test is security-critical — it proves
non-whitelisted tools cannot be called via the MCP primitive path. The
surgical flag test proves the governance rule (G1 per MCP_BRIEF §6) is
implemented.

Commit: `test(mcp): MCP-3-S1 item 4 — primitives dispatcher tests (auth, whitelist, surgical flag)`

---

### Item 5 — TypeScript + Jest gate

**What:** Run the full gate command from `session_queue_MCP.yaml` MCP-3-S1
and confirm it exits 0:

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavMCP/platform &&
test -f src/app/api/mcp/primitives/[tool]/route.ts &&
test -f src/lib/mcp/primitives_registry.ts &&
npx tsc --noEmit &&
npx jest --testPathPattern="mcp/primitives" --passWithNoTests &&
cd ../platform-mcp &&
for t in query_chart_facts query_signals query_dasha_periods query_panchanga \
         query_ephemeris query_transit_event lel_query vector_search \
         get_cgm_subgraph cross_school_lookup; do
  test -f "src/tools/${t}.ts" || { echo "FAIL: ${t}.ts missing"; exit 1; }
done &&
npx tsc --noEmit
```

Fix any issues before claiming PASS.

**AC.MCP_3_S1.5:** Full gate command exits 0; all 10 tool files present;
both `platform/` and `platform-mcp/` TypeScript clean.

**Why:** Gate command is what the Conductor checks before marking this
session complete. It must pass before FINAL_SUMMARY is emitted.

Commit: `chore(mcp): MCP-3-S1 item 5 — tsc + jest gate passes`

---

## §4 — Session-open handshake

You are a Conductor sub-agent. State briefly at start:

"MCP-3-S1 opening. Will implement primitives_registry.ts whitelist,
/api/mcp/primitives/[tool] dispatcher, 10 MCP tool wrappers with §4.6
descriptions, and dispatcher Jest tests. 5 scope items. Will NOT modify
any existing retrieval tools in platform/src/lib/retrieve/."

---

## §5 — Scope constraints

### may_touch

```
platform/src/app/api/mcp/primitives/[tool]/route.ts      # CREATE
platform/src/lib/mcp/primitives_registry.ts              # CREATE
platform/src/lib/__tests__/mcp/primitives.test.ts        # CREATE
platform-mcp/src/tools/query_chart_facts.ts              # CREATE
platform-mcp/src/tools/query_signals.ts                  # CREATE
platform-mcp/src/tools/query_dasha_periods.ts            # CREATE
platform-mcp/src/tools/query_panchanga.ts                # CREATE
platform-mcp/src/tools/query_ephemeris.ts                # CREATE
platform-mcp/src/tools/query_transit_event.ts            # CREATE
platform-mcp/src/tools/lel_query.ts                      # CREATE
platform-mcp/src/tools/vector_search.ts                  # CREATE
platform-mcp/src/tools/get_cgm_subgraph.ts               # CREATE
platform-mcp/src/tools/cross_school_lookup.ts            # CREATE
platform-mcp/src/server.ts                               # UPDATE — import + call 10 new register functions
00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCP_3_S1_v1_0.md  # status flip PENDING → COMPLETE
```

### must_not_touch

```
platform/src/lib/retrieve/**                             # existing tools wrapped, never modified
platform/src/lib/pipeline/**                             # planner unchanged
platform/src/app/api/chat/consume/**                     # orchestrator unchanged
platform/src/app/api/mcp/execute/**                      # MCP-1-S1 endpoint unchanged
platform/src/lib/mcp/auth.ts                             # MCP-1-S1 auth unchanged
platform/src/lib/mcp/epistemics.ts                       # MCP-1-S1 builder unchanged
platform-mcp/src/tools/ask_madhav.ts                     # MCP-2-S2 descriptions unchanged
platform-mcp/src/tools/plan_query.ts                     # MCP-2-S2 descriptions unchanged
platform-mcp/src/tools/execute_plan.ts                   # MCP-2-S2 descriptions unchanged
platform-mcp/src/client.ts                               # MCP-2-S1 client unchanged
platform-mcp/resources/**                                # MCP-2-S2 resources unchanged
01_FACTS_LAYER/**                                        # L1 sealed
025_HOLISTIC_SYNTHESIS/**                                # L2.5 sealed
00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md                   # sealed
00_ARCHITECTURE/CAPABILITY_MANIFEST.json                 # not touched in this session
CLAUDE.md                                               # §E update is post-workstream-close
```

### Commit cadence

Commit after each scope item with format:

```
<type>(mcp): MCP-3-S1 item <N> — <one-line summary>

<2-3 line description>
Acceptance criterion: AC.MCP_3_S1.<N>
```

---

## §6 — Session-close checklist (FINAL_SUMMARY)

After all 5 scope items are completed and the gate command passes, emit:

```
---FINAL_SUMMARY---
session_id: MCP-3-S1
status: PASS | HALT_NEEDS_HUMAN
commits:
  - <sha_item_1>
  - <sha_item_2>
  - <sha_item_3>
  - <sha_item_4>
  - <sha_item_5>
scope_items_completed:
  - AC.MCP_3_S1.1   # primitives_registry.ts
  - AC.MCP_3_S1.2   # /api/mcp/primitives/[tool] dispatcher
  - AC.MCP_3_S1.3   # 10 MCP tool wrappers
  - AC.MCP_3_S1.4   # Jest tests (auth, whitelist, surgical flag)
  - AC.MCP_3_S1.5   # tsc + Jest gate passes
scope_items_failed: []
gate_command_runs:
  - name: mcp_3_s1_primitives_gate
    result: PASS | FAIL
notes_for_orchestrator: >
  10 surgical primitives wired: dispatcher + whitelist registry on platform,
  10 tool wrappers with §4.6 descriptions on platform-mcp. server.ts
  updated to register all 13 tools (3 Tier-1/2 from MCP-2-S1 + 10 new).
  Next session: MCP-3-S2 (read_asset, get_trace, list_recent_queries +
  per-key rate limiting).
human_decision_needed: >
  <empty if PASS>
---END_FINAL_SUMMARY---
```

---

*End of CLAUDECODE_BRIEF_MCP_3_S1_v1_0.md.*
