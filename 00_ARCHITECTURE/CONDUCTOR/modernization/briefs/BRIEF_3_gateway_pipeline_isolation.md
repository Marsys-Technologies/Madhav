---
status: COMPLETE
unit: 3.gateway_pipeline_isolation
wave: 3
title: Tool gateway (B.11 + per-chart authz chokepoint) + isolate the two pipelines
stream: A
worktree: ../MadhavStreamA
blockedBy: [G3_contract, 2a]
on_red: rollback
file_fence: "touches lib/retrieve dispatch + consume/route.ts — serialize after 2a; do not run concurrently with 3.dejudge or 3.tool_asset_recon (shared tool layer)"
---

## Context (self-contained)
Two jobs (MASTER_PLAN §5 + §7.5): build the gateway over the unified contract (2b), and physically isolate
the two interleaved pipelines in `consume/route.ts`.

## Scope
- **Gateway** `platform/src/lib/gateway/`: `search_tools(query|family)` + `invoke_tool(name, params)` over the
  unified contract; **hosts the single B.11 forced-first guarantee** and the **per-chart `authorizeChartAccess`
  chokepoint** (every tool call resolves principal + chart_id + ayanamsha_id, authorizes, then dispatches).
  Resident core ≤ ~12; rest discoverable via search_tools.
- **Pipeline isolation:** `platform/src/lib/pipelines/{single_pass,agentic,shared}/` behind one `QueryPipeline`
  interface; `consume/route.ts` becomes a thin selector. Shared stages (auth, chart resolution, planner, B.11
  floor, persistence, streaming, citation) → `pipelines/shared/`. UI labels (Classic/Claude-style) unchanged.

## Acceptance criteria (all automated)
1. `search_tools`/`invoke_tool` work on both channels; `invoke_tool` calls `authorizeChartAccess` before dispatch.
2. B.11 forced-first enforced via the gateway (test: a query cannot reach a tool without the holistic-read floor).
3. **Golden-transcript:** both pipelines produce byte-identical output before/after extraction (behaviour-preserving).
4. `consume/route.ts` is a thin selector (no inline pipeline bodies); each pipeline module owns its types + tests.

## must_not_touch
`chart_facts`/`l25_*` (2a), `platform/python-sidecar/**`, `platform/src/app/clients/**` (consult_nav),
`platform/src/lib/disclosure/**` (tier_excision).

## Commit cadence / rollback
Commits: (1) gateway + authz chokepoint + B.11-forced, (2) extract shared stages, (3) split single_pass/agentic
+ thin route selector. Rollback = revert; flag-gate the selector so the legacy path stays reachable until G5b.
