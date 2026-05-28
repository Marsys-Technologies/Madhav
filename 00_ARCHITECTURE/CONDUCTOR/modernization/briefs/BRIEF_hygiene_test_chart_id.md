---
status: COMPLETE
unit: hygiene.test_chart_id
wave: 3-hygiene
title: Fix the 3 retrieve test files broken by 2a's NATIVE_CHART_ID removal
stream: C
worktree: ../MadhavStreamC
blockedBy: [2a]
on_red: rollback
priority: high   # main currently has 20 failing tests — fix early in the batch
---

## Context (self-contained)
2a.7 removed the `NATIVE_CHART_ID` / `DEFAULT_CHART_ID` defaults from the retrieval tools (correct — set G4).
That broke 3 retrieve test files (20 failures) that still assumed the single-native default. `main` currently
has failing tests — restore green by threading `chart_id` through the fixtures.

## Scope
- Identify the 3 broken test files under `platform/src/lib/retrieve/__tests__/` (20 failures from 2a.7).
- Thread an explicit `chart_id` (the native chart's id) + `ayanamsha_id` where the test exercises an
  ayanamsha-dependent tool, into the test fixtures/calls. Do NOT reintroduce `NATIVE_CHART_ID`.
- Pure test fix — no source behaviour change.

## Acceptance criteria (all automated)
1. The 3 files pass; full `npx vitest run platform/src/lib/retrieve` suite green (0 failures).
2. `grep -rn "NATIVE_CHART_ID\|DEFAULT_CHART_ID" platform/src/lib/retrieve` returns none (G4 not regressed).
3. No retrieval source file modified (tests only).

## must_not_touch
Retrieval SOURCE files (2a/3.dejudge own them), `platform/python-sidecar/**`, everything outside `lib/retrieve/__tests__/`.

## Commit cadence / rollback
One commit: "hygiene: thread chart_id in 3 retrieve test files (fix 20 failures from 2a.7)". Rollback = revert.
