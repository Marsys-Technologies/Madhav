# R11 — Claude Code KICKOFF Prompt

Paste this into a **fresh Claude Code session** pointed at
`/Users/Dev/Vibe-Coding/Apps/MadhavR11`, AFTER you've run `CLAUDE_CODE_SETUP_PROMPT.md`
in the main repo and the worktree is set up.

Launch Claude Code with:

```
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11
claude --dangerously-skip-permissions
```

(or whichever equivalent flag your Claude Code version uses to bypass per-action
permission prompts. With this flag the Conductor's sub-agents inherit
write/exec permissions in the worktree.)

## What to paste

```
You are the R11 Conductor — the autonomous orchestrator for MARSYS-JIS R11
(Chat V2 → Claude Parity).

Read these files in order BEFORE doing anything else:

1. CLAUDE.md (full read — your governance orientation)
2. 00_ARCHITECTURE/chat_v2_briefs/round11/NATIVE_RULINGS_v1_0.md
   (LOCKED native rulings — these override any conflicting language in briefs)
3. 00_ARCHITECTURE/chat_v2_briefs/round11/R11_MASTER_PLAN_v1_0.md
4. 00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_R11_v1_0.md (your full role spec)

Then begin the autonomous loop against:
   00_ARCHITECTURE/CONDUCTOR/session_queue_R11.yaml

Worktree: /Users/Dev/Vibe-Coding/Apps/MadhavR11
Branch:   chat-v2/round11-claude-parity
Execution mode: sequential single-stream
Halt policy: STRICT — halt on first gate failure or sub-agent HALT_NEEDS_HUMAN
Permissions: --dangerously-skip-permissions (inherited from this session)
Bypass: skip every permission prompt; trust the gate checks for safety

The queue has 17 entries:
- 16 implementation sessions (V-S1..V-S6, S-S1..S-S5, O-S1..O-S5)
- 1 terminal merge entry (R11-MERGE) which pushes the branch, opens a PR, and
  enables auto-merge to main per native override (NATIVE_RULINGS §6)

For each pending eligible entry:
1. Mark in_flight, persist session_queue_R11.yaml.
2. Spawn a general-purpose sub-agent with the §4 template from
   CONDUCTOR_PROMPT_R11_v1_0.md (substituting the brief_path, session_id,
   worktree_path, branch).
3. Wait for the sub-agent's FINAL_SUMMARY block.
4. Run the entry's gate_command from the worktree root.
5. If both sub-agent status: PASS AND gate exit 0 → mark passed, append
   PASS entry to CONDUCTOR_LOG.md, emit heartbeat, continue.
6. Otherwise → mark halted, append HALT entry to CONDUCTOR_HALT_LOG.md,
   emit HALT banner, STOP. Wait for me (the native) to RESUME / SKIP / ABANDON
   from my Cowork chat (I'm watching).

Heartbeat format (after each PASS):
   ✓ R11 <session_id> passed at <ISO>
     Sessions passed: <N of 17>  |  Remaining: <M>  |  Next: <next_id>

Begin now with V-S1.
```

## What I (the native) do while the Conductor runs

The Conductor runs in Claude Code; I watch from this Cowork chat. When the
Conductor halts (or completes), it emits a banner with three options:

- `RESUME <session_id>` — Conductor retries the halted entry
- `SKIP <session_id>` — Conductor marks skipped, advances
- `ABANDON` — Conductor stops permanently

I issue these by either:
- Going back to the Claude Code session and typing the command, OR
- Telling Cowork (this chat) what to do; Cowork updates `session_queue_R11.yaml`
  on disk, then I re-paste the kickoff prompt in a fresh Claude Code session.

The queue state on disk is the source of truth — no information is lost between
Claude Code sessions.

## On context budget

R11 has 17 entries. The Conductor's 20-sub-agent-per-chat cap should fit all of
R11 in one Claude Code session. If the Conductor emits an
`ORCHESTRATOR HANDOFF` banner before queue close (it shouldn't), open a fresh
Claude Code session and re-paste this kickoff prompt — the disk state picks up
where the previous session left off.

## On the auto-merge step

R11-MERGE pushes the branch and runs `gh pr merge --auto --squash --delete-branch`.
The PR will auto-merge once CI checks pass. If CI fails, the PR sits open and
the Conductor halts — I (the native) intervene at that point.

This is an explicit native override of the Wave 1 invariant "PR-to-main always
human-gated" — see `NATIVE_RULINGS §6`. The override is local to R11 only.

## On Marsys brand preservation

The `.consume-shell` brand identity (gold-on-charcoal, brand-gold accent, gold-
hairline borders, glassmorphic speech-tail user bubble) is **preserved**.
Claude rendering is layered inside it (fonts, markdown scale, message shape,
chrome dimensions, citation idiom). The single flag
`MARSYS_FLAG_R11_CLAUDE_RENDERING` (default false, NEXT_PUBLIC) gates the
V-group visual changes; flip to true at V-S6 close to verify parity.
