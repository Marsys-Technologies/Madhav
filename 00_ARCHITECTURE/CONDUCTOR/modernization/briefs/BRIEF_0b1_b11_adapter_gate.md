---
unit: 0b.1
wave: 0b
title: B.11 citation gate on the adapter/agentic path (live governance hole)
stream: B
worktree: ../MadhavStreamB
blockedBy: []
contributes_gate: G5b_onfinish
on_red: rollback
---

## Context (self-contained)
Audit-confirmed: `validateCitationsForStream` runs on the LEGACY path only at
`platform/src/app/api/chat/consume/route.ts:1374`; the live adapter/agentic branch (`:923–:1198`, gated by
`R11V2_USE_ADAPTERS=true`) has NO citation gate. This is a live B.11 (holistic-read/citation) hole and a hard
prerequisite (G5) for later legacy-pipeline deletion. Port the gate to the adapter path WITHOUT touching the
legacy synthesis trio.

## Scope
Wrap the adapter result stream with `validateCitationsForStream` (mirror the legacy `:1374` site) so adapter
responses pass the same citation/holistic output guard before `data-citation` parts emit. Do not alter the
legacy path. (Note: this is the route file the 0a.1 rename also touches — Conductor must sequence 0b.1 and
0a.1 on the same file, never concurrent; file-fence on `consume/route.ts`.)

## Acceptance criteria (all automated)
1. `pnpm vitest run platform/src/app/api/chat` green.
2. A new test asserts the adapter branch output passes the citation gate (parity with the legacy site).
3. **Golden-transcript:** an adapter-path response is byte-stable vs a recorded baseline EXCEPT for the added
   citation-gate enforcement (no other behavior change).
4. No regression: legacy-path citation test still green.

## must_not_touch
`platform/src/lib/synthesis/orchestrator.ts`, `single_model_strategy.ts`, `panel_strategy.ts` (legacy trio —
deleted later under G5/G5b, not here).

## Commit cadence / rollback
One commit: "0b.1 port B.11 citation gate to adapter path". Rollback = revert (gate simply not present again).
