---
title: Journey5 Identity and Security
version: 1.1
status: DEPLOYED_READ_ONLY_VERIFIED
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

- [x] Write meaningful regression coverage in `platform/tests/account/routes.test.ts and profile-form.test.tsx:401/403, ignores/rejects foreign owner, rejects unknown keys/email, validates bounds; failed save retains input.`
- Initial per-task RED proof is not claimed beyond retained receipts; see execution receipt below.
- [x] Implement the named contract and corresponding Claude Design screen.
- [x] Run focused tests and relevant regressions; require PASS.
- [x] Inspect desktop/mobile/keyboard flow and record result.
- [x] Commit scoped changes after required quality checks; master plan governs release.

### Task 2: Security

**Files:** platform/src/app/account/security/page.tsx; platform/src/components/account/SecurityForm.tsx; platform/src/app/api/account/security/route.ts
**Interfaces:** POST accepts fresh Firebase idToken matching session uid and auth_time within5minutes, revokes refresh tokens then clears cookie. Browser Firebase reauthenticateWithCredential/updatePassword; current/new/repeat≥12; no passwords to app server. Recovery existing route; sign-out-all real; no device inventory or keep-current claim.

- [x] Write meaningful regression coverage in `platform/tests/account/routes.test.ts, password-flow.test.ts and security-form.test.tsx: mismatch/stale/malformed/origin rejection; revoke failure not success; reauthentication and matching new passwords required; logout regressions.`
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
