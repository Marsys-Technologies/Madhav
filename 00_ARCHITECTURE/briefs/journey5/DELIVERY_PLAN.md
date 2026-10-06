---
title: Journey 5 delivery
version: 1.0
status: IN_PROGRESS
source: f50a00091db22ac794c33d188941591e91aa0792
authority: CCD-024
---
# Journey 5 Delivery Implementation Plan

**Goal:** Deliver all four reconciled blocks through Claude Design, working frontend/backend and a verified protected release.
> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement task-by-task.

**Architecture:** Reuse the accepted Journey shell, exact Console default and owner-scoped metering; add bounded typed account persistence. Keep personal AI separate from restricted operator diagnostics.
**Tech Stack:** Next.js/React, TypeScript, PostgreSQL, Firebase Auth, Vitest.
**Spec:** RECONCILIATION.md and the owner-authorized delivery sequence.

## Global Constraints
- My Account → Profile, Security, Preferences, AI Cockpit → Console, Personas, My Observatory, Consumption. Preserve review serials18–24.
- Preserve signature12, accepted typography, #0A0806/#14110B, restrained gold, shared title control, and 320/390/1440 layouts. Existing approved shell rules override generic brand examples.
- Deep (Recommended) and Classical Parāśari initial defaults; preserve explicit saved/per-question choices. Account AI default is one exact choice; legacy persona stack overrides remain explicit and compatible.
- Authenticated active-user ownership throughout. No fake device inventory, password success, missing-value zeros, copied chart identity, paid-provider acceptance or expanded grants.
- No unrelated engine/campaign work or destructive schema/data change. Provisional Sanskrit names remain provisional.

## Review Focus
1. User A settings/personas/usage never appear for B; include unauthenticated and inactive-user denial.
2. Concurrent persona defaults/deletes preserve one default and final persona transactionally.
3. Failed/stale password reauthentication never succeeds or stores credentials; fresh proof must match own uid.
4. All usage summaries, graphs and drilldowns receive identical dates/filters; stale responses cannot overwrite current scope.
5. Explicit consultation choices survive preference loading; defaults seed new work while resumed history remains intact.

## Execution and campaign
- [x] Self-review four block plans against reconciliation and current source.
- [x] Revise SAME Claude Design project; create Journey05 board and update Review Hub/Foundations feedback. Inspect interactive desktop/mobile/keyboard and preserve versioned export.
- [x] Implement [Identity/security](PLAN_IDENTITY_SECURITY.md).
- [x] Implement [Preferences](PLAN_PREFERENCES.md).
- [x] Implement [AI setup/personas](PLAN_AI_SETUP_PERSONAS.md).
- [x] Implement [Activity/consumption](PLAN_ACTIVITY_CONSUMPTION.md).
- [x] Run focused meaningful tests, required full quality gates, additive migration review/rehearsal and rendered acceptance; repair failures.
- [ ] Update campaign evidence; protected PR/merge; exclusive production lease; backup/rollback; exact candidate deployment and live read-only verification.

| Block | Plan | Claude Design | Implemented | Verified | Deployed |
|---|---|---|---|---|---|
| Identity/security | Reconciled | Revised in Claude Design | Implemented locally | Source and fictional rendered checks pass; authenticated release checks pending | Pending |
| Preferences | Reconciled | Revised in Claude Design | Implemented locally | Source and fictional rendered checks pass; authenticated release checks pending | Pending |
| AI setup/personas | Reconciled | Revised in Claude Design | Implemented locally | Source and fictional rendered checks pass; authenticated release checks pending | Pending |
| Activity/consumption | Reconciled | Revised in Claude Design | Implemented locally | Source and fictional rendered checks pass; authenticated release checks pending | Pending |

Design, implementation, runtime and owner acceptance are distinct. The prototype uses illustrative data and never claims deployment.

## Release and rollback
Refresh main/leases and pin exact accepted candidate. Verify migration-number collisions, synthetic PostgreSQL rehearsal, recoverable backup identifier/restore mechanism, required checks and previous healthy web revision/image/traffic. Use existing governed migration runner and candidate/smoke/promotion process; independently verify actual schema application and deployed revision/traffic/authenticated screens. No bypass or foreign-run cancellation. Stop/rollback on unexpected identity, isolation, migration or service state. Backward-compatible additive schema can remain with predecessor app only after verification. Real credential-changing acceptance remains human-owned; no real chart/account mutation for testing.

Changelog: v1.0 records scope, dependencies, evidence gates and four deliverables.
