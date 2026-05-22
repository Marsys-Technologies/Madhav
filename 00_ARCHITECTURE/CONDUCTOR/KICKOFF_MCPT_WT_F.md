# KICKOFF — MCP Transformation WT-F (MSR Grounding + Calibration MV)

Paste into a fresh Claude Code chat in Google Antigravity IDE, workspace at `/Users/Dev/Vibe-Coding/Apps/MadhavMCPT-GRD`.

---

```
You are the Conductor — autonomous orchestrator for MCP Transformation worktree F.
Single long-running session: v3.4-S1 (MSR signal-grounding pass + perf brief Phase P6
calibration MV + dashboard tab).

Implementation surface: Claude Code in Google Antigravity IDE.

Read first:
  1. PROJECT_MEMORY_MCP_TRANSFORMATION_v1_0.md
  2. 00_ARCHITECTURE/CONDUCTOR/MCP_TRANSFORMATION_PLAN_v1_0.md
  3. 00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_v1_0.md
  4. 00_ARCHITECTURE/CONDUCTOR/session_queue_MCPT_WT_F.yaml

Worktree: /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-GRD
Branch:   feature/mcpt-grounding
Queue:    00_ARCHITECTURE/CONDUCTOR/session_queue_MCPT_WT_F.yaml

Autonomy posture: requires_human_approval: false. Spawn with
--dangerously-skip-permissions. Per-session commit + push.

v3.4-S1 is the LONGEST single session in MCP Transformation (~6-10 hours wall-clock):
  Track A — MSR signal-grounding pipeline (419 ungrounded → 95%+ grounded). Operator
  review of candidates is part of the loop; sub-agent prepares the CSV review queue,
  pauses for operator markup, then applies grounded citations. Partial completion
  acceptable.
  Track B — Wilson SQL functions + mv_calibration_score MV + dashboard tab
  implementation (replaces v3.1.0-S5's placeholder).

If sub-agent hits SUB_AGENT_CONTEXT_OVERFLOW mid-grounding, halt and resume with a
continuation sub-agent that picks up where it left off (the candidate CSV is persisted).

After v3.4-S1's tracks both close (or partial-Track-A acceptable per brief), merge:
  git checkout feature/mcpt-final
  git merge --no-ff feature/mcpt-grounding -m "MCPT v3.4-S1: grounding + calibration MV → final"
  git push origin feature/mcpt-final

Begin now: v3.4-S1 is the only entry, depends_on: [].
```

---

## Operator quick-reference

- Single session, long-running: v3.4-S1.
- The MSR grounding pipeline writes a candidate CSV to `00_ARCHITECTURE/grounding_review/`. Operator (you) reviews + marks accepted candidates → sub-agent applies. Allow ~3 hours for review pass.
- Tracks A + B run in parallel within the same session as much as possible.
- Expected wall-clock: ~6–10 hours total (Day 1–4, runs in background while other WTs progress).
- Merge to feature/mcpt-final at session close.
- Operator close this chat after v3.4-S1 commits + pushes.
