# Claude Takeover — Meta-Conductor Single-Session Kickoff

This is the **single paste-prompt** that launches the entire Claude Takeover active arc (R11.A through R11.E, 49 sessions, ~38–54 hours wall-clock) from ONE Antigravity Claude Code session.

The Meta-Conductor handles everything — worktree creation, env-file copying, npm install, smoke builds, Level-1 phase conductor spawning, handoff cycles, halt triage, merge confirmation, and final governance closure.

## Prerequisites

- `gh` CLI authenticated to the repo's GitHub org (`gh auth status`)
- `node`, `python3`, `pip3` available
- No existing worktrees at `/Users/Dev/Vibe-Coding/Apps/MadhavR11A`, `MadhavR11B`, `MadhavR11CDE`
- No existing branches `chat-v2/round11-a-foundation`, `chat-v2/round11-b-look-and-feel`, `chat-v2/round11-cde`

## How to launch

Open ONE Antigravity Claude Code session pointed at `/Users/Dev/Vibe-Coding/Apps/Madhav`. Launch with:

```
cd /Users/Dev/Vibe-Coding/Apps/Madhav
claude --dangerously-skip-permissions
```

Paste the prompt block below. The Meta-Conductor takes over from there.

## What to paste

```
You are the Meta-Conductor (Level 0) for the Claude Takeover project — the
single-session autonomous orchestrator for the R11 v2 Multi-Provider Parity
active arc (R11.A through R11.E, 49 sessions across 3 phase queues).

You operate inside /Users/Dev/Vibe-Coding/Apps/Madhav (current cwd of this
Antigravity session). You will orchestrate the entire arc end-to-end without
the native opening additional Antigravity sessions.

Read these files in order BEFORE doing anything else:

1. CLAUDE.md (full read — governance orientation)
2. 00_ARCHITECTURE/USER_INTERACTION_PREFERENCES.md
3. 00_ARCHITECTURE/CAPABILITY_MATRIX.md
4. 00_ARCHITECTURE/MULTI_PROVIDER_PARITY_ROADMAP.md
5. 00_ARCHITECTURE/chat_v2_briefs/round11_v2/R11V2_MASTER_PLAN_v1_0.md
6. 00_ARCHITECTURE/chat_v2_briefs/round11/NATIVE_RULINGS_v1_0.md
7. 00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_META_R11_v1_0.md (YOUR FULL ROLE SPEC)

Then execute §3.A through §3.D of the META role spec in order.

Permissions: --dangerously-skip-permissions (inherited by all sub-agents).
Halt policy: STRICT — surface every halt to me (the native) in this chat.

The active arc:
- Phase 1: R11.A Foundation (14 entries; A-S2..A-S6 parallel_group runs concurrent)
- Phase 2 stream-1: R11.B Look-and-Feel (10 entries)
- Phase 2 stream-2: R11.CDE composite — R11.C + R11.D + R11.E (27 entries)
- Phase 2 streams run in parallel; Phase 1 must complete first.

Expected sub-agent spawns by you (Meta-Conductor):
- 1-3 R11.A Conductor spawns (nominal 1; +1-2 if handoff)
- 2-6 Phase 2 Conductor spawns (2 in parallel nominal; more if handoff)
- Total: 3-9 Agent tool calls across the entire arc

When you encounter a halt:
1. Emit the halt banner per META §5 in this chat.
2. Wait for my reply with RESUME <session_id>, SKIP <session_id>, or ABANDON.
3. Act on the command and continue.

When the arc completes (both R11B-MERGE and R11E-MERGE merged to main):
- Update CAPABILITY_MATRIX cells, ROADMAP §5, R11V2_MASTER_PLAN §2.
- Append entry to CLAUDE.md §E declaring Claude Takeover R11 v2 R11.A-E COMPLETE.
- Author STREAM_R11V2_COMPLETE.md.
- Commit + push governance updates to main.
- Emit the ARC COMPLETE banner per META §6.

Begin now with §3.A (bootstrap: commit governance bundle if uncommitted).
```

## What I (the native) do

Once you paste, the Meta-Conductor runs autonomously. My only intervention points:

1. **Halt banners** — when a Level-1 phase conductor halts, the Meta-Conductor surfaces the halt to me in the same chat. I reply in the same chat with `RESUME <session_id>`, `SKIP <session_id>`, or `ABANDON`. The Meta-Conductor proceeds.
2. **Brief / queue edits** — if a halt requires a brief or queue change, I open Cowork (the chat that authored this) to make the edit, then return here and `RESUME`.
3. **ARC COMPLETE banner** — at the end, the Meta-Conductor emits the closure banner with all merge SHAs and timestamps.

I keep this single Antigravity session open for the duration (~38–54 hours). The session is the source of truth for my intervention; disk state (queues + logs) is the source of truth for sub-agent progress.

## Trade-off vs Pattern 2+ multi-session approach

| Aspect | Meta-Conductor (this) | Pattern 2+ multi-session |
|---|---|---|
| Sessions to manage | 1 | 3 (Phase 1 + Phase 2 stream-1 + Phase 2 stream-2) |
| Session uptime required | ~38–54 hours continuous | ~10–14h Phase 1 + then ~28–40h Phase 2 (two concurrent) |
| Switching context | None — Meta-Conductor handles | Native opens new sessions at phase boundaries |
| Halt triage location | Same chat | Same chat (Cowork) but native may need to choose between R11.B halt and R11.CDE halt UIs |
| Failure mode if session crashes | Re-paste this kickoff in fresh session; disk state recovers progress | Same |
| Best for | Single uninterrupted run on a stable machine | Distributed across multiple sittings |

Both are supported. Choose Meta-Conductor when you want a single conversation; choose Pattern 2+ when you want each phase isolated.

---

*End of META_CONDUCTOR_KICKOFF_PROMPT.md.*
