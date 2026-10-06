---
title: Journey5 Preferences
version: 1.0
status: PLANNED
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

**Files:** platform/src/lib/account/{preferences,preference-types}.ts; platform/src/app/api/account/preferences/route.ts; platform/migrations/<next>_journey5_account_preferences.sql
**Interfaces:** AccountPreferences titles:en|sa, nav/history/evidencePinned:boolean, grounding:right|inline, reducedMotion:boolean, textScale:0.875|1|1.125|1.25, readingDepth:deep|auto|quick|standard. Strict partial PATCH merges JSON in profiles.account_preferences atomically. GET returns defaults without overwriting explicit values. Default persona remains personas table.

- [ ] Write failing meaningful tests in `platform/tests/account/preferences.test.ts:invalid/unknown fields, own active identity only, concurrent disjoint patches preserve both, explicitfalse/zero, no secrets.`
- [ ] Run focused Vitest file; confirm behavior fails before implementation.
- [ ] Implement the named contract and corresponding Claude Design screen.
- [ ] Run focused tests and relevant regressions; require PASS.
- [ ] Inspect desktop/mobile/keyboard flow and record result.
- [ ] Commit scoped changes after required quality checks; master plan governs release.

### Task 2: Shared consumers

**Files:** platform/src/app/account/preferences/page.tsx; platform/src/components/account/{PreferencesForm,AccountPreferencesProvider}.tsx; platform/src/components/journey1/{Titles,JourneyShell}.tsx; consultation preference consumers mapped in source
**Interfaces:** Provider reads owner prefs; mirrors existing keys/events, synchronizes contextual edits and visible save failure without cross-user storage. Form mirrors titles/pins/persona default. Deep seeds new consultation, preserves newer clicks/explicit choices/resumed question.

- [ ] Write failing meaningful tests in `platform/tests/account/preference-consumers.test.tsx:header/form synchronization, delayed-load newer-choice protection, owner cache cleared, initialdepth vs explicit/resumed, failedsave visible.`
- [ ] Run focused Vitest file; confirm behavior fails before implementation.
- [ ] Implement the named contract and corresponding Claude Design screen.
- [ ] Run focused tests and relevant regressions; require PASS.
- [ ] Inspect desktop/mobile/keyboard flow and record result.
- [ ] Commit scoped changes after required quality checks; master plan governs release.

Changelog: v1.0 defines testable deliverables, interfaces and evidence.
