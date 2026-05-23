# R11.F Bounded Loop Arc — Conductor Operator Docs

## Overview

| Item | Value |
|---|---|
| Arc name | R11.F — Bounded Agentic Loop Activation |
| Branch | `chat-v2/r11f-agentic-loop` |
| Worktree | `/Users/Dev/Vibe-Coding/Apps/MadhavR11FBound` |
| Queue | `00_ARCHITECTURE/CONDUCTOR/r11f/session_queue.yaml` |
| Master plan | `00_ARCHITECTURE/chat_v2_briefs/round11f/R11F_MASTER_PLAN_v1_0.md` |
| Sessions | 14 across 3 phases (A: 5, B: 5, C: 4) |
| PR cadence | 1 PR at C-S4; HALT for native merge approval |
| Log | `00_ARCHITECTURE/CONDUCTOR/r11f/CONDUCTOR_LOG.md` |
| Halt log | `00_ARCHITECTURE/CONDUCTOR/r11f/CONDUCTOR_HALT_LOG.md` |

## Precondition (CRITICAL)

**`feature/r11f-wiring-arc` must be merged to main before implementation sessions push
to `chat-v2/r11f-agentic-loop`.**

Verify: `git log main --oneline | grep 'r11f-s4'`
Expected: commit for `feat(r11f-s4): wire Gemini cachedContent API`.

If not merged: do NOT proceed past A-S1 authoring. Halt and report.

## Queue authority

The `session_queue.yaml` in the WORKTREE (`/Users/Dev/Vibe-Coding/Apps/MadhavR11FBound/`)
is the authoritative copy. The copy committed to main is for visibility only — it may lag
by 1–2 sessions. Conductor reads and writes the worktree copy exclusively.

## How to kick off

In a new Claude Code session, in the worktree directory:

```
You are the Conductor for the R11.F Bounded Loop Arc on the Marsys-JIS project.

Working directory: /Users/Dev/Vibe-Coding/Apps/MadhavR11FBound
Branch: chat-v2/r11f-agentic-loop
Queue: 00_ARCHITECTURE/CONDUCTOR/r11f/session_queue.yaml
Master plan: 00_ARCHITECTURE/chat_v2_briefs/round11f/R11F_MASTER_PLAN_v1_0.md

Your rules:
1. Read the queue. Walk sessions in order (respect blocked_by).
2. Spawn sub-agents via the Agent tool (subagent_type: general-purpose) for each session.
   Pass the full brief content as the prompt. The brief path is in the queue entry.
3. For B-S1 and B-S3 (parallel_safe: true): spawn BOTH in a single message with two
   Agent tool calls, each with isolation: worktree. Merge their commits after both PASS.
4. On PASS: mark status: completed, record commit_sha in the queue. Commit queue update.
5. On FAIL: write HALT_R11F-<session-id>.md to 00_ARCHITECTURE/CONDUCTOR/r11f/,
   mark status: halted, STOP. Do NOT fix-forward. Surface to operator.
6. After A-S5 PASS: B-S1 and B-S3 may be spawned in parallel (both are blocked_by A-S2,
   which is complete by then). B-S5 is blocked_by both B-S1 and B-S3.
7. C-S3 requires explicit IS.8(b) PASS declaration from C-S2. Verify before proceeding.
8. C-S4 opens the PR and HALTS unconditionally — never auto-merge.

Begin by reading the queue and reporting current status before spawning any sub-agent.
```

## Session discipline

- All commits go to `chat-v2/r11f-agentic-loop`.
- For parallel B-S1/B-S3 sub-agents using `isolation: worktree`: each agent works on an
  isolated copy. After both return PASS, verify commits are on or cherry-pick to the
  feature branch.
- Visual smoke sessions (A-S5, B-S2, B-S4, B-S5, C-S4) use Chrome MCP. Invoke the
  `chrome-devtools` skill if the MCP is not already connected.
- Screenshot evidence is committed to the worktree and included in the final PR.

## HALT protocol

Any sub-agent FAIL → Conductor writes `HALT_R11F-<id>.md` with:
- Session ID and title
- Failure description
- Screenshot if visual smoke session
- Last vitest output
- Suggested next step (for operator, not for autonomous retry)

Then marks the queue entry `status: halted` and STOPS.

DO NOT retry a failed session. DO NOT fix-forward. Surface to operator.

## PR cadence

One PR opened at C-S4. No per-phase PRs — the full arc lands in one squash or merge.
Title format: `feat(r11f): bounded agentic loop activation — all providers, B.11 floor, onFinish parity`

## After PR merge (operator steps)

1. Cloud Build deploys automatically from main.
2. Verify flags live in Cloud Run:
   ```bash
   gcloud run services describe amjis-web --region asia-south1 \
     --format='value(spec.template.spec.containers[0].env)' | tr ',' '\n' | grep R11E
   ```
3. Send 1 test query per provider from the UI. Confirm tool-flow timeline.
4. Watch error logs for 10 minutes.
5. Retire worktree: `git worktree remove /Users/Dev/Vibe-Coding/Apps/MadhavR11FBound`

---
*README.md — R11.F Conductor operator docs — authored 2026-05-23*
