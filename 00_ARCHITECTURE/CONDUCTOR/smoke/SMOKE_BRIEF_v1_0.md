---
artifact: SMOKE_BRIEF_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: READY
session_id: SMOKE-S0
authored_by: Claude Code (Sonnet 4.6, session CONDUCTOR-S0)
authored_on: 2026-05-19
purpose: >
  Conductor end-to-end proof of life. No real work performed — this brief exists
  solely to exercise the orchestrator + sub-agent + gate pattern before the first
  real Phase 4C session runs. If this smoke test passes, the Conductor design is
  structurally sound.
---

# SMOKE_BRIEF — Conductor Proof of Life

## §0 — Scope (one item only)

### Item 1 — Heartbeat file

**What:** Create `00_ARCHITECTURE/CONDUCTOR/smoke/SMOKE_HEARTBEAT.md` with the
following exact content (substituting the actual ISO timestamp):

```
Conductor smoke test heartbeat at <ISO timestamp — e.g. 2026-05-19T14:58:00+05:30>
Session: SMOKE-S0
Branch: feature/phase-4c-panchang
Worktree: /Users/Dev/Vibe-Coding/Apps/Panchang
```

Then commit the file with message exactly: `SMOKE-S0: heartbeat`

**AC.SMOKE.1:**
- File exists at `00_ARCHITECTURE/CONDUCTOR/smoke/SMOKE_HEARTBEAT.md`
- File contains `Conductor smoke test heartbeat at` followed by a timestamp
- A commit on `feature/phase-4c-panchang` with message containing `SMOKE-S0: heartbeat`

---

## §1 — Scope constraints

**may_touch:** `00_ARCHITECTURE/CONDUCTOR/smoke/SMOKE_HEARTBEAT.md` only.

**must_not_touch:** Everything else on the branch — especially:
- Any file outside `00_ARCHITECTURE/CONDUCTOR/smoke/`
- `platform/**`
- `CLAUDE.md`
- Any governance files

This is a minimal proof-of-life brief. Do not clean up, add, or modify anything
beyond the single heartbeat file.

---

## §2 — Session-close

After completing Item 1, emit the FINAL_SUMMARY block per orchestrator prompt §3 template:

```
---FINAL_SUMMARY---
session_id: SMOKE-S0
status: PASS
commits:
  - <sha of the heartbeat commit>
scope_items_completed:
  - AC.SMOKE.1
scope_items_failed: []
gate_command_runs:
  - name: smoke_gate
    result: PASS
notes_for_orchestrator: >
  Smoke test heartbeat file created and committed. SMOKE-S0 brief executed successfully.
  The orchestrator + sub-agent + gate pattern is confirmed working.
human_decision_needed: ""
---END_FINAL_SUMMARY---
```

Begin with Item 1.
