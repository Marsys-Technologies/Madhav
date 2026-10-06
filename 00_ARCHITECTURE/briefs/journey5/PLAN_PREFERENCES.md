---
title: Journey5 Preferences
version: 1.1
status: DEPLOYED_READ_ONLY_VERIFIED
---
# Preferences Implementation Plan

**Goal:** One saved setting shared across account and contextual controls.
> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement task-by-task.

**Architecture:** Reuse the accepted Journey shell, exact Console default and owner-scoped metering; add bounded typed account persistence. Keep personal AI separate from restricted operator diagnostics.
**Tech Stack:** Next.js/React, TypeScript, PostgreSQL, Firebase Auth, Vitest.
**Spec:** RECONCILIATION.md and the owner-authorized delivery sequence.

## Global Constraints
All constraints/review-focus cases in DELIVERY_PLAN.md apply. Claude Design precedes screen implementation; source-backed contracts qualify prototype claims.

## Review Focus
Owner isolation, concurrent writes, explicit choices, truthful unknowns and failures are tested below.

### Task 1: Persistence

**Files:** platform/src/lib/account/{profile,preference-types}.ts; platform/src/app/api/account/preferences/route.ts; platform/migrations/1310_journey5_account_preferences.sql
**Interfaces:** AccountPreferences titles:en|sa, nav/history/evidencePinned:boolean, grounding:right|inline, reducedMotion:boolean, textScale:0.875|1|1.125|1.25, readingDepth:deep|auto|quick|standard. Strict partial PATCH merges JSON in profiles.account_preferences atomically. GET returns defaults without overwriting explicit values. Default persona remains personas table.

- [x] Write meaningful regression coverage in `platform/tests/account/routes.test.ts and database.test.ts:invalid/unknown fields, own active identity only, concurrent disjoint patches preserve both, explicitfalse/zero, no secrets.`
- Initial per-task RED proof is not claimed beyond retained receipts; see execution receipt below.
- [x] Implement the named contract and corresponding Claude Design screen.
- [x] Run focused tests and relevant regressions; require PASS.
- [x] Inspect desktop/mobile/keyboard flow and record result.
- [x] Commit scoped changes after required quality checks; master plan governs release.

### Task 2: Shared consumers

**Files:** platform/src/app/account/preferences/page.tsx; platform/src/components/account/{PreferencesForm,AccountPreferencesProvider}.tsx; platform/src/components/journey1/{Titles,JourneyShell}.tsx; consultation preference consumers mapped in source
**Interfaces:** Provider reads owner prefs; mirrors existing keys/events, synchronizes contextual edits and visible save failure without cross-user storage. Form mirrors titles/pins/persona default. Deep seeds new consultation, preserves newer clicks/explicit choices/resumed question.

- [x] Write meaningful regression coverage in `platform/tests/account/preference-consumers.test.tsx, reading-preferences.test.tsx and reading-preferences.test.tsx:header/form synchronization, delayed-load newer-choice protection, owner cache cleared, initialdepth vs explicit/resumed, failedsave visible.`
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
