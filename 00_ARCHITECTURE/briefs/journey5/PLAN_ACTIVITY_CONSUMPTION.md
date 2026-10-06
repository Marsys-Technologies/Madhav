---
title: Journey5 Activity and Consumption
version: 1.1
status: DEPLOYED_READ_ONLY_VERIFIED
---
# Activity and Consumption Implementation Plan

**Goal:** Two personal views sharing owner ledger and filter contract.
> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement task-by-task.

**Architecture:** Reuse the accepted Journey shell, exact Console default and owner-scoped metering; add bounded typed account persistence. Keep personal AI separate from restricted operator diagnostics.
**Tech Stack:** Next.js/React, TypeScript, PostgreSQL, Firebase Auth, Vitest.
**Spec:** RECONCILIATION.md and the owner-authorized delivery sequence.

## Global Constraints
All constraints/review-focus cases in DELIVERY_PLAN.md apply. Claude Design precedes screen implementation; source-backed contracts qualify prototype claims.

## Review Focus
Owner isolation, concurrent writes, explicit choices, truthful unknowns and failures are tested below.

### Task 1: Scope and routes

**Files:** platform/src/app/account/ai-cockpit/{observatory,consumption}/page.tsx; platform/src/components/observatory/{ObservatoryScope,ObservatoryDashboard}.tsx; platform/src/components/account/PersonalActivity.tsx; platform/src/app/usage/page.tsx; platform/src/lib/metering/queries.ts
**Interfaces:** Account routes force admin=false including superadmin; /api/usage derives uid. Canonical from/to/channel/provider/model/purpose plus connection/chart only where recorded. Same URL scope bothviews. Usage alias preservesquery. Admin Observatory remains restricted separately.

- [x] Write meaningful regression coverage in `platform/tests/account/activity-filters.test.ts and personal-activity.test.tsx:owner cannot spoofotheruid, invaliddates/bounds, aliases preservefilters, personaladmin noportal userselector, identicalallqueryfilters.`
- Initial per-task RED proof is not claimed beyond retained receipts; see execution receipt below.
- [x] Implement the named contract and corresponding Claude Design screen.
- [x] Run focused tests and relevant regressions; require PASS.
- [x] Inspect desktop/mobile/keyboard flow and record result.
- [x] Commit scoped changes after required quality checks; master plan governs release.

### Task 2: Breakdown and drilldown

**Files:** platform/src/lib/metering/queries.ts; platform/src/components/observatory/ObservatoryDashboard.tsx; platform/src/components/account/PersonalActivity.tsx
**Interfaces:** API/CLI→connection→model from same events with unknown bucket and aggregator/underlyingmodel when recorded. Label bars/healthline axes units; missinglatency null notzero. Keep conversation→turn→attempt detail/pagination, receipt/estimate/unpriced/subscription distinctions; no globalMCPhealth personal.

- [x] Write meaningful regression coverage in `platform/tests/account/activity-database.test.ts and consumption-evidence.test.tsx:summarycalls equals breakdown includingunknown, status sum, datefilters applyall, nullcost/usage vs realzero, stale response canceled, ownscoped pagination/details.`
- Initial per-task RED proof is not claimed beyond retained receipts; see execution receipt below.
- [x] Implement the named contract and corresponding Claude Design screen.
- [x] Run focused tests and relevant regressions; require PASS.
- [x] Inspect desktop/mobile/keyboard flow and record result.
- [x] Commit scoped changes after required quality checks; master plan governs release.

Changelog: v1.0 defines testable deliverables, interfaces and evidence.

## Execution receipt

Implemented and protected-merged in PR3197 as2c117ba1. Actual coverage: [CHECKS.json](CHECKS.json), [independent review and repair](REVIEW_AND_VERIFICATION.md), [implementation](IMPLEMENTATION.md). The named test files above reconcile the original planning placeholders to delivered tests. Final focused qualification:17files/76tests; full qualification:15,774passing tests, types/build pass, lint0errors. Source/prototype normal-state inspection covers all nine pages320/390/1440; source replay covers shared scope, persona/pin/depth defaults and keyboard drawer dismissal. These are scoped checks, not every possible keyboard/error state.

Retained initial activity RED receipts show missing-module failures before implementation. Retained independent-review corrections show10behavior failures before repair and21passes afterward; initial per-task RED runs for every other block are not independently asserted. Real password/provider/account mutation acceptance is separate; automatic deployment37415721436 and live read-only verification are recorded by [RELEASE.md](RELEASE.md).

Changelog: v1.1 reconciles actual paths, completed execution and retained evidence limits; original v1.0 remains in Git history.
