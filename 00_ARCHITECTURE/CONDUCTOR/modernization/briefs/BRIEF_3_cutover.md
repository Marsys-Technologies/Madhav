---
unit: 3.cutover
wave: 3
title: Pipeline cutover — adapter onFinish parity + flip selector default (sets G5b)
stream: A
worktree: ../MadhavStreamA
blockedBy: [2a, 3.gateway_pipeline_isolation, 0b.1]
sets_gate: G5b_onfinish
on_red: halt_queue   # prod cutover — integrity-critical; stop + surface on failure
---

## Context (self-contained)
The new deterministic data is already live (2a did the staging→live swap). The gateway + isolated pipelines
exist (3.gateway). 0b.1 ported the B.11 citation gate to the adapter path (the first half of G5b). This unit
completes the cutover: bring the adapter/agentic path's `onFinish` to full parity, then flip the default
pipeline. G5b is the hard gate that gates legacy deletion.

## Scope
- **onFinish parity (the G5b core):** the adapter/agentic path's `onFinish` must write-through identically to
  the legacy path — **persistence** (conversation/messages), **prediction logging**, and **observatory**
  telemetry. Prove with a golden-transcript test (legacy `onFinish` vs adapter `onFinish` produce identical
  persistence/prediction/observatory writes for a fixed transcript).
- **Flip the selector default** to the new (Claude-style/adapter) pipeline in the SettingsDropdown / pipeline
  selector. Legacy stays reachable behind the flag (NOT deleted yet — that is 3.legacy_delete).
- **Zero-touch prod:** deploy → automated post-deploy smoke → auto-rollback on failure (kill-switch on error spike).

## Acceptance criteria (all automated)
1. **G5b gate:** `npx vitest run platform/src/app/api/chat/__tests__/onfinish_parity.golden.test.ts` green —
   adapter onFinish == legacy onFinish on persistence + predictions + observatory.
2. Selector default = new pipeline; legacy still reachable behind the flag.
3. Post-deploy smoke green (else auto-rollback + halt_queue); no telemetry/persistence rows dropped vs legacy.
4. B.11 citation gate still enforced on the now-default adapter path (no regression from 0b.1).

## must_not_touch
`chart_facts`/`l25_*` (2a, done), `platform/python-sidecar/**`, `platform/src/app/clients/**` (consult_nav, done),
`platform/src/lib/synthesis/orchestrator.ts` etc. (legacy trio — deleted in 3.legacy_delete, not here).

## Commit cadence / rollback
Commits: (1) adapter onFinish write-through parity + golden test, (2) selector default flip + deploy. Rollback
= revert + flag flip back to legacy. on_red=halt_queue (this is the prod cutover).
