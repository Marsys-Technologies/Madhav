---
title: Journey5 Activity and Consumption
version: 1.0
status: PLANNED
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

**Files:** platform/src/app/account/ai-cockpit/{observatory,consumption}/page.tsx; platform/src/components/observatory/{ObservatoryScope,ObservatoryDashboard}.tsx; platform/src/app/usage/page.tsx; platform/src/lib/metering/queries.ts
**Interfaces:** Account routes force admin=false including superadmin; /api/usage derives uid. Canonical from/to/channel/provider/model/purpose plus connection/chart only where recorded. Same URL scope bothviews. Usage alias preservesquery. Admin Observatory remains restricted separately.

- [ ] Write failing meaningful tests in `platform/tests/account/activity-scope.test.ts:owner cannot spoofotheruid, invaliddates/bounds, aliases preservefilters, personaladmin noportal userselector, identicalallqueryfilters.`
- [ ] Run focused Vitest file; confirm behavior fails before implementation.
- [ ] Implement the named contract and corresponding Claude Design screen.
- [ ] Run focused tests and relevant regressions; require PASS.
- [ ] Inspect desktop/mobile/keyboard flow and record result.
- [ ] Commit scoped changes after required quality checks; master plan governs release.

### Task 2: Breakdown and drilldown

**Files:** platform/src/lib/metering/queries.ts; platform/src/components/observatory/ObservatoryDashboard.tsx; platform/src/components/account/ActivityBreakdown.tsx
**Interfaces:** API/CLI→connection→model from same events with unknown bucket and aggregator/underlyingmodel when recorded. Label bars/healthline axes units; missinglatency null notzero. Keep conversation→turn→attempt detail/pagination, receipt/estimate/unpriced/subscription distinctions; no globalMCPhealth personal.

- [ ] Write failing meaningful tests in `platform/tests/account/activity-reconciliation.test.ts:summarycalls equals breakdown includingunknown, status sum, datefilters applyall, nullcost/usage vs realzero, stale response canceled, ownscoped pagination/details.`
- [ ] Run focused Vitest file; confirm behavior fails before implementation.
- [ ] Implement the named contract and corresponding Claude Design screen.
- [ ] Run focused tests and relevant regressions; require PASS.
- [ ] Inspect desktop/mobile/keyboard flow and record result.
- [ ] Commit scoped changes after required quality checks; master plan governs release.

Changelog: v1.0 defines testable deliverables, interfaces and evidence.
