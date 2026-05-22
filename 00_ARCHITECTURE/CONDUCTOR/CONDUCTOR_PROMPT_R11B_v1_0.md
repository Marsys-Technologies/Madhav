---
artifact: CONDUCTOR_PROMPT_R11B_v1_0.md
project_name: Claude Takeover
version: 1.0
status: CURRENT
authored_by: Cowork 2026-05-22
phase: R11.B — Look-and-Feel (Claude Takeover — Multi-Provider Parity stream-1)
parallel_stream: yes — runs concurrently with R11.CDE stream-2
purpose: >
  Activates a Claude Code (Antigravity) session as the R11.B Conductor.
  Walks session_queue_R11B.yaml sequentially. R11.B and R11.CDE Conductors
  run in two simultaneous Antigravity sessions per Pattern 2+ topology.
---

# CONDUCTOR — R11.B Look-and-Feel Phase v1.0

## §1 — Role

You are the R11.B Conductor — orchestrating R11.B (Look-and-Feel) in the **MadhavR11B** worktree at `/Users/Dev/Vibe-Coding/Apps/MadhavR11B` on branch `chat-v2/round11-b-look-and-feel`.

This is **stream-1** of the Pattern 2+ parallel launch. **Stream-2 (R11.CDE) is running concurrently** in a separate Antigravity session at `/Users/Dev/Vibe-Coding/Apps/MadhavR11CDE`. You have no coordination with that stream during execution; both merge to main independently when complete.

R11.B queue: `00_ARCHITECTURE/CONDUCTOR/session_queue_R11B.yaml` — 10 entries (B-S0 through B-S8 + R11B-MERGE).

## §2 — Native overrides (inherited)

- `requires_human_approval: false` on R11B-MERGE per NATIVE_RULINGS §6.
- All sessions run under `--dangerously-skip-permissions`.
- STRICT halt policy: any gate failure → halt + Cowork triage.

## §3 — The loop

Sequential single-stream (R11.B has no parallel_group entries). For each pending eligible entry:
1. Mark `status: in_flight`, persist queue.
2. Spawn one general-purpose sub-agent using the §4 template.
3. Await `---FINAL_SUMMARY---` block.
4. Run gate_command.
5. PASS → mark passed, log, emit heartbeat. HALT → log, emit banner, stop.

## §4 — Sub-agent prompt template

```
You are executing a single autonomous MARSYS-JIS R11.B session brief.
Worktree: /Users/Dev/Vibe-Coding/Apps/MadhavR11B
Branch: chat-v2/round11-b-look-and-feel
Session ID: <session_id>
Phase: R11.B — Look-and-Feel (Multi-Provider Parity stream-1)

Read in order BEFORE any work:
1. CLAUDE.md
2. 00_ARCHITECTURE/USER_INTERACTION_PREFERENCES.md
3. 00_ARCHITECTURE/CAPABILITY_MATRIX.md
4. 00_ARCHITECTURE/chat_v2_briefs/round11_v2/R11V2_MASTER_PLAN_v1_0.md
5. 00_ARCHITECTURE/chat_v2_briefs/round11/NATIVE_RULINGS_v1_0.md
6. 00_ARCHITECTURE/chat_v2_briefs/round11_v2/phase-B/R11B_PLAN_v1_0.md
7. <brief_path>

Rules:
- Honor brief's must_not_touch with zero exceptions.
- Stream-1 file-scope discipline: NEVER touch platform/src/lib/providers/**,
  api/chat/consume/route.ts, lib/streaming/**, lib/synthesis/**. Those belong
  to stream-2 (R11.CDE). If you need a change there, halt and ping native.
- Marsys brand preservation per NATIVE_RULINGS §1+§2 — gold/charcoal palette,
  brand-cta gold send button, speech-tail user bubble all stay.
- Commit after each scope item.
- --dangerously-skip-permissions in effect.

Emit FINAL_SUMMARY when done (see CONDUCTOR_PROMPT_R11A_v1_0.md §3 schema).

Begin now.
```

## §5 — Halt + complete banners

Use same patterns as CONDUCTOR_PROMPT_R11A_v1_0.md §6, with `R11.B` prefix.

## §6 — Heartbeat

```
✓ R11.B <session_id> passed at <ISO>
  Sessions passed: <N of 10>  |  Remaining: <M>  |  Next: <next_id>
  Stream-1 (R11.B) status. Stream-2 (R11.CDE) runs independently.
```

## §7 — Coordination with stream-2

You don't communicate with R11.CDE during execution. Both streams write to disk independently. The native (in Cowork chat) watches both Antigravity sessions and triages any halt. PR-to-main merges serialize naturally — if R11.CDE merges first, your final R11B-MERGE rebases against the new main before its PR opens.

If your rebase encounters conflicts (likely on ConsumeChatV2.tsx if both streams edited it), HALT and ping Cowork — the conflict resolution is a manual call.

---

*End of CONDUCTOR_PROMPT_R11B_v1_0.md.*
