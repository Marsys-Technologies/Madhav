---
title: Journey5 Identity and Security
version: 1.0
status: PLANNED
---
# Identity and Security Implementation Plan

**Goal:** Account index, profile and secure password/recovery/sign-out workflows.
> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement task-by-task.

**Architecture:** Reuse the accepted Journey shell, exact Console default and owner-scoped metering; add bounded typed account persistence. Keep personal AI separate from restricted operator diagnostics.
**Tech Stack:** Next.js/React, TypeScript, PostgreSQL, Firebase Auth, Vitest.
**Spec:** RECONCILIATION.md and the owner-authorized delivery sequence.

## Global Constraints
All constraints/review-focus cases in DELIVERY_PLAN.md apply. Claude Design precedes screen implementation; source-backed contracts qualify prototype claims.

## Review Focus
Owner isolation, concurrent writes, explicit choices, truthful unknowns and failures are tested below.

### Task 1: Profile and account shell

**Files:** platform/src/app/account/{layout,page}.tsx; platform/src/app/account/profile/page.tsx; platform/src/components/account/{AccountNav,ProfileForm}.tsx; platform/src/app/api/account/profile/route.ts
**Interfaces:** GET/PATCH profile current active user only; PATCH accepts name1–100 characters; username uses existing endpoint, email read-only. No phone, fixed chart or fabricated member-since. Avatar points/account.

- [ ] Write failing meaningful tests in `platform/tests/account/profile.test.ts:401/403, ignores/rejects foreign owner, rejects unknown keys/email, validates bounds; failed save retains input.`
- [ ] Run focused Vitest file; confirm behavior fails before implementation.
- [ ] Implement the named contract and corresponding Claude Design screen.
- [ ] Run focused tests and relevant regressions; require PASS.
- [ ] Inspect desktop/mobile/keyboard flow and record result.
- [ ] Commit scoped changes after required quality checks; master plan governs release.

### Task 2: Security

**Files:** platform/src/app/account/security/page.tsx; platform/src/components/account/SecurityForm.tsx; platform/src/app/api/account/security/route.ts
**Interfaces:** POST accepts fresh Firebase idToken matching session uid and auth_time within5minutes, revokes refresh tokens then clears cookie. Browser Firebase reauthenticateWithCredential/updatePassword; current/new/repeat≥12; no passwords to app server. Recovery existing route; sign-out-all real; no device inventory or keep-current claim.

- [ ] Write failing meaningful tests in `platform/tests/account/security.test.ts: mismatch/stale/malformed/origin rejection; revoke failure not success; reauthentication and matching new passwords required; logout regressions.`
- [ ] Run focused Vitest file; confirm behavior fails before implementation.
- [ ] Implement the named contract and corresponding Claude Design screen.
- [ ] Run focused tests and relevant regressions; require PASS.
- [ ] Inspect desktop/mobile/keyboard flow and record result.
- [ ] Commit scoped changes after required quality checks; master plan governs release.

Changelog: v1.0 defines testable deliverables, interfaces and evidence.
