---
artifact: CLAUDECODE_BRIEF_CONDUCTOR_S0_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: READY
authored_by: Cowork 2026-05-19
authored_at: 2026-05-19
amended_at: 2026-05-19 (in-place — worktree co-location with Phase 4C; split-PR strategy at Wave 1 close)
session_id: CONDUCTOR-S0
session_name: CONDUCTOR-S0 — Orchestrator Scaffold + Queue Manifest + Smoke Test
executor: Claude Code (VS Code extension / Antigravity)
execution_mode: single session, --dangerously-skip-permissions
worktree:
  name: Panchang (shared with Phase 4C workstream — see §11 for Wave 2 migration)
  branch: feature/phase-4c-panchang
  base: main
  path_absolute: /Users/Dev/Vibe-Coding/Apps/Panchang
governing_design: Cowork conversation 2026-05-19 (Conductor architecture established with native)
predecessor_session: 4C-0 close (Phase 4C governance sealed 2026-05-19; 10 commits on feature/phase-4c-panchang ending at f965486)
target_wave: Wave 1 — Phase 4C autonomy proving ground
next_session_anticipated: First autonomous Conductor run (user-triggered, picks 4C-1-S1 from queue)
---

# CLAUDECODE_BRIEF — CONDUCTOR-S0
## Build the Orchestrator: Queue Manifest + Orchestrator Prompt + Halt Log + Smoke Test

**Worktree co-location:** This session runs in the existing Panchang worktree at `/Users/Dev/Vibe-Coding/Apps/Panchang` on branch `feature/phase-4c-panchang` — the same branch that just closed 4C-0 and is the home for the remaining Phase 4C campaign. Conductor artifacts ride along with Phase 4C until Wave 1 close, at which point the Conductor commits cherry-pick to main as a small standalone PR ahead of the Phase 4C close PR. Rationale and migration plan in §10 and §11.

---

## §0 — How to start this session

**Step 1 — Confirm you're in the Panchang worktree on the right branch (paste in your terminal):**

```bash
cd /Users/Dev/Vibe-Coding/Apps/Panchang
git status
# Expected: On branch feature/phase-4c-panchang, working tree clean,
#           HEAD at f965486 (4C-0 final commit) or later

git worktree list
# Expected: at least two entries — Madhav (the canonical clone) and Panchang (here)
```

If your worktree is not on `feature/phase-4c-panchang`, halt and resolve before proceeding. This session must NOT create a new worktree or a new branch.

**Step 2 — Stage this brief into the Panchang worktree and activate it:**

```bash
cd /Users/Dev/Vibe-Coding/Apps/Panchang

mkdir -p 00_ARCHITECTURE/CONDUCTOR    # BRIEFS/ already exists from 4C-0

cp ../Madhav/00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_CONDUCTOR_S0_v1_0.md \
   ./00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_CONDUCTOR_S0_v1_0.md

cp ./00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_CONDUCTOR_S0_v1_0.md ./CLAUDECODE_BRIEF.md

git add 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_CONDUCTOR_S0_v1_0.md CLAUDECODE_BRIEF.md
git commit -m "CONDUCTOR-S0: stage brief as session dispatcher"
```

**Step 3 — In the Antigravity window already pointed at `/Users/Dev/Vibe-Coding/Apps/Panchang`, launch Claude Code with `--dangerously-skip-permissions` and paste:**

```
Read CLAUDE.md per §C, then read CLAUDECODE_BRIEF.md and execute it.
You are in the Panchang worktree at /Users/Dev/Vibe-Coding/Apps/Panchang
on branch feature/phase-4c-panchang (which is also the Phase 4C branch).
Active session: CONDUCTOR-S0. Execute all 10 scope items in §3 in order.
This session BUILDS the Conductor; it does NOT yet run any autonomous
executions outside the smoke test in Item 7. Commit after each scope item.
Honor §5 must_not_touch strictly — Phase 4C source code on this branch
is OFF LIMITS for this session.
```

---

## §1 — Session identity

| Field | Value |
|---|---|
| Session ID | CONDUCTOR-S0 |
| Cowork thread name | `CONDUCTOR-S0 Orchestrator Scaffold 2026-05-19` |
| Branch | `feature/phase-4c-panchang` (shared with Phase 4C campaign) |
| Worktree path | `/Users/Dev/Vibe-Coding/Apps/Panchang` |
| Execution mode | Single session, `--dangerously-skip-permissions` |
| Build target | Wave 1 Conductor — Phase 4C autonomy only |
| Co-location rationale | One worktree, one branch, no IDE-window switching during Phase 4C. Conductor escapes to main via cherry-pick PR at Wave 1 close (see §10 + §11). |
| Anticipated next | First autonomous Conductor run (user-triggered against the populated queue) |

---

## §2 — Mandatory reads at session open (in order)

1. `CLAUDE.md` (§C mandatory list — full read; understand the canonical project shape)
2. `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` §2 (active state — Phase 4C ACTIVE, sub-phase 4C-1 OPEN, 4C-0 CLOSED)
3. `00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md` §C.1–§C.6 + §K (the protocol the Conductor must respect on every session)
4. `00_ARCHITECTURE/SESSION_OPEN_TEMPLATE_v1_0.md` + `00_ARCHITECTURE/SESSION_CLOSE_TEMPLATE_v1_0.md` (the templates every autonomous session must satisfy)
5. `00_ARCHITECTURE/PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md` §6 (the Wave 1 session list — for populating the queue)
6. `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PHASE_4C_1_S1_v1_0.md` (the one Phase 4C session brief with `status: READY`; the orchestrator's first real spawn will be this one)
7. `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M5A_S1_v1_0.md` (the long-form brief pattern — for understanding session shape; do NOT touch any M5-A files in this session)
8. The Phase 4C source code already on this branch from 4C-0 (`ls platform/sidecar/` if it exists yet, `ls 03_DERIVATIONS/`, etc.) — read to know what's HERE so you don't accidentally touch it

Then emit SESSION_OPEN per `SESSION_OPEN_TEMPLATE_v1_0.md`.

---

## §3 — Scope (10 items — execute in order; commit after each)

### Item 1 — Create the Conductor directory + scaffold files

**What:** Create `00_ARCHITECTURE/CONDUCTOR/` with the following empty-or-skeleton files. Touch each, commit the empty scaffold, then populate them across subsequent items.

```
00_ARCHITECTURE/CONDUCTOR/
  README.md                       # Item 8
  CONDUCTOR_PROMPT_v1_0.md        # Item 2
  session_queue.yaml              # Item 3
  CONDUCTOR_LOG.md                # Item 4 (append-only run log)
  CONDUCTOR_HALT_LOG.md           # Item 4 (append-only halt log)
  WAVE_2_MIGRATION_NOTE.md        # Item 8 (cherry-pick-to-main reminder)
  CLAUDE_MD_AMENDMENT_PROPOSAL.md # Item 9 (deferred apply)
  schemas/
    queue_entry_schema.json       # Item 5 (machine-readable schema)
    halt_entry_schema.json        # Item 5
  smoke/
    SMOKE_BRIEF_v1_0.md           # Item 6
    smoke_queue.yaml              # Item 6 (single-entry queue for smoke test)
  validate_queue.py               # Item 5 (the validator)
```

**AC.CONDUCTOR-S0.1:** Directory + skeleton files exist; commit message reads `CONDUCTOR-S0 Item 1: scaffold Conductor directory`.

### Item 2 — Author `CONDUCTOR_PROMPT_v1_0.md` (the orchestrator's system prompt)

**What:** This file is the meta-prompt that puts a Claude Code session into "orchestrator mode." When the user pastes a kickoff prompt referencing this file, Claude Code reads it and starts walking the queue. Content sections:

**§1 — Role**

> You are the Conductor — the orchestrator of autonomous Claude Code sessions for the MARSYS-JIS project. You do not write application code or governance prose directly. You read the queue manifest, decide which session runs next, spawn a sub-agent (via the Task tool) to execute that session's brief, validate the result, advance the queue, and loop. You halt cleanly when a session fails its gate or when an entry requires human approval.

**§2 — The loop (executed every iteration)**

1. Read `session_queue.yaml`. Find the first entry where:
   - `status` is `pending`
   - All `depends_on` entries have `status: passed` or `status: skipped`
   - `requires_external_gate` (if present) is satisfied (e.g., calendar gate met, acharya panel ≥3)
2. If no eligible entry exists: emit `QUEUE COMPLETE` banner, append a closing entry to `CONDUCTOR_LOG.md`, stop.
3. If the eligible entry has `requires_human_approval: true`: emit `HUMAN APPROVAL REQUIRED` banner with the entry's `human_decision_prompt`, append a halt entry to `CONDUCTOR_HALT_LOG.md`, stop. Wait for user to reply with `APPROVE <session_id>` or `SKIP <session_id>` and re-paste the kickoff prompt.
4. Mark the entry `status: in_flight`; persist `session_queue.yaml`.
5. Construct the sub-agent prompt from the entry's `brief_path` and a fixed prefix (see §3 below).
6. Call the Task tool with `subagent_type: "general-purpose"` and the constructed prompt. Wait for the sub-agent to return its final summary.
7. Run the entry's `gate_command` (Bash). Capture stdout, stderr, exit code.
8. Decide:
   - Exit 0 AND sub-agent returned a structured summary with `status: PASS` → mark entry `status: passed`; append `CONDUCTOR_LOG.md` entry with commit hash, gate output, sub-agent summary; persist queue; continue loop.
   - Exit non-zero OR sub-agent returned `status: HALT_NEEDS_HUMAN` → mark entry `status: halted`; append `CONDUCTOR_HALT_LOG.md` entry with full failure context; emit conspicuous banner in chat (see §5 below); stop loop. Do NOT advance.
9. After each successful session, emit a heartbeat: `✓ <session_id> passed at <timestamp>. <N> sessions passed, <M> remaining. Next: <next_session_id>.`
10. If the heartbeat counter hits a multiple of 10, queue a maintenance entry (run `anthropic-skills:consolidate-memory` skill against MEMORY.md; check CLAUDE.md §E for completed-workstream entries that should archive; rotate SESSION_LOG.md if over size budget).

**§3 — Sub-agent prompt template**

```
You are executing a single session brief autonomously. Read these files in order:
1. CLAUDE.md (§C mandatory reads)
2. <brief_path>

Then execute the brief. You have a fresh context. Past sessions are gone from
your memory — what you need to know is on disk. Read what the brief tells you
to read; do NOT read files outside the brief's §2 mandatory list unless the
work itself requires it; honor the brief's §5 must_not_touch list strictly.

You operate under --dangerously-skip-permissions. Commit after each scope item
with descriptive messages. When done, emit a FINAL SUMMARY in this exact
machine-readable form (last message before termination):

---FINAL_SUMMARY---
session_id: <from brief frontmatter>
status: PASS | HALT_NEEDS_HUMAN
commits: <list of commit SHAs in order>
scope_items_completed: <list of AC IDs>
scope_items_failed: <list of AC IDs, or empty>
gate_command_runs: <list of gate-command names run, with PASS/FAIL>
notes_for_orchestrator: <one-paragraph plain text — what to know about this run>
human_decision_needed: <empty if PASS; one-paragraph question if HALT>
---END_FINAL_SUMMARY---

Begin now.
```

**§4 — Queue eligibility logic**

Explicit pseudocode for the eligibility check; covers `depends_on` (other session_ids), `requires_external_gate` (named gates like `phase_4b_closed` or `acharya_panel_assembled`), and `requires_human_approval` (always halts before execution).

**§5 — Halt banner format**

When halting, emit in chat panel:

```
🛑 CONDUCTOR HALT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
session_id:     <id>
failure_class:  <gate_failed | sub_agent_halt | human_approval_required>
timestamp:      <ISO>
last_passed:    <prior session_id>
queue_remaining: <count>

Reason:
<one-paragraph reason>

To resume:
  RESUME <session_id>   — orchestrator retries this entry
  SKIP <session_id>     — orchestrator marks skipped + advances
  ABANDON               — orchestrator stops permanently

Halt details in: 00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_HALT_LOG.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**§6 — Constraints on the orchestrator itself**

- Orchestrator NEVER edits application code. Only queue/log files.
- Orchestrator NEVER pushes to remote unless an entry explicitly has `push_to_remote: true`.
- Orchestrator NEVER merges to main. PR-to-main entries always have `requires_human_approval: true`.
- Orchestrator NEVER runs more than 20 sub-agents in one chat session (context-budget guard — see §7).
- After 20 sessions or 150K orchestrator-context tokens used (whichever first), orchestrator emits `ORCHESTRATOR HANDOFF` banner — user pastes kickoff again in a fresh Antigravity chat to continue.

**§7 — Context budget**

The orchestrator's own context is finite. Each sub-agent summary consumes ~2K tokens (FINAL_SUMMARY block + Task tool overhead). Queue YAML read is ~5K tokens. Log appends are file ops, not context-consuming. Realistic ceiling: 20 sub-agents per orchestrator session before context fills. After Wave 1's ~20 sessions, the user re-kicks; Wave 2 (eventually) will need automatic orchestrator handoff.

**AC.CONDUCTOR-S0.2:** `CONDUCTOR_PROMPT_v1_0.md` exists with sections §1–§7; total length 400–600 lines; commit message reads `CONDUCTOR-S0 Item 2: author orchestrator system prompt`.

### Item 3 — Author `session_queue.yaml` (Wave 1: Phase 4C only)

**What:** Populate the queue manifest with all remaining Phase 4C sessions. Schema:

```yaml
schema_version: 1.0
queue_name: wave_1_phase_4c
generated_at: 2026-05-19
generated_by: CONDUCTOR-S0
total_entries: 9   # 4C-1-S1 through 4C-9

entries:
  - session_id: 4C-1-S1
    brief_path: 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PHASE_4C_1_S1_v1_0.md
    branch: feature/phase-4c-panchang
    worktree_path: /Users/Dev/Vibe-Coding/Apps/Panchang
    depends_on: []
    requires_external_gate: null
    requires_human_approval: false
    push_to_remote: false
    gate_command: |
      cd /Users/Dev/Vibe-Coding/Apps/Panchang/platform/sidecar/panchang_engine && \
      pytest -v tests/test_drik_parity.py && \
      python ../../../platform/scripts/governance/schema_validator.py
    expected_artifacts:
      - platform/sidecar/panchang_engine/__init__.py
      - platform/sidecar/panchang_engine/angas.py
      - platform/sidecar/panchang_engine/tests/fixtures/drik_panchang_v1.json
    est_tokens: 120000
    est_duration_min: 90
    status: pending
    human_decision_prompt: null

  - session_id: 4C-1-S2
    brief_path: 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PHASE_4C_1_S2_v1_0.md
    # NOTE: brief does not yet exist. Authored by Cowork after 4C-1-S1 closes.
    # Conductor will halt at this entry with requires_brief_authoring: true
    branch: feature/phase-4c-panchang
    worktree_path: /Users/Dev/Vibe-Coding/Apps/Panchang
    depends_on: [4C-1-S1]
    requires_brief_authoring: true   # special flag: halt for Cowork to author
    requires_human_approval: true
    gate_command: ""
    status: pending
    human_decision_prompt: |
      4C-1-S1 has closed. Cowork session needed to author CLAUDECODE_BRIEF_PHASE_4C_1_S2_v1_0.md
      covering: special_yogas implementation, Drik fixture extension 10→30 days,
      muhurat scoring scaffold.

  # ... entries for 4C-1-S3, 4C-2 through 4C-9 follow the same pattern.
  # For Wave 1, only 4C-1-S1 has its brief authored. Subsequent entries are
  # placeholders that halt for brief authoring as each predecessor closes.
  # All entries use branch: feature/phase-4c-panchang and
  # worktree_path: /Users/Dev/Vibe-Coding/Apps/Panchang.
```

**Wave 1 queue entries to author:** 4C-1-S1 (executable now), 4C-1-S2 through 4C-1-S3 (placeholders, brief authoring halts), 4C-2 (placeholder, depends on 4C-1 close AND `requires_external_gate: phase_4b_closed`), 4C-3 through 4C-9 (placeholders, sequential deps).

External gate definitions in a `external_gates:` block at the top of the YAML:

```yaml
external_gates:
  phase_4b_closed:
    description: Phase 4B ephemeris sunrise + MEAN_NODE rebuild must close before 4C.2 backfill.
    check_command: |
      cd /Users/Dev/Vibe-Coding/Apps/Madhav && \
      grep -q "PHASE_4B.*CLOSED" 00_ARCHITECTURE/CURRENT_STATE_v1_0.md
    blocker_human_prompt: |
      Phase 4B is still PENDING. 4C.2 (Cloud SQL panchang_daily schema + backfill)
      requires the rebuilt ephemeris_daily with MEAN_NODE Rahu. Defer 4C.2 until
      4B closes, or explicitly approve 4C.2 with the legacy TRUE_NODE ephemeris
      (not recommended — known bug).
```

**AC.CONDUCTOR-S0.3:** `session_queue.yaml` exists with 9 entries for Phase 4C; only 4C-1-S1 has a real `brief_path` + `gate_command`; remaining entries are placeholder-status with `requires_brief_authoring: true` or `requires_external_gate` set; YAML validates against `schemas/queue_entry_schema.json`; commit message reads `CONDUCTOR-S0 Item 3: populate Wave 1 queue manifest`.

### Item 4 — Author `CONDUCTOR_LOG.md` and `CONDUCTOR_HALT_LOG.md` templates

**What:** Both are append-only Markdown files. Each entry follows a fixed schema (also captured in `schemas/halt_entry_schema.json`).

`CONDUCTOR_LOG.md` template (top-of-file):

```markdown
# CONDUCTOR Run Log

Append-only record of every Conductor-driven session execution. Read top-down
for the most recent run.

## Schema
Each entry has: timestamp, session_id, result (PASS/HALT/SKIPPED),
sub-agent summary, gate output (truncated to 500 chars if longer), commits,
context-budget snapshot.

---
```

`CONDUCTOR_HALT_LOG.md` template (top-of-file):

```markdown
# CONDUCTOR Halt Log

Append-only record of every halt the orchestrator emitted. Read top-down for
the most recent halt. Resolution status updated in-place per entry.

## Schema
Each entry has: timestamp, session_id, failure_class
(gate_failed | sub_agent_halt | human_approval_required | requires_brief_authoring),
queue position, last passed session_id, full failure context (1000-char cap on
sub-agent stderr; full gate stdout), suggested resolution paths, resolution_status
(open | resumed | skipped | abandoned).

---
```

**AC.CONDUCTOR-S0.4:** Both files exist with templates; commit message reads `CONDUCTOR-S0 Item 4: log file templates`.

### Item 5 — Author JSON schemas for queue + halt entries

**What:** `00_ARCHITECTURE/CONDUCTOR/schemas/queue_entry_schema.json` and `halt_entry_schema.json`. Standard JSON Schema (draft-07). Includes type definitions for all fields, enum for `status`, enum for `failure_class`, regex pattern for `session_id`, required-fields list.

These schemas serve two purposes: (a) machine validation of queue YAML via `ajv`, (b) reference documentation for what fields exist.

Add a tiny validator script `00_ARCHITECTURE/CONDUCTOR/validate_queue.py`:

```python
#!/usr/bin/env python3
"""Validate session_queue.yaml against queue_entry_schema.json."""
import json, sys, yaml
from pathlib import Path
try:
    from jsonschema import validate, ValidationError
except ImportError:
    print("pip install jsonschema --break-system-packages", file=sys.stderr)
    sys.exit(2)

base = Path(__file__).parent
schema = json.loads((base / "schemas" / "queue_entry_schema.json").read_text())
queue = yaml.safe_load((base / "session_queue.yaml").read_text())

for entry in queue.get("entries", []):
    try:
        validate(entry, schema)
    except ValidationError as e:
        print(f"FAIL {entry.get('session_id')}: {e.message}", file=sys.stderr)
        sys.exit(1)

print(f"OK — {len(queue['entries'])} entries valid")
```

**AC.CONDUCTOR-S0.5:** Schemas + validator exist; running `python 00_ARCHITECTURE/CONDUCTOR/validate_queue.py` from the worktree root reports `OK — 9 entries valid`; commit message reads `CONDUCTOR-S0 Item 5: queue + halt schemas + validator`.

### Item 6 — Author smoke-test brief and queue

**What:** Build the minimum-viable end-to-end proof. Create `00_ARCHITECTURE/CONDUCTOR/smoke/SMOKE_BRIEF_v1_0.md`:

```markdown
---
artifact: SMOKE_BRIEF_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: READY
session_id: SMOKE-S0
purpose: Conductor end-to-end proof — no real work, just exercises orchestrator + sub-agent + gate pattern
---

# SMOKE_BRIEF — Conductor Proof of Life

## §0 — Scope (one item only)

### Item 1 — Heartbeat file
**What:** Create `00_ARCHITECTURE/CONDUCTOR/smoke/SMOKE_HEARTBEAT.md` with content
`Conductor smoke test heartbeat at <ISO timestamp>`. Commit with message
`SMOKE-S0: heartbeat`.

**AC.SMOKE.1:** File exists at the path; commit on current branch with the message.

## §1 — Constraints

**may_touch:** `00_ARCHITECTURE/CONDUCTOR/smoke/SMOKE_HEARTBEAT.md` only.
**must_not_touch:** everything else — especially anything outside the Conductor directory.

## §2 — Session-close

Emit FINAL_SUMMARY per orchestrator prompt §3 template.
```

Create `00_ARCHITECTURE/CONDUCTOR/smoke/smoke_queue.yaml`:

```yaml
schema_version: 1.0
queue_name: smoke
total_entries: 1
entries:
  - session_id: SMOKE-S0
    brief_path: 00_ARCHITECTURE/CONDUCTOR/smoke/SMOKE_BRIEF_v1_0.md
    branch: feature/phase-4c-panchang
    worktree_path: /Users/Dev/Vibe-Coding/Apps/Panchang
    depends_on: []
    requires_human_approval: false
    push_to_remote: false
    gate_command: |
      test -f 00_ARCHITECTURE/CONDUCTOR/smoke/SMOKE_HEARTBEAT.md && \
      git log -1 --pretty=%s | grep -q "SMOKE-S0: heartbeat"
    expected_artifacts:
      - 00_ARCHITECTURE/CONDUCTOR/smoke/SMOKE_HEARTBEAT.md
    est_tokens: 5000
    est_duration_min: 3
    status: pending
```

**AC.CONDUCTOR-S0.6:** Smoke brief + smoke queue exist; queue validates against schema; commit message reads `CONDUCTOR-S0 Item 6: smoke test brief + queue`.

### Item 7 — Execute the smoke test manually (this session's executor IS the orchestrator for this one)

**What:** As the executor of CONDUCTOR-S0, you simulate the orchestrator one time to prove the pattern:

1. Read `smoke_queue.yaml` → pick SMOKE-S0
2. Construct the sub-agent prompt per `CONDUCTOR_PROMPT_v1_0.md §3` template using `SMOKE_BRIEF_v1_0.md`
3. Call the Task tool with `subagent_type: "general-purpose"` and the constructed prompt
4. Wait for sub-agent's FINAL_SUMMARY
5. Run the gate command (Bash) from the worktree root
6. If both succeed: append a PASS entry to `CONDUCTOR_LOG.md` with the sub-agent's summary + gate output + commit SHA; update `smoke_queue.yaml` `status: passed`
7. If either fails: append a HALT entry to `CONDUCTOR_HALT_LOG.md` with full context; emit halt banner in chat; do NOT advance

**AC.CONDUCTOR-S0.7:**
- `00_ARCHITECTURE/CONDUCTOR/smoke/SMOKE_HEARTBEAT.md` exists with valid timestamp
- A commit on `feature/phase-4c-panchang` with message `SMOKE-S0: heartbeat`
- `CONDUCTOR_LOG.md` has its first entry (PASS for SMOKE-S0)
- `smoke_queue.yaml` SMOKE-S0 entry shows `status: passed`
- Commit message for this item reads `CONDUCTOR-S0 Item 7: smoke test PASS — orchestrator + sub-agent pattern proven`

If the smoke test HALTS instead of PASSES: do NOT proceed with subsequent items. Diagnose the failure (sub-agent could not spawn? gate command malformed? branch state wrong?), fix, re-run. This is the canary; if it fails, the design has a real bug.

### Item 8 — Author `README.md` + `WAVE_2_MIGRATION_NOTE.md`

**What — `00_ARCHITECTURE/CONDUCTOR/README.md`:** Operator-facing documentation. Sections:

- §1 — What the Conductor is (one paragraph: orchestrator that walks `session_queue.yaml`, spawning sub-agents per brief, gated, halt-on-failure)
- §2 — How to kick off an autonomous run (the exact kickoff prompt to paste in Antigravity, with worktree context — `/Users/Dev/Vibe-Coding/Apps/Panchang` on `feature/phase-4c-panchang`)
- §3 — How to read the logs (CONDUCTOR_LOG.md = run history; CONDUCTOR_HALT_LOG.md = open halts)
- §4 — How to respond to a halt (RESUME / SKIP / ABANDON keywords; re-paste kickoff prompt)
- §5 — How to add a session to the queue (edit `session_queue.yaml`; validate with `validate_queue.py`)
- §6 — Architectural invariants (per-session commits autonomous; PR-to-main human-gated; orchestrator never touches app code; each sub-agent gets fresh context)
- §7 — Context-budget guards (20-session cap per orchestrator chat; user re-kicks for next batch; future wave handles automatic handoff)
- §8 — Wave 1 / Wave 2 boundary (Conductor currently lives on `feature/phase-4c-panchang` co-located with Phase 4C work; migrates to main via cherry-pick PR at Wave 1 close — see `WAVE_2_MIGRATION_NOTE.md`)
- §9 — Known limitations (Wave 1 only; orchestrator doesn't yet handle inter-worktree mirror discipline; brief-authoring halts are expected pause points)
- §10 — Where to look first when something is wrong (CONDUCTOR_HALT_LOG.md → CONDUCTOR_LOG.md → the failing sub-agent's commits on its branch)

**What — `00_ARCHITECTURE/CONDUCTOR/WAVE_2_MIGRATION_NOTE.md`:** A single-page reminder document targeted at future-you (or future-Cowork) at the moment Wave 1 closes. Sections:

- §1 — Why this exists: Conductor was built on `feature/phase-4c-panchang` for Wave 1 convenience. Wave 2 needs it on main so M5-A / 4B / 4D sessions running on other worktrees can consume it.
- §2 — The cherry-pick procedure:

  ```bash
  # From the Madhav clone (or a fresh worktree of main):
  cd /Users/Dev/Vibe-Coding/Apps/Madhav
  git checkout main
  git pull origin main
  git checkout -b feature/conductor-to-main

  # Identify Conductor commits on feature/phase-4c-panchang.
  # These are commits that ONLY touch 00_ARCHITECTURE/CONDUCTOR/ paths
  # AND/OR 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_CONDUCTOR_*.md
  git log feature/phase-4c-panchang --oneline -- 00_ARCHITECTURE/CONDUCTOR/

  # Cherry-pick each Conductor commit in order:
  git cherry-pick <sha-1> <sha-2> ... <sha-N>

  # Resolve trivial conflicts (likely none if Conductor stayed scoped to its directory)
  # Push and open PR to main:
  git push -u origin feature/conductor-to-main
  # PR title: "Conductor — autonomous session orchestrator (Wave 1 → main)"
  ```

- §3 — Trigger condition for running this procedure: ANY of (a) Wave 1 close (all of 4C-1 through 4C-9 closed); (b) Wave 2 expansion starts (M5-A or 4B work that wants to be driven by Conductor); (c) red-team finding that Phase 4C branch contamination is risking review of the Phase 4C close PR.
- §4 — What to verify post-merge: Conductor files exist on main; running `python 00_ARCHITECTURE/CONDUCTOR/validate_queue.py` from a fresh checkout of main succeeds; CLAUDE.md amendment (from `CLAUDE_MD_AMENDMENT_PROPOSAL.md`) applied + version bumped + MP.1 mirror update done in a follow-up Cowork session.
- §5 — Anti-pattern warning: do NOT merge `feature/phase-4c-panchang` to main as a single PR if Conductor is still on that branch. Cherry-pick Conductor first, then PR Phase 4C. Otherwise the Phase 4C review is muddied by infrastructure noise.

**AC.CONDUCTOR-S0.8:** README exists with all 10 sections; WAVE_2_MIGRATION_NOTE.md exists with all 5 sections; total ~250–400 lines combined; commit message reads `CONDUCTOR-S0 Item 8: operator README + Wave 2 migration note`.

### Item 9 — Draft CLAUDE.md amendment (do NOT apply this session)

**What:** Write `00_ARCHITECTURE/CONDUCTOR/CLAUDE_MD_AMENDMENT_PROPOSAL.md`. This is a PROPOSED change to `CLAUDE.md §E` that adds the Conductor as the sixth concurrent workstream. Includes:

- The exact text block to add to CLAUDE.md §E (Five → Six workstreams)
- Rationale (why Conductor is a workstream — it's project-spanning infrastructure that touches main and outlives any single phase)
- Suggested version bump (e.g. CLAUDE.md v2.6 → v2.7)
- Mirror impact (MP.1 update to `.geminirules` required)
- **Timing note:** the amendment is APPLIED ONLY AFTER the Conductor cherry-pick PR merges to main (Wave 2 migration). Applying it earlier creates a CLAUDE.md state that references a workstream not visible on main. The apply happens in a follow-up Cowork session that runs against the Madhav clone on main.

The amendment is NOT applied in this session, nor in the cherry-pick PR itself. It's a separate, third operation.

**AC.CONDUCTOR-S0.9:** Proposal file exists with all four items above plus the timing note; commit message reads `CONDUCTOR-S0 Item 9: CLAUDE.md amendment proposal (deferred apply — post Wave 2 migration)`.

### Item 10 — Session-close + handoff note

**What:**
1. Update `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` concurrent_workstreams block: add Conductor entry (`status: BUILT — on feature/phase-4c-panchang pending Wave 1 close + cherry-pick to main`)
2. Append `00_ARCHITECTURE/SESSION_LOG.md` with the CONDUCTOR-S0 atomic block (open + body + close)
3. Flip frontmatter of this brief `status: READY` → `status: COMPLETE`
4. Remove `CLAUDECODE_BRIEF.md` from worktree root
5. Final commit message: `CONDUCTOR-S0: session close — Conductor scaffold built, smoke test PASS, queue populated for Wave 1`
6. Write a `HANDOFF.md` at worktree root summarizing for the user:
   - What got built (3-line summary)
   - **The split-PR strategy at Wave 1 close** (cherry-pick Conductor to main FIRST as its own small PR; Phase 4C closes via a SEPARATE PR later; reference `WAVE_2_MIGRATION_NOTE.md` for the exact cherry-pick procedure)
   - How to trigger the first real autonomous run NOW (the kickoff prompt — works against the populated queue immediately, no merge required since Conductor and Phase 4C share this branch)
   - Open known limitations

**AC.CONDUCTOR-S0.10:** CURRENT_STATE updated; SESSION_LOG appended; brief flipped to COMPLETE; HANDOFF.md at root with split-PR strategy explicitly named; final commit landed.

---

## §4 — Mirror discipline

**No active mirror updates this session.** The CLAUDE.md amendment is DEFERRED to post-Wave-2-migration (per Item 9). `.geminirules` updates happen in the follow-up Cowork session that applies the amendment on main, not now and not in the cherry-pick PR itself. Document this clearly in the amendment proposal (Item 9 timing note).

---

## §5 — Constraints

**may_touch (in `/Users/Dev/Vibe-Coding/Apps/Panchang`):**

- `00_ARCHITECTURE/CONDUCTOR/**` (all new this session)
- `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_CONDUCTOR_S0_v1_0.md` (status flip at session close only)
- `CLAUDECODE_BRIEF.md` at worktree root (delete at session close)
- `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` (concurrent_workstreams block — add Conductor entry only; do NOT touch Phase 4C state fields)
- `00_ARCHITECTURE/SESSION_LOG.md` (append CONDUCTOR-S0 entry only)
- `HANDOFF.md` at worktree root (new)

**must_not_touch (CRITICAL — co-located branch hygiene):**

- `platform/**` (no app code this session; Phase 4C source code that may already exist on this branch from 4C-0 governance commits is OFF LIMITS)
- `00_ARCHITECTURE/PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md` (sealed in 4C-0)
- `00_ARCHITECTURE/BRIEFS/PHASE_4C_PANCHANG_BRIEF_v1_0.md` (sealed in 4C-0)
- `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PHASE_4C_0_v1_0.md` (sealed COMPLETE in 4C-0)
- `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PHASE_4C_1_S1_v1_0.md` (authored but not yet executed; off-limits — do NOT pre-stage or pre-execute)
- `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` (Conductor is workflow infrastructure, not a corpus artifact)
- `03_DERIVATIONS/PANCHANG_DAILY_v1_0.md` (created in 4C-0)
- `01_FACTS_LAYER/**`, `025_HOLISTIC_SYNTHESIS/**`, `035_DISCOVERY_LAYER/**` (corpus frozen)
- `CLAUDE.md` (amendment is PROPOSED, not applied — Item 9 writes a proposal file, not an in-place edit)
- `.geminirules`, `.gemini/project_state.md` (no mirror updates this session)
- Anything outside `/Users/Dev/Vibe-Coding/Apps/Panchang/` (no cross-worktree edits)

The branch hygiene constraint is the most important rule for this session. `feature/phase-4c-panchang` is shared with the Phase 4C application-code workstream. The Conductor builds in `00_ARCHITECTURE/CONDUCTOR/` only. Every Conductor commit must be cleanly cherry-pickable to main without dragging Phase 4C application code with it. If the executor needs to touch a non-Conductor file mid-session, halt and report to native — do not silently expand scope.

---

## §6 — Session-close checklist

- [ ] SESSION_OPEN artifact emitted and validates
- [ ] All 10 AC checks completed (AC.CONDUCTOR-S0.1 through .10)
- [ ] Smoke test PASS verified — heartbeat file exists, commit landed on `feature/phase-4c-panchang`, log entry written
- [ ] `validate_queue.py` exits 0 on both `session_queue.yaml` and `smoke/smoke_queue.yaml`
- [ ] All scope items committed separately on `feature/phase-4c-panchang` (10 scope commits + 1 staging + 1 close = ~12 Conductor-tagged commits)
- [ ] Every Conductor commit touches ONLY `00_ARCHITECTURE/CONDUCTOR/` or `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_CONDUCTOR_*.md` or `HANDOFF.md` or `CURRENT_STATE`/`SESSION_LOG` housekeeping — verifiable via `git log --name-only` review
- [ ] CURRENT_STATE_v1_0.md Conductor entry present in concurrent_workstreams block
- [ ] SESSION_LOG.md CONDUCTOR-S0 atomic entry appended
- [ ] HANDOFF.md at worktree root with split-PR strategy explicitly documented
- [ ] WAVE_2_MIGRATION_NOTE.md exists with the cherry-pick procedure
- [ ] SESSION_CLOSE artifact emitted and validates
- [ ] Branch `feature/phase-4c-panchang` ready for autonomous-run kickoff (Conductor immediately usable on this branch; cherry-pick to main is deferred to Wave 1 close — see §10/§11)

---

## §7 — LLM stack for this session

| Role | Model | Notes |
|---|---|---|
| Primary inference | Gemini (gemini-2.5-pro for code/YAML, flash for templates) | Default |
| Fallback | DeepSeek v4 Pro | |
| Tertiary | NIM | |
| Anthropic/Claude API | **BANNED** | Per memory file 2026-05-19 |

Note: when the Conductor runs autonomously, each sub-agent honors the LLM stack policy declared in its own brief (§7 of each brief). Phase 4C briefs are on Gemini stack.

---

## §8 — Context carried (do not re-derive)

These decisions were settled in the Cowork conversation 2026-05-19 and should not be re-litigated by the executor:

- **Autonomy boundary:** Per-session commits autonomous on feature branches; PR-to-main always human-gated. Queue entries with `requires_human_approval: true` always halt before execution.
- **Harness:** Antigravity Claude Code extension as orchestrator host; Task tool spawns sub-agents per brief (each sub-agent gets fresh 200K context).
- **Halt notification:** Conspicuous chat panel banner + append to `CONDUCTOR_HALT_LOG.md`. No email/Slack/desktop notifications. User responds in chat with `RESUME` / `SKIP` / `ABANDON` keyword.
- **Wave 1 scope:** Phase 4C only — 4C-1-S1 through 4C-9, ~20 sessions. Wave 2 (extend to M5-A + 4B + 4D) is a separate future Cowork conversation, after Wave 1 proves out.
- **Context discipline:** Files on disk are the inheritance medium, not conversation memory. Past sessions' execution detail is gone from sub-agent context by design. Slow-leak hygiene = periodic `consolidate-memory` queue entries every ~10 sessions.
- **Brief-authoring halts are intentional pause points.** Only 4C-1-S1 has an authored brief today. 4C-1-S2, 4C-1-S3, 4C-2 etc. will halt the queue with `requires_brief_authoring: true` until Cowork authors each one. This is the right design — briefs need Cowork-level deliberation, not autonomous generation.
- **The orchestrator's own context cap is ~20 sessions per Antigravity chat.** After 20, user re-kicks in a fresh chat. Wave 1 (20 sessions) fits in one chat with margin; future waves may need automated handoff (out of Wave 1 scope).
- **Worktree co-location:** Conductor lives on `feature/phase-4c-panchang` alongside Phase 4C work for Wave 1 convenience. Cherry-pick to main at Wave 1 close. Branch hygiene during execution = Conductor commits touch ONLY Conductor paths.

---

## §9 — On the smoke test as canary

Item 7 (smoke test execution) is the most important AC in this session. If it FAILS, the entire Conductor design has an unfixed bug and we should not proceed to populate the real queue. Acceptable failure modes:

- **Sub-agent does not spawn:** Task tool not available / wrong subagent_type / prompt malformed. Fix the orchestrator prompt §3.
- **Sub-agent runs but does not commit:** Sub-agent prompt lacks explicit commit instruction OR `--dangerously-skip-permissions` not actually in effect. Fix the sub-agent prompt template.
- **Gate command fails:** `git log` doesn't find the message because sub-agent is on the wrong branch. Fix the worktree_path enforcement in queue schema.
- **FINAL_SUMMARY not parseable:** Sub-agent forgot to emit the block, or emitted a malformed version. Tighten the sub-agent prompt template.

In each failure mode, fix the design, commit the fix, re-run the smoke test. Do not proceed to Item 8+ until Item 7 PASSES.

---

## §10 — On what happens AFTER this session (split-PR strategy)

When CONDUCTOR-S0 closes cleanly, the immediate next step is NOT to PR to main — it's to start using the Conductor on this very branch.

1. **First autonomous run is local to `feature/phase-4c-panchang`.** You paste the kickoff prompt from `00_ARCHITECTURE/CONDUCTOR/README.md §2` in any Antigravity chat pointed at the Panchang worktree. The orchestrator picks up `session_queue.yaml`, finds 4C-1-S1 eligible, spawns a sub-agent against `CLAUDECODE_BRIEF_PHASE_4C_1_S1_v1_0.md`, watches it complete, runs the gate, advances. No PR needed — Conductor and 4C-1-S1 are on the same branch in the same worktree.

2. **The queue halts at 4C-1-S2** (brief doesn't exist yet). You return to Cowork, I author 4C-1-S2 in a focused conversation, you commit it to `feature/phase-4c-panchang`, update the queue entry (`requires_brief_authoring: false`, fill `brief_path` + `gate_command`), re-paste the kickoff. Loop.

3. **At Wave 1 close** — when 4C-9 has closed cleanly and the Phase 4C campaign is ready to merge — you execute the **split-PR strategy**:

   **PR 1 (Conductor → main):** Open a separate small PR with ONLY the Conductor commits. Cherry-pick procedure documented in `00_ARCHITECTURE/CONDUCTOR/WAVE_2_MIGRATION_NOTE.md`. PR title: `Conductor — autonomous session orchestrator (Wave 1 → main)`. Reviewer: native. This PR is small (~10–15 commits, all infrastructure), fast to review, lands the Conductor on main where Wave 2 (M5-A, 4B, 4D sessions on other worktrees) can use it.

   **PR 2 (Phase 4C close → main):** Then open the standard Phase 4C close PR with the application-code work — panchang_engine + query_panchanga + /panchang UI + Muhurat Finder + iCal feed + Ask-Madhav + telemetry. Same pattern as Phase O Observatory's close. Reviewer: native. This PR is large and gets the deliberate review Phase 4C deserves, uncluttered by Conductor infrastructure.

4. **Apply the CLAUDE.md amendment AFTER PR 1 merges to main** — a tiny follow-up Cowork session that opens the proposal file (`CLAUDE_MD_AMENDMENT_PROPOSAL.md`), applies the edit to `CLAUDE.md §E`, version-bumps CLAUDE.md, propagates MP.1 to `.geminirules`. Runs against the Madhav clone on main.

5. **Wave 2 unblocks.** Once Conductor is on main, the queue manifest expands to cover M5-A + 4B + 4D. Their sessions live on their own worktrees/branches, and the Conductor (now on main, accessible to any worktree) drives them.

---

## §11 — Wave 2 migration note (the cherry-pick is mandatory)

The split-PR strategy in §10 is not optional polish — it is the bridge between Wave 1 (Phase 4C-only autonomy) and Wave 2 (multi-workstream autonomy). If you merge `feature/phase-4c-panchang` to main as a single fat PR without cherry-picking Conductor out first, two failure modes follow:

1. **Phase 4C review is muddied.** Reviewer (you, in your future "merge-this-to-main" mode) has to mentally separate workflow infrastructure from application code in a single review pass. This is exactly the dilution that drives review fatigue and missed bugs.

2. **Wave 2 is gated on Phase 4C completion.** If Conductor is on main only after Phase 4C closes, Wave 2 cannot start until then — which means M5-A, 4B, and 4D either stall waiting for 4C-9, or they run manually (defeating the purpose of building the Conductor at all).

The cherry-pick procedure is in `00_ARCHITECTURE/CONDUCTOR/WAVE_2_MIGRATION_NOTE.md`. Trigger conditions to execute it (any one of):

- **Wave 1 closes** — natural moment; do the cherry-pick + PR 1 before opening PR 2.
- **Wave 2 expansion is requested mid-Phase-4C** — if you want to start M5-A or 4B autonomously before all of 4C-9 closes, cherry-pick early. Cleaner than waiting.
- **Red-team finding** — if branch contamination is flagged in a Phase 4C red-team pass, cherry-pick to resolve immediately.

The Conductor commits are designed to be cleanly cherry-pickable: they touch only `00_ARCHITECTURE/CONDUCTOR/` and a few governance files explicitly listed in §5 may_touch. If a Conductor commit accidentally drags a Phase 4C application file with it, that's a session-discipline failure to catch in red-team review before the cherry-pick.

---

*End of CLAUDECODE_BRIEF_CONDUCTOR_S0_v1_0.md — authored 2026-05-19; amended 2026-05-19 in-place to co-locate the Conductor on the Panchang worktree's `feature/phase-4c-panchang` branch instead of a dedicated sibling worktree; split-PR strategy at Wave 1 close added in §10–§11.*
*Executor: Claude Code (Antigravity / VS Code extension). Branch: feature/phase-4c-panchang. Worktree: /Users/Dev/Vibe-Coding/Apps/Panchang. Session: CONDUCTOR-S0.*
*Wave 1 scope: Phase 4C only. Wave 2+ deferred to future Cowork conversation. Cherry-pick to main at Wave 1 close is mandatory.*
