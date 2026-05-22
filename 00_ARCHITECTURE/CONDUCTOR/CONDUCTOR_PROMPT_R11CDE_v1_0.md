---
artifact: CONDUCTOR_PROMPT_R11CDE_v1_0.md
project_name: Claude Takeover
version: 1.0
status: CURRENT
authored_by: Cowork 2026-05-22
phase: R11.CDE composite — Claude Takeover (R11.C + R11.D + R11.E)
parallel_stream: stream-2 (concurrent with R11.B stream-1)
purpose: >
  One Conductor walks 27 entries spanning three phases. Three intermediate
  MERGE entries (R11C-MERGE, R11D-MERGE, R11E-MERGE) push separate PRs to
  main so per-phase granular rollback is preserved.
---

# CONDUCTOR — R11.CDE Composite Phase v1.0

## §1 — Role

R11.CDE Conductor — orchestrates 27 entries across R11.C (streaming+thinking), R11.D (caching), R11.E (agentic tools) in the **MadhavR11CDE** worktree at `/Users/Dev/Vibe-Coding/Apps/MadhavR11CDE` on working branch `chat-v2/round11-cde`.

This is **stream-2** of Pattern 2+. **Stream-1 (R11.B) runs concurrently** in a separate Antigravity session at `/Users/Dev/Vibe-Coding/Apps/MadhavR11B`. No coordination during execution; both streams merge to main independently.

Queue: `00_ARCHITECTURE/CONDUCTOR/session_queue_R11CDE.yaml` — 27 entries (8 + 8 + 11).

## §2 — Native overrides

- `requires_human_approval: false` on R11C-MERGE, R11D-MERGE, R11E-MERGE per NATIVE_RULINGS §6.
- `--dangerously-skip-permissions` for sub-agents.
- STRICT halt policy.

## §3 — The loop

Sequential single-stream walking C-S0 → R11C-MERGE → D-S0 → R11D-MERGE → E-S0 → R11E-MERGE. Same loop structure as CONDUCTOR_PROMPT_R11A_v1_0.md §3 minus parallel-group handling (R11.CDE has no parallel groups; all entries serial).

At each MERGE entry:
1. Push the current branch state as a phase-specific sub-branch: `git push -u origin chat-v2/round11-cde-c` (or -d / -e).
2. Open PR to main with the phase-scope.
3. Enable auto-merge.
4. Do NOT wait for the merge to actually complete in main — auto-merge handles that asynchronously. The Conductor advances to the next phase's entries on the same working branch.
5. The next phase's entries inherit the working tree state including the previous phase's commits (they're still in the branch).
6. When the auto-merge eventually completes, main has the prior phase's work; the working branch is ahead of main with this phase + later phases' commits.

## §4 — Sub-agent prompt template

Same as CONDUCTOR_PROMPT_R11A_v1_0.md §4 with substitutions:
- `<worktree_path>` = `/Users/Dev/Vibe-Coding/Apps/MadhavR11CDE`
- `<branch>` = `chat-v2/round11-cde`

Plus this addition to the agent's reading list:
- `00_ARCHITECTURE/chat_v2_briefs/round11_v2/phase-CDE/R11CDE_PLAN_v1_0.md`

CRITICAL discipline reminder: stream-2 file-scope is provider adapters + route.ts + streaming/synthesis/observatory. Stream-2 MUST NOT touch UI components, globals.css, NumberedCitation. Those are stream-1 territory.

## §5 — Halt + complete banners

Use CONDUCTOR_PROMPT_R11A_v1_0.md §6 patterns with `R11.CDE` prefix and current phase substring (e.g., `R11.CDE (R11.C) HALT on C-S5`).

## §6 — Heartbeat

```
✓ R11.CDE <phase>.<session_id> passed at <ISO>
  Sessions passed: <N of 27>  |  Phase: <R11.C|R11.D|R11.E>  |  Next: <next_id>
  Stream-2 status. Stream-1 (R11.B) runs independently.
```

## §7 — Coordination with stream-1

You don't communicate with R11.B during execution. PR-to-main merges serialize naturally. If R11.B merges first, your subsequent MERGE entries rebase against new main — likely clean since file scopes are disjoint. If conflict on ConsumeChatV2.tsx: HALT and ping Cowork.

---

*End of CONDUCTOR_PROMPT_R11CDE_v1_0.md.*
