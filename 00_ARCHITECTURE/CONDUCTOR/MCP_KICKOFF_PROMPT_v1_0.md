# MCP — Claude Code KICKOFF Prompt v1.0 (REUSABLE)

Paste this into a **fresh Claude Code session** pointed at
`/Users/Dev/Vibe-Coding/Apps/MadhavMCP`, AFTER you've run
`MCP_SETUP_PROMPT_v1_0.md` in the main repo and the worktree exists.

**This prompt is reusable.** If the Conductor halts at any session, paste
this same prompt in a fresh Claude Code session — the disk state picks up
exactly where it left off. No edits needed.

Launch Claude Code with:

```
cd /Users/Dev/Vibe-Coding/Apps/MadhavMCP
claude --dangerously-skip-permissions
```

## What to paste

```
You are the MCP Conductor — the autonomous orchestrator for the MARSYS-JIS
Model Context Protocol Server workstream.

Read these files in order BEFORE doing anything else:

1. CLAUDE.md (full read — your governance orientation)
2. 00_ARCHITECTURE/BRIEFS/MCP_BRIEF_v1_0.md (the master brief — strategic
   spec for what's being built and why)
3. 00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_MCP_v1_0.md (your full role
   specification — defines the loop, sub-agent template, halt/heartbeat
   formats, log schemas, native overrides)

Then begin the autonomous loop against:
   00_ARCHITECTURE/CONDUCTOR/session_queue_MCP.yaml

Worktree:        /Users/Dev/Vibe-Coding/Apps/MadhavMCP
Branch:          feature/mcp-server
Execution mode:  sequential single-stream
Halt policy:     STRICT — halt on first gate failure or sub-agent HALT_NEEDS_HUMAN
Permissions:     --dangerously-skip-permissions (inherited from this session)
Bypass:          skip every permission prompt; trust the gate checks for safety

The queue has 9 entries:
- 1 brief-authoring meta-session (MCP-0-AUTHOR) — sub-agent reads
  MCP_BRIEF_v1_0.md and authors the remaining 7 sub-briefs from it,
  using CLAUDECODE_BRIEF_MCP_1_S1 as the reference standard
- 6 implementation sessions (MCP-1-S1, MCP-2-S1, MCP-2-S2, MCP-3-S1,
  MCP-3-S2, MCP-4-S1)
- 1 red-team session (MCP-4-S2) per §IS.8(b) cadence
- 1 terminal merge entry (MCP-MERGE) which pushes the branch, opens a PR,
  and enables auto-merge per native override (CONDUCTOR_PROMPT_MCP §2)

For each pending eligible entry:
1. Mark in_flight, persist session_queue_MCP.yaml.
2. Spawn a general-purpose sub-agent with the §4 template from
   CONDUCTOR_PROMPT_MCP_v1_0.md (substituting the brief_path, session_id,
   worktree_path, branch).
3. Wait for the sub-agent's FINAL_SUMMARY block.
4. Run the entry's gate_command from the worktree root.
5. If both sub-agent status: PASS AND gate exit 0 → mark passed, append
   PASS entry to CONDUCTOR_LOG.md, emit heartbeat, continue.
6. Otherwise → mark halted, append HALT entry to CONDUCTOR_HALT_LOG.md,
   emit HALT banner, STOP. Wait for the native to RESUME / SKIP / ABANDON
   from their Cowork chat.

Heartbeat format (after each PASS):
   ✓ MCP <session_id> passed at <ISO>
     Sessions passed: <N of 9>  |  Remaining: <M>  |  Next: <next_id>

Begin now with the first pending eligible entry (likely MCP-0-AUTHOR on
a fresh run, or the most-recently-halted entry on a resume).
```

## What the native does while the Conductor runs

The Conductor runs autonomously in Claude Code; the native watches from
their Cowork chat. When the Conductor halts (or completes), it emits a
banner with three options:

- `RESUME <session_id>` — Conductor retries the halted entry
- `SKIP <session_id>` — Conductor marks skipped, advances
- `ABANDON` — Conductor stops permanently

The native issues these by either:
- Going back to the Claude Code session and typing the command, OR
- Telling Cowork (their chat) what to do; Cowork updates
  `session_queue_MCP.yaml` on disk, then the native re-pastes the kickoff
  prompt in a fresh Claude Code session.

The queue state on disk is the source of truth — no information is lost
between Claude Code sessions.

## On context budget

MCP has 9 entries. The Conductor's 20-sub-agent-per-chat cap fits all of
MCP in one Claude Code session with comfortable headroom. If the Conductor
emits an `ORCHESTRATOR HANDOFF` banner before queue close (it shouldn't,
but defensive), open a fresh Claude Code session and re-paste this kickoff
prompt — the disk state picks up where the previous session left off.

## On the auto-merge step (MCP-MERGE)

MCP-MERGE pushes the branch and runs `gh pr merge --auto --squash --delete-branch`.
The PR will auto-merge once CI checks pass. If CI fails, the PR sits open
and the Conductor halts — the native intervenes at that point.

This is an explicit native override of the Wave 1 invariant "PR-to-main
always human-gated" — see `CONDUCTOR_PROMPT_MCP_v1_0.md §2`. The override
is local to MCP only.

## On the brief-authoring session (MCP-0-AUTHOR)

The first entry, MCP-0-AUTHOR, is unusual: instead of touching application
code, it authors the 7 remaining sub-briefs (MCP-2-S1, MCP-2-S2, MCP-3-S1,
MCP-3-S2, MCP-4-S1, MCP-4-S2, MCP-MERGE). This pattern lets Cowork avoid
pre-authoring all sub-briefs in one chat — the Conductor scales it via
sub-agent. Once MCP-0-AUTHOR passes, the rest of the queue runs as normal
implementation sessions.

The sub-agent for MCP-0-AUTHOR uses CLAUDECODE_BRIEF_MCP_1_S1_v1_0.md
(pre-authored by Cowork) as the gold-standard reference for brief style
and depth.
