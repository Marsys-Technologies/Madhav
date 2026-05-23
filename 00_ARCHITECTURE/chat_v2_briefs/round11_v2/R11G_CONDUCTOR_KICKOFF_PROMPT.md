---
canonical_id: R11G_CONDUCTOR_KICKOFF_PROMPT
version: 1.0
status: CURRENT
authored: 2026-05-23
purpose: Paste-prompt #2 — launches the autonomous R11.G Conductor in the MadhavR11G worktree. Run this in a FRESH Claude Code session opened at /Users/Dev/Vibe-Coding/Apps/MadhavR11G with --dangerously-skip-permissions enabled.
---

# R11.G — Conductor Kickoff Prompt

## Pre-paste checklist

1. Setup prompt #1 completed successfully.
2. You have opened a FRESH Claude Code session at `/Users/Dev/Vibe-Coding/Apps/MadhavR11G`.
3. Started Claude Code with `--dangerously-skip-permissions` flag.

## Paste this into the new worktree's Claude Code session

```
You are launching the autonomous R11.G arc. You will act as the Conductor and walk the session queue without further operator confirmation. Use --dangerously-skip-permissions. Halt strictly on the first RED at any phase.

## Context — read first, in order

1. /Users/Dev/Vibe-Coding/Apps/MadhavR11G/CLAUDE.md — project orientation.
2. /Users/Dev/Vibe-Coding/Apps/MadhavR11G/00_ARCHITECTURE/chat_v2_briefs/round11_v2/R11G_LIVE_ARC_PLAN_v1_0.md — the plan.
3. /Users/Dev/Vibe-Coding/Apps/MadhavR11G/00_ARCHITECTURE/chat_v2_briefs/round11_v2/R11G_BRIEF_v1_0.md — ground truth brief.
4. /Users/Dev/Vibe-Coding/Apps/MadhavR11G/00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_R11G_v1_0.md — your Conductor working prompt.
5. /Users/Dev/Vibe-Coding/Apps/MadhavR11G/00_ARCHITECTURE/CONDUCTOR/session_queue_R11G.yaml — the queue.
6. /Users/Dev/Vibe-Coding/Apps/MadhavR11G/00_ARCHITECTURE/KNOWN_PRE_EXISTING_FAILURES.md — baseline for Sessions 4 + 6 CI diff.

## Operating mode

- --dangerously-skip-permissions enabled. NO operator pauses between sub-agents.
- Strict halt: first RED → write R11G_HALT_S<N>.md + STOP. No retry. No fix-forward.
- Single feature branch: `feature/r11g-tool-executor-toggle` (already created by setup).
- Single PR at end via `gh pr merge --squash --delete-branch --admin`.
- Production rollout: deploy.yml NEXT_PUBLIC flag flip lands in this arc (toggle visibility goes live in prod). R11.E loop + R11.D D.3 cache flags stay operator-controlled — DO NOT TOUCH.

## Session walk

Walk /Users/Dev/Vibe-Coding/Apps/MadhavR11G/00_ARCHITECTURE/CONDUCTOR/session_queue_R11G.yaml entries in order.

For each entry:
1. Read entry's `prompt` field.
2. Spawn sub-agent via Agent tool (subagent_type: general-purpose).
3. Wait for return. Parse `STATUS=PASS|FAIL`.
4. PASS → mark `status: passed`, commit YAML update, proceed.
5. FAIL → write R11G_HALT_S<N>.md, mark `status: failed`, STOP.

R11.G has NO parallel groups — all 7 sessions are sequential. Simpler than R11.F.

## Session-completion bookkeeping

After each sub-agent reports PASS:

1. Verify sub-agent's commit landed on `feature/r11g-tool-executor-toggle`:
   ```bash
   cd /Users/Dev/Vibe-Coding/Apps/MadhavR11G
   git log --oneline -5
   ```

2. Update session_queue_R11G.yaml: set `status: passed`, `passed_at: <ISO timestamp>`, `commit_sha: <HEAD>`.

3. Commit the queue update:
   ```bash
   git add 00_ARCHITECTURE/CONDUCTOR/session_queue_R11G.yaml
   git commit -m "chore(r11g): G-S<N> passed [conductor]"
   ```

4. Proceed.

## Final close (Session 7)

When Session 7 sub-agent completes:
1. Confirm `ROLLOUT_PHASE_R11G_RESULT.md` exists.
2. Confirm governance commit landed on main.
3. Surface final report to operator:

   "R11.G autonomous arc COMPLETE.
   - 7 sessions PASSED.
   - Branch: feature/r11g-tool-executor-toggle merged to main via PR #<N>.
   - Final Cloud Run revision: <revision-ID>.
   - Settings dropdown now visible in production.
   - Default chat shell: Classic (existing users see no change).
   - Tool executor wired: R11.E loops now execute real MCP tools when their flags flip.
   - R11.E flag rollout commands unchanged — see ROLLOUT_PHASE_R11F_RESULT.md when ready.
   - Test it: open /consume in your browser, click the gear icon in the header, switch to 'Claude-style chat', hard-refresh. The R11.B chrome activates."

## Halt protocol

On ANY sub-agent FAIL:
1. Write /Users/Dev/Vibe-Coding/Apps/MadhavR11G/00_ARCHITECTURE/chat_v2_briefs/round11_v2/R11G_HALT_S<N>.md with:
   - Failing assertion verbatim
   - Last successful commit SHA
   - Current branch state
   - Sub-agent's full final message
2. Do NOT retry. Do NOT fix-forward.
3. Surface to operator: "R11.G arc HALTED at Session <N>. See R11G_HALT_S<N>.md."

## Non-negotiables

- No MCPT touches.
- No R11.E loop flag flips (operator-only).
- No R11.D D.3 cache flag flip (operator-only).
- No adapter code edits (stable from R11.F).
- No code outside the may_touch list in the brief.
- No PR to main before Session 6.
- Mirror discipline propagated in Session 7 only.

Begin Session 1 now.
```

## Operator notes

- Expected wall-clock: 6-8 hours autonomous.
- After arc completes, you can immediately test the toggle in your browser without flipping any new server flags. The R11.B chrome activates client-side via localStorage.
- R11.E loop flag rollout remains your decision — flip them when you're ready, separately from R11.G.

*End of R11G_CONDUCTOR_KICKOFF_PROMPT_v1_0.md*
