---
title: Journey5 AI Setup and Personas
version: 1.1
status: DEPLOYED_READ_ONLY_VERIFIED
---
# AI Setup and Personas Implementation Plan

**Goal:** Personal Cockpit with existing complete Console and consistent persona default.
> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement task-by-task.

**Architecture:** Reuse the accepted Journey shell, exact Console default and owner-scoped metering; add bounded typed account persistence. Keep personal AI separate from restricted operator diagnostics.
**Tech Stack:** Next.js/React, TypeScript, PostgreSQL, Firebase Auth, Vitest.
**Spec:** RECONCILIATION.md and the owner-authorized delivery sequence.

## Global Constraints
All constraints/review-focus cases in DELIVERY_PLAN.md apply. Claude Design precedes screen implementation; source-backed contracts qualify prototype claims.

## Review Focus
Owner isolation, concurrent writes, explicit choices, truthful unknowns and failures are tested below.

### Task 1: Console and navigation

**Files:** platform/src/app/account/ai-cockpit/{page,console/page}.tsx; platform/src/components/account/CockpitNav.tsx; platform/src/components/ai-console/AIConsole.tsx; platform/src/app/ai-console/layout.tsx
**Interfaces:** Compact group index, four child areas, reuse real Console provider/CLI/customconfig/fourroles controls. Exact state.defaultChoice drives summary. Legacyai-console aliases canonical account route. Viewactivity uses same recorded connection scope. No catalogue/readiness conflation.

- [x] Write meaningful regression coverage in `platform/tests/account/ai-owner-state.test.tsx and personal-activity.test.tsx:fourareas, ordinaryuser personal access, adminsystem guards unchanged, exactdefault header, allintegration groups/roles retained.`
- Initial per-task RED proof is not claimed beyond retained receipts; see execution receipt below.
- [x] Implement the named contract and corresponding Claude Design screen.
- [x] Run focused tests and relevant regressions; require PASS.
- [x] Inspect desktop/mobile/keyboard flow and record result.
- [x] Commit scoped changes after required quality checks; master plan governs release.

### Task 2: Personas

**Files:** platform/src/lib/personas.ts; platform/src/app/api/personas/{route,[id]/route}.ts; platform/src/app/account/ai-cockpit/personas/page.tsx; platform/src/app/settings/personas/{PersonaForm,PersonaCard}.tsx; platform/src/components/account/{PersonaManager,ReadingPersonaPicker,DefaultPersonaSelect}.tsx
**Interfaces:** Serialize owner mutations with profile row lock in withTransaction; verify target before clearingdefault; deletion reassigns default and protects last inside transaction. Classical Parāśari is a non-mutating fallback for an empty account; an explicit first persona save establishes a saved default, never overwriting an existing one. Nullstack=Use accountAIdefault; preserve legacy overrides. Strict enum/body/origin and active guard.

- [x] Write meaningful regression coverage in `platform/tests/account/database.test.ts, persona-api.test.ts, persona-manager.test.tsx, persona-store.test.tsx, persona-reading.test.ts and persona-synthesis.test.ts:foreign target cannot cleardefault, swaps/deletes atomic, lastprotected, preference/default mirror, nullstack and legacy selection.`
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
