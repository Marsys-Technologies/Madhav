---
title: Journey5 AI Setup and Personas
version: 1.0
status: PLANNED
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

- [ ] Write failing meaningful tests in `platform/tests/account/cockpit.test.tsx:fourareas, ordinaryuser personal access, adminsystem guards unchanged, exactdefault header, allintegration groups/roles retained.`
- [ ] Run focused Vitest file; confirm behavior fails before implementation.
- [ ] Implement the named contract and corresponding Claude Design screen.
- [ ] Run focused tests and relevant regressions; require PASS.
- [ ] Inspect desktop/mobile/keyboard flow and record result.
- [ ] Commit scoped changes after required quality checks; master plan governs release.

### Task 2: Personas

**Files:** platform/src/lib/personas.ts; platform/src/app/api/personas/{route,[id]/route}.ts; platform/src/app/account/ai-cockpit/personas/page.tsx; platform/src/app/settings/personas/{PersonaForm,PersonaCard}.tsx; platform/src/components/chat/ModelStylePicker.tsx
**Interfaces:** Serialize owner mutations with profile row lock in withTransaction; verify target before clearingdefault; deletion reassigns default and protects last inside transaction. Classical Parāśari initializes empty account through explicitbootstrap, never overwrites existing. Nullstack=Use accountAIdefault; preserve legacy overrides. Strict enum/body/origin and active guard.

- [ ] Write failing meaningful tests in `platform/tests/account/personas.test.ts:foreign target cannot cleardefault, swaps/deletes atomic, lastprotected, preference/default mirror, nullstack and legacy selection.`
- [ ] Run focused Vitest file; confirm behavior fails before implementation.
- [ ] Implement the named contract and corresponding Claude Design screen.
- [ ] Run focused tests and relevant regressions; require PASS.
- [ ] Inspect desktop/mobile/keyboard flow and record result.
- [ ] Commit scoped changes after required quality checks; master plan governs release.

Changelog: v1.0 defines testable deliverables, interfaces and evidence.
