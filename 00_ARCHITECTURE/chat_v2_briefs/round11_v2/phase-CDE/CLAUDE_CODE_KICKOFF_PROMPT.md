# R11.CDE Composite — Claude Code KICKOFF Prompt

Paste this into a **fresh Antigravity Claude Code session** pointed at `/Users/Dev/Vibe-Coding/Apps/MadhavR11CDE`, launched with `claude --dangerously-skip-permissions`.

This is **stream-2** of Pattern 2+ — concurrent with R11.B stream-1.

## What to paste

```
You are the R11.CDE Conductor — orchestrating the composite phase covering
R11.C (Streaming + Thinking), R11.D (Caching), and R11.E (Adaptive Tool
Sequencing). 27 entries total walked sequentially in one worktree.

You operate inside MadhavR11CDE worktree at /Users/Dev/Vibe-Coding/Apps/MadhavR11CDE
on working branch chat-v2/round11-cde. Three intermediate MERGE entries
(R11C-MERGE, R11D-MERGE, R11E-MERGE) push separate sub-branches to main as
the queue advances.

This is stream-2 of Pattern 2+. Stream-1 (R11.B Look-and-Feel) runs
concurrently in a separate Antigravity session at /Users/Dev/Vibe-Coding/Apps/MadhavR11B.
No coordination during execution; both streams merge to main independently.

Read in order BEFORE doing anything else:

1. CLAUDE.md
2. 00_ARCHITECTURE/USER_INTERACTION_PREFERENCES.md
3. 00_ARCHITECTURE/CAPABILITY_MATRIX.md
4. 00_ARCHITECTURE/MULTI_PROVIDER_PARITY_ROADMAP.md
5. 00_ARCHITECTURE/chat_v2_briefs/round11_v2/R11V2_MASTER_PLAN_v1_0.md
6. 00_ARCHITECTURE/chat_v2_briefs/round11/NATIVE_RULINGS_v1_0.md
7. 00_ARCHITECTURE/chat_v2_briefs/round11_v2/phase-CDE/R11CDE_PLAN_v1_0.md
8. 00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_R11CDE_v1_0.md

Then begin the autonomous loop against:
   00_ARCHITECTURE/CONDUCTOR/session_queue_R11CDE.yaml

Execution: sequential within phase; phases walk in order C → R11C-MERGE → D
→ R11D-MERGE → E → R11E-MERGE.
Halt policy: STRICT.
Permissions: --dangerously-skip-permissions (inherited).

CRITICAL file-scope discipline (parallel-safety with stream-1):
- Stream-2 touches: platform/src/lib/providers/**, route.ts, streaming/,
  synthesis/, observatory/, ToolCallCard.tsx, ReasoningProgress.tsx,
  PreTokenIndicator.tsx, feature_flags.ts.
- Stream-2 MUST NEVER touch: UI components (AssistantMessage, UserMessage,
  MarkdownContent, Composer, MessageActionBar, NumberedCitation,
  ConversationSidebarV2), globals.css. Those are stream-1 territory.
- If a sub-agent needs to edit those: halt and ping native via Cowork.

Heartbeat:
   ✓ R11.CDE <phase>.<session_id> passed at <ISO>
     Sessions passed: <N of 27>  |  Phase: <R11.C|R11.D|R11.E>  |  Next: <next_id>

Begin now with C-S0.
```

## Halt + complete coordination

If R11.CDE halts, the native sees the banner. They open Cowork, paste it, Cowork triages and provides a resume paste-prompt. Stream-1 (R11.B) continues independently.

When R11E-MERGE auto-merges to main, stream-2 is complete. Both streams' arc terminus is when R11B-MERGE (stream-1) and R11E-MERGE (stream-2) have both landed in main.
