---
canonical_id: R10_Y_S8
version: 1.0
status: CURRENT
session_id: Y-S8
title: Validator per-gate expander in ValidatorFailureBand
depends_on: [Y-S7]
blocked_on: []
flag: MARSYS_FLAG_R10_VALIDATOR_GATES
flag_default: true
client_side: "yes — NEXT_PUBLIC_MARSYS_FLAG_R10_VALIDATOR_GATES"
authored: 2026-05-20
---

# Y-S8 — Validator Per-Gate Expander

## Context

`ValidatorFailureBand` currently shows a collapsed failure summary when the query pipeline's validator stage rejects a response. Users can't see which specific gates failed and why. This session makes the failure band expandable — clicking it reveals a per-gate list with each gate's verdict (PASS/FAIL/WARN) and its reason text. The failure event payload is extended to carry per-gate verdicts.

**Amendment 1 (HARD GATE):** `NEXT_PUBLIC_MARSYS_FLAG_R10_VALIDATOR_GATES` is a client-side flag. It MUST be added to `.github/workflows/deploy.yml` `--build-arg` block.

**Amendment 3:** FLAGGED — changes failure event payload structure; risk-managed.

**Amendment 2:** Visible component (expandable ValidatorFailureBand) → click-path and parent-context test required.

## Files in Scope

- `platform/src/components/chat-v2/validator/ValidatorFailureBand.tsx` — add expandable per-gate list
- Validator adapter/event emitter (executor grep: `grep -rn "validator_failure\|ValidatorFailure" platform/src/lib/ platform/src/app/api/` ) — extend event payload to include `gates: Array<{name, verdict, reason}>`
- `.github/workflows/deploy.yml` — add `--build-arg NEXT_PUBLIC_MARSYS_FLAG_R10_VALIDATOR_GATES=true`
- `platform/tests/` — integration test

## Files Must NOT Touch

- Core validator logic (gate pass/fail computation) — only the event payload serialization
- Phase 4C files
- `platform/src/components/chat-v2/messages/MarkdownContent.tsx`

## Acceptance Criteria

1. **deploy.yml (Amendment 1 — HARD GATE):** `.github/workflows/deploy.yml` contains `--build-arg NEXT_PUBLIC_MARSYS_FLAG_R10_VALIDATOR_GATES=true`. Session is NOT complete until present.
2. **Client-side classification (Amendment 1):** Executor confirms via grep: `grep -rn "NEXT_PUBLIC_MARSYS_FLAG_R10_VALIDATOR_GATES" platform/src --include="*.ts*"` — confirms usage in a `'use client'` component.
3. **click-path (Amendment 2):** User path: Chat V2 → receive a response where the validator rejected at least one gate → `ValidatorFailureBand` appears → click the band → it expands to show a list of gates, each with a colored PASS/FAIL/WARN badge and a short reason string → clicking again collapses it. Document in commit body.
4. **Event payload extension:** The `validator_failure` event (or equivalent query_trace_steps entry) gains a `gates` array: `[{ name: string, verdict: 'PASS' | 'FAIL' | 'WARN', reason: string }]`. Existing consumers of the event are backward-compatible (gates is optional / may be empty array for legacy events).
5. **Per-gate rendering:** When flag is enabled and `gates` is non-empty: expandable list. When `gates` is empty or flag is disabled: collapsed band as before (no regression).
6. **Visual treatment:** FAIL = red badge, WARN = yellow, PASS = green. Gate name in monospace. Reason in normal text.
7. **Parent-context integration test (Amendment 2):** At least one test mounts `ValidatorFailureBand` within its real message/event provider chain (with a mock validator failure event containing gates array and flag=true) and asserts: (a) band is collapsed by default, (b) clicking expands and shows per-gate verdicts. Leaf test alone does NOT satisfy this AC.

## Pre-commit Gates

```bash
# Amendment 1 — HARD GATE
grep "NEXT_PUBLIC_MARSYS_FLAG_R10_VALIDATOR_GATES" .github/workflows/deploy.yml && echo "PASS: deploy.yml has flag" || echo "FAIL: HARD GATE"

grep -rn "NEXT_PUBLIC_MARSYS_FLAG_R10_VALIDATOR_GATES" platform/src --include="*.ts*" && echo "PASS" || echo "FAIL"

npx jest --testPathPattern="ValidatorFailure|validator.*gate|per.*gate|gate.*expand" --passWithNoTests
```

## Commit Template

```
feat(chat-v2): expandable per-gate verdicts in ValidatorFailureBand

ValidatorFailureBand gains click-to-expand list of per-gate verdicts
(PASS/FAIL/WARN + reason). Validator failure event payload extended
with gates[] array. Backward-compatible. Guarded by
MARSYS_FLAG_R10_VALIDATOR_GATES=true (NEXT_PUBLIC + deploy.yml build-arg
per Amendment 1).

Click-path: failure band → click → per-gate list expands → click → collapses.
```

## Decision Log

*(Executor: record any decisions or deviations here at close.)*
