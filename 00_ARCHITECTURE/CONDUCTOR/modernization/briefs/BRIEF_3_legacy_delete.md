---
status: COMPLETE
unit: 3.legacy_delete
wave: 3
title: Delete the flag-gated legacy single-pass pipeline (after cutover holds green)
stream: A
worktree: ../MadhavStreamA
blockedBy: [3.cutover, G5b_onfinish]
on_red: rollback
---

## Context (self-contained)
With the new pipeline the default and G5b green (onFinish parity proven), remove the dead legacy body
(MASTER_PLAN §6-B/G + audit). Hard gate already satisfied: B.11 ported (0b.1) + onFinish parity (3.cutover).

## Scope (delete)
- `platform/src/lib/synthesis/orchestrator.ts`, `single_model_strategy.ts`, and `panel_strategy.ts`
  **(CAREFUL: `panel_strategy.ts` is the legacy single-pass panel — distinct from the ACTIVE
  `synthesis/panel/` directory; do NOT delete the active panel)**.
- The `synthesisRequest` construction + the legacy `else` branch in `consume/route.ts` (route is now a thin
  selector to the agentic pipeline only); the duplicate budget table `tokensFor` (keep `tokensForAdapter`).
- The orphaned `/api/mcp/execute/route.ts` + `callPlatform()` / `callPlatformPlan()` in
  `platform-mcp/src/client.ts` (verify their callers are gone first).
- Remove the now-dead pipeline-selector flag/branch if the selector collapses to one path.

## Acceptance criteria (all automated)
1. Legacy modules deleted; `grep -rn "createOrchestrator\|single_model_strategy\|synthesisRequest\|callPlatformPlan" platform/src platform-mcp/src` returns none (except in `synthesis/panel/` active code).
2. `consume/route.ts` has no legacy branch; full chat test suite + B.11 citation test green.
3. No orphaned imports (madge/grep); build passes.

## must_not_touch
`platform/src/lib/synthesis/panel/**` (ACTIVE panel), `chart_facts`/`l25_*`, `platform/python-sidecar/**`.

## Commit cadence / rollback
Commits: (1) delete legacy trio + route legacy branch, (2) delete /api/mcp/execute + client.ts dead callers,
(3) selector/flag cleanup. Rollback = `git revert` (not a flag flip — legacy is gone). Run only after a green
post-cutover window.
