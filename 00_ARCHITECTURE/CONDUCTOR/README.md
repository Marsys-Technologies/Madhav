# CONDUCTOR — Autonomous Session Orchestrator

Wave 1: Phase 4C Panchang Module autonomy proving ground.
Authored: 2026-05-19, session CONDUCTOR-S0.

---

## §1 — What the Conductor is

The Conductor is an orchestrator that walks `session_queue.yaml`, spawning Claude Code
sub-agents (via the Agent tool) to execute each session's brief autonomously. Each
sub-agent gets a fresh 200K-token context, reads CLAUDE.md + its brief, executes its
scope, commits after every item, and emits a machine-readable FINAL_SUMMARY. The
Conductor reads that summary, runs a gate command (shell test on artifacts), and
decides PASS or HALT. On PASS it advances the queue and loops; on HALT it writes to
`CONDUCTOR_HALT_LOG.md` and stops, waiting for human input.

The Conductor never edits application code. It only manages `session_queue.yaml`,
`CONDUCTOR_LOG.md`, and `CONDUCTOR_HALT_LOG.md`. All real work happens inside sub-agents.

---

## §2 — How to kick off an autonomous run

Open an Antigravity chat window pointed at `/Users/Dev/Vibe-Coding/Apps/Panchang`
(the Panchang worktree, branch `feature/phase-4c-panchang`) and paste:

```
You are the Conductor — the autonomous orchestrator for MARSYS-JIS Wave 1.

Read 00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_v1_0.md fully, then begin the
autonomous loop against 00_ARCHITECTURE/CONDUCTOR/session_queue.yaml.

Worktree: /Users/Dev/Vibe-Coding/Apps/Panchang
Branch: feature/phase-4c-panchang

Begin.
```

The orchestrator will:
1. Read `session_queue.yaml`
2. Find the first eligible pending entry
3. Spawn a sub-agent against that entry's brief
4. Wait for the sub-agent's FINAL_SUMMARY
5. Run the gate command
6. PASS or HALT
7. Loop until queue complete or halt

The first eligible entry is `4C-1-S1` (panchang_engine Python library). It will
halt immediately after because `4C-1-S2` requires brief authoring.

---

## §3 — How to read the logs

**`CONDUCTOR_LOG.md`** — run history. One entry per executed session. Fields:
`session_id`, `result` (PASS/HALT/SKIPPED), `timestamp`, `commits`, `gate_exit_code`,
`gate_output` (500-char cap), `sub_agent_summary`, `scope_items_completed`.

**`CONDUCTOR_HALT_LOG.md`** — open and resolved halts. One entry per halt. Fields:
`session_id`, `failure_class`, `timestamp`, `last_passed`, `queue_position`,
`resolution_status` (open/resumed/skipped/abandoned), `failure_context` (1000-char cap).

Read CONDUCTOR_LOG.md to understand what ran. Read CONDUCTOR_HALT_LOG.md to
understand what is blocked and why.

---

## §4 — How to respond to a halt

When the orchestrator halts, it emits a banner in chat. Three options:

| Command | Effect |
|---|---|
| `RESUME <session_id>` | Re-attempt the halted entry (re-run from the top of the loop) |
| `SKIP <session_id>` | Mark the entry `status: skipped`; orchestrator advances to next eligible |
| `ABANDON` | Stop permanently; orchestrator appends a closing entry to the halt log |

For `requires_brief_authoring` halts: author the brief in Cowork, commit it to
`feature/phase-4c-panchang`, update the queue entry (flip `requires_brief_authoring:
false`, set `brief_path` and `gate_command`), then re-paste the kickoff prompt.
The orchestrator picks up from where it stopped.

---

## §5 — How to add a session to the queue

1. Edit `session_queue.yaml` — add a new entry with all required fields per the schema.
   Required fields: `session_id`, `brief_path`, `branch`, `worktree_path`, `depends_on`,
   `requires_human_approval`, `push_to_remote`, `gate_command`, `status: pending`.

2. Validate: `python3 00_ARCHITECTURE/CONDUCTOR/validate_queue.py` from the worktree root.
   Must exit 0 before continuing.

3. Commit the updated queue with a descriptive message.

4. Author the brief at the `brief_path` you declared, then flip `requires_brief_authoring:
   false` in the queue entry.

---

## §6 — Architectural invariants

| Invariant | Rule |
|---|---|
| Per-session commits autonomous | Sub-agents commit after every scope item; no human approval needed for commits on feature branches |
| PR-to-main always human-gated | Any merge-to-main entry has `requires_human_approval: true`; orchestrator halts |
| Orchestrator never touches app code | Conductor files only: `session_queue.yaml`, log files |
| Fresh context per sub-agent | Each sub-agent gets 200K tokens; disk is the inheritance medium |
| Brief-authoring halts are intentional | Only authored briefs enter the executable path; unreviewed briefs never auto-execute |
| Gate is mandatory for PASS | PASS requires both sub-agent `status: PASS` AND gate command exit 0 |

---

## §7 — Context-budget guards

| Limit | Value | What happens |
|---|---|---|
| Sub-agents per chat | 20 | Orchestrator emits ORCHESTRATOR HANDOFF banner and stops |
| Log appends | Unlimited | Log writes are file ops, not context |

After 20 sessions, re-paste the kickoff prompt in a **fresh** Antigravity chat.
The queue state on disk is the handoff — no information is lost.

---

## §8 — Wave 1 / Wave 2 boundary

Wave 1 queue: `session_queue.yaml` (Phase 4C only, 11 entries).
This Conductor lives on `feature/phase-4c-panchang` alongside Phase 4C work.

**At Wave 1 close**, execute the split-PR strategy:

**PR 1 (Conductor to main):** Cherry-pick only the Conductor commits to main.
See `WAVE_2_MIGRATION_NOTE.md` for the exact procedure.

**PR 2 (Phase 4C to main):** Separate PR with the application-code work.

Wave 2 (M5-A, 4B, 4D) begins after PR 1 lands. The Conductor's queue expands
to cover those workstreams on their own worktrees.

---

## §9 — Known limitations (Wave 1)

- **Wave 1 only.** Queue covers Phase 4C only. Wave 2 is a future Cowork conversation.
- **No inter-worktree mirror discipline.** Orchestrator does not enforce MP.1/MP.2 across
  worktrees. Session briefs declare their own mirror obligations.
- **Brief-authoring halts are expected pause points.** Only `4C-1-S1` has an authored
  brief today. Every subsequent entry halts for Cowork to author the next brief.
- **SMOKE-S0 was the only executed run in CONDUCTOR-S0.** The first real Phase 4C
  autonomous run starts when you paste the kickoff prompt after this session closes.
- **No desktop/email notifications.** Halts emit only to the chat panel.

---

## §10 — Where to look first when something is wrong

```
1. CONDUCTOR_HALT_LOG.md
   → Which entry halted, what failure_class, what the gate said

2. CONDUCTOR_LOG.md
   → What ran before the halt; the sub_agent_summary field

3. git log --oneline -- 00_ARCHITECTURE/CONDUCTOR/
   → Conductor commits in order (clean cherry-pickable path to main)

4. git log --oneline feature/phase-4c-panchang
   → Sub-agent commits mixed in; verify they touch only their declared scope

5. The failing session's brief (brief_path from queue entry)
   → Was the gate_command correct? Does the expected_artifact exist?
```

If the gate command is wrong, fix it in `session_queue.yaml`, validate, commit,
then `RESUME <session_id>` in the next kickoff.

---

*End of CONDUCTOR README — Wave 1 / Phase 4C.*
*Conductor lives at: 00_ARCHITECTURE/CONDUCTOR/*
*Migrate to main at Wave 1 close — see WAVE_2_MIGRATION_NOTE.md.*
