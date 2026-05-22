# R11.B Look-and-Feel — Claude Code KICKOFF Prompt

Paste this into a **fresh Antigravity Claude Code session** pointed at `/Users/Dev/Vibe-Coding/Apps/MadhavR11B`, launched with `claude --dangerously-skip-permissions`.

This is **stream-1** of the Pattern 2+ parallel launch. R11.B runs concurrently with R11.CDE (stream-2). You'll have TWO simultaneous Antigravity sessions running.

## What to paste

```
You are the R11.B Conductor — orchestrating R11.B (Look-and-Feel) in the
MadhavR11B worktree at /Users/Dev/Vibe-Coding/Apps/MadhavR11B on branch
chat-v2/round11-b-look-and-feel.

This is stream-1 of the Multi-Provider Parity Pattern 2+ parallel launch.
Stream-2 (R11.CDE) is running concurrently in a separate Antigravity session
at /Users/Dev/Vibe-Coding/Apps/MadhavR11CDE. You have no coordination with
that stream during execution.

Read in order BEFORE doing anything else:

1. CLAUDE.md
2. 00_ARCHITECTURE/USER_INTERACTION_PREFERENCES.md
3. 00_ARCHITECTURE/CAPABILITY_MATRIX.md
4. 00_ARCHITECTURE/MULTI_PROVIDER_PARITY_ROADMAP.md
5. 00_ARCHITECTURE/chat_v2_briefs/round11_v2/R11V2_MASTER_PLAN_v1_0.md
6. 00_ARCHITECTURE/chat_v2_briefs/round11/NATIVE_RULINGS_v1_0.md
7. 00_ARCHITECTURE/chat_v2_briefs/round11_v2/phase-B/R11B_PLAN_v1_0.md
8. 00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_R11B_v1_0.md

Then begin the autonomous loop against:
   00_ARCHITECTURE/CONDUCTOR/session_queue_R11B.yaml

Execution: sequential single-stream within R11.B.
Halt policy: STRICT.
Permissions: --dangerously-skip-permissions (inherited).

Queue has 10 entries: B-S0 adapter health check, B-S1..B-S6 visual restyle
(typography / user-bubble / message-container / composer / sidebar / markdown
typescale), B-S7 inline citation parity (extends NumberedCitation + retires
CitationSidePanel), B-S8 brand preservation audit, R11B-MERGE.

CRITICAL file-scope discipline (parallel-safety with stream-2):
- R11.B touches ONLY: UI components, globals.css, NumberedCitation, feature_flags.
- R11.B MUST NEVER touch: platform/src/lib/providers/**, route.ts,
  lib/streaming/**, lib/synthesis/**. Those are stream-2 territory.
- If a sub-agent needs to edit those: halt and ping native via Cowork.

Heartbeat: ✓ R11.B <session_id> passed at <ISO> | Sessions passed: N of 10

Begin now with B-S0.
```

## Halt + complete coordination

If R11.B halts, the native sees the banner here. They open Cowork, paste the banner, Cowork triages, and provides a fresh resume paste-prompt. R11.CDE stream-2 continues running independently — its halts come through separately.

When R11B-MERGE auto-merges to main, the stream-1 work is done. Stream-2 continues until R11E-MERGE.
