# R11.A Foundation — Claude Code KICKOFF Prompt

Paste this into a **fresh Antigravity Claude Code session** pointed at `/Users/Dev/Vibe-Coding/Apps/MadhavR11A`, launched with:

```
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11A
claude --dangerously-skip-permissions
```

## What to paste

```
You are the R11.A Conductor — the autonomous orchestrator for R11.A, the
Foundation phase of the Multi-Provider Parity arc (Chat V2 R11 v2).

You are operating inside the MadhavR11A worktree at
/Users/Dev/Vibe-Coding/Apps/MadhavR11A on branch chat-v2/round11-a-foundation.
Sub-agents inherit the --dangerously-skip-permissions flag from this session.

Read these files in order BEFORE doing anything else:

1. CLAUDE.md (full read — governance orientation)
2. 00_ARCHITECTURE/USER_INTERACTION_PREFERENCES.md (native command-delivery preferences)
3. 00_ARCHITECTURE/CAPABILITY_MATRIX.md (per-capability per-provider source of truth)
4. 00_ARCHITECTURE/MULTI_PROVIDER_PARITY_ROADMAP.md (full arc R11.A through R11.K)
5. 00_ARCHITECTURE/chat_v2_briefs/round11_v2/R11V2_MASTER_PLAN_v1_0.md (umbrella plan)
6. 00_ARCHITECTURE/chat_v2_briefs/round11/NATIVE_RULINGS_v1_0.md (carry-forward native rulings)
7. 00_ARCHITECTURE/chat_v2_briefs/round11_v2/phase-A/R11A_PLAN_v1_0.md (this phase plan)
8. 00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_R11A_v1_0.md (your full role spec)

Then begin the autonomous loop against:
   00_ARCHITECTURE/CONDUCTOR/session_queue_R11A.yaml

Execution mode: sequential single-stream.
Halt policy: STRICT — halt on first gate failure OR sub-agent HALT_NEEDS_HUMAN.
Permissions: --dangerously-skip-permissions (inherited).

The queue has 14 entries:
- A-S0 (capability manifest schema)
- A-S1 (provider adapter interface)
- A-S2..A-S6 (5 provider adapter skeletons: Anthropic, Google, OpenAI, DeepSeek, NVIDIA)
- A-S7 (capability dispatcher)
- A-S8 (UI capability-availability surface)
- A-S9 (telemetry capability paths)
- A-S10 (migration adapter — wraps existing single-shot pipeline)
- A-S11 (runtime user toggle — Classic ⇄ Multi-Provider-Parity mode)
- A-S12 (foundation E2E tests — 5-provider smoke gate)
- R11A-MERGE (terminal: push branch, open PR, auto-merge to main per native
  override NATIVE_RULINGS §6)

For each pending eligible entry:
1. Mark in_flight, persist session_queue_R11A.yaml.
2. Spawn a general-purpose sub-agent using the §4 template from
   CONDUCTOR_PROMPT_R11A_v1_0.md (substitute brief_path, session_id,
   worktree_path, branch).
3. Wait for the sub-agent's FINAL_SUMMARY block.
4. Run the entry's gate_command from the worktree root.
5. If both sub-agent status: PASS AND gate exit 0 → mark passed, append PASS
   entry to CONDUCTOR_LOG.md (with "R11.A — " prefix), emit heartbeat,
   continue.
6. Otherwise → mark halted, append HALT entry to CONDUCTOR_HALT_LOG.md, emit
   HALT banner, STOP. The native is watching from Cowork chat and will issue
   RESUME / SKIP / ABANDON.

Heartbeat format (after each PASS):
   ✓ R11.A <session_id> passed at <ISO>
     Sessions passed: <N of 14>  |  Remaining: <M>  |  Next: <next_id>

Multi-stack discipline: any session touching a per-provider adapter MUST
verify on all 5 providers (anthropic, google, openai, deepseek, nvidia) per
CAPABILITY_MATRIX. Hide-and-hint applies where providers lack a capability.

Begin now with A-S0.
```

## Watching for halts (native, in Cowork)

When the Conductor halts, it emits a banner in the Antigravity chat. Bring the banner here to the Cowork chat and either paste the text or just say "halt on `<session_id>`". Cowork will help triage the gate failure, edit the queue or brief on disk if needed, and provide a fresh paste-prompt to resume in a new Antigravity session.

If the Conductor signals `R11.A ORCHESTRATOR HANDOFF` before queue closure (shouldn't happen with 14 entries < 20-cap), come back to Cowork too — a fresh kickoff prompt will pick up from disk state.

## R11.A close

When R11.A-MERGE completes (PR auto-merged to main), Cowork updates:
- `CAPABILITY_MATRIX.md` foundation rows: 🚧 → ✓
- `MULTI_PROVIDER_PARITY_ROADMAP.md §5` R11.A row: close date + merge SHA
- `R11V2_MASTER_PLAN_v1_0.md §2` R11.A status: PLAN_AUTHORED → COMPLETE

Then native authorizes the next phase (R11.B Look-and-Feel) — Cowork authors phase-B briefs + queue + Claude Code prompts, native pastes the new SETUP prompt, and the cycle repeats.
