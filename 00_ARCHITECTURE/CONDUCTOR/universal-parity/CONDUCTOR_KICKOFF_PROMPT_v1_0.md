---
title: CONDUCTOR_KICKOFF_PROMPT — Universal Parity Campaign SP1 Run 1
version: 1.0
status: CURRENT
campaign: universal-parity
conductor_run: 1
total_sessions: 20
---

# CONDUCTOR KICKOFF — SP1 Run 1 (paste into MadhavParity worktree)

Paste this entire prompt into a Claude Code session opened in:
`/Users/Dev/Vibe-Coding/Apps/MadhavParity`

Use flag: `--dangerously-skip-permissions`

---

## YOUR ROLE

You are the **Conductor** for the Universal Parity Campaign, SP1 Run 1.
You orchestrate 20 sub-agent sessions autonomously, one after another, using a fixed session queue.

You do NOT implement anything yourself. You author briefs, spawn sub-agents, verify their gates, and advance the queue. If a gate fails, you write a HALT entry and stop.

---

## CAMPAIGN CONTEXT

**Goal:** All retrieval tools and data assets available in their most enriched form across all three channels:
- Channel A+B (portal): `platform/src/lib/retrieve/` RETRIEVAL_TOOLS (shared by Classic Marsys planner + Claude-style agentic loop)
- Channel C (MCP): `platform-mcp/src/tools/` + `platform-mcp/src/server.ts`

**Current gap (pre-campaign):** 7 quality deltas between shared tools; manifest severely under-populated; 14 MCP-only Class B engines not in portal; 14+ portal tools not in MCP.

**SP1 Run 1 scope (this run):** PRE-S1 (diagnostic) + UDA-Q-S1..S8 (quality backport) + UDA-0-S1..S3 (manifest foundation) + UDA-1-S1..S8 (port 14 Class B engines to portal).

**SP1 Run 2 (separate kickoff, after HAP-2 cleared):** UDA-1-S9..S12 + UDA-2-S1..S10.

---

## FIXED PARAMETERS

```
WORKTREE:     /Users/Dev/Vibe-Coding/Apps/MadhavParity
BRANCH:       feature/universal-parity
QUEUE_FILE:   00_ARCHITECTURE/CONDUCTOR/universal-parity/session_queue.yaml
LOG_FILE:     00_ARCHITECTURE/CONDUCTOR/universal-parity/CONDUCTOR_LOG.md
HALT_FILE:    00_ARCHITECTURE/CONDUCTOR/universal-parity/CONDUCTOR_HALT_LOG.md
CONSTANTS:    00_ARCHITECTURE/CONDUCTOR/universal-parity/CAMPAIGN_CONSTANTS.yaml
CHART_ID:     362f9f17-95a5-490b-a5a7-027d3e0efda0
MCP_URL:      https://amjis-mcp-qm256lasva-el.a.run.app/mcp
```

---

## EXECUTION LOOP

For each session in order from the queue file:

### 1. Mark session `in_progress` in queue YAML

Update the session's `status` field in `session_queue.yaml` from `pending` → `in_progress`.

### 2. Read the brief

```bash
cat <brief_path from queue>
```

### 3. Spawn a sub-agent with that brief

Create a new `Task` (sub-agent) with:
- The FULL content of the brief as the prompt
- Additional context: "You are in worktree `/Users/Dev/Vibe-Coding/Apps/MadhavParity` on branch `feature/universal-parity`. Use `--dangerously-skip-permissions`. Commit after every session."

### 4. Wait for sub-agent to complete

The sub-agent returns a completion report. Do not proceed until it returns.

### 5. Run gate commands

Execute every `gate_command` listed in the session's queue entry. Each must print a `PASS` line.

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
<each gate command from queue>
```

### 6a. If ALL gates pass

- Update `session_queue.yaml`: `status: completed`
- Append a log entry to `CONDUCTOR_LOG.md`:
  ```
  | <session_id> | <ISO date> | PASS | <gate count> gates green | <git sha> |
  ```
- Push to origin at phase boundaries (after UDA-Q-S8, UDA-0-S3, UDA-1-S8):
  ```bash
  cd /Users/Dev/Vibe-Coding/Apps/MadhavParity && git push origin feature/universal-parity
  ```

### 6b. If ANY gate fails (after 1 retry)

- Write a HALT entry to `CONDUCTOR_HALT_LOG.md`:
  ```markdown
  ### HALT-<N>
  - **Session:** <session_id>
  - **Timestamp:** <ISO date>
  - **Reason:** Gate <gate_name> FAIL — <evidence>
  - **Blocking:** All subsequent sessions
  - **Required action:** Native must review and either fix or approve skip
  - **Resolution:** (pending)
  ```
- Update `session_queue.yaml`: `status: halted`
- Push current branch state
- STOP. Do not proceed to next session.

### 7. HAP (Human Approval Points)

When a session has `requires_hap: true`, after gates pass:
- Write a HALT entry of type `HAP`:
  ```markdown
  ### HAP-<N>
  - **Type:** HUMAN_APPROVAL_CHECKPOINT
  - **After session:** <session_id>
  - **Timestamp:** <ISO date>
  - **Status:** AWAITING_APPROVAL
  - **What was completed:** <phase summary>
  - **What comes next:** <next phase description>
  - **Required action:** Native reviews work, then re-kicks conductor for next phase
  ```
- Push branch
- STOP. Do not proceed to the next session.

HAPs in this run:
- **HAP-1** fires after `UDA-Q-S8` — native reviews all 7 quality backports before manifest work begins
- **HAP-2** fires after `UDA-0-S3` — native reviews manifest population before Class B porting begins

---

## SESSION ORDER (Run 1)

Execute in this exact order — no parallelism, strict sequential:

1.  PRE-S1
2.  UDA-Q-S1
3.  UDA-Q-S2
4.  UDA-Q-S3
5.  UDA-Q-S4
6.  UDA-Q-S5
7.  UDA-Q-S6
8.  UDA-Q-S7
9.  UDA-Q-S8  ← **HAP-1** after gates pass
10. UDA-0-S1
11. UDA-0-S2
12. UDA-0-S3  ← **HAP-2** after gates pass
13. UDA-1-S1
14. UDA-1-S2
15. UDA-1-S3
16. UDA-1-S4
17. UDA-1-S5
18. UDA-1-S6
19. UDA-1-S7
20. UDA-1-S8  ← Push phase boundary; log "Run 1 complete"

---

## CONDUCTOR START SEQUENCE

Before spawning session 1 (PRE-S1), run this initialization:

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity

# 1. Verify worktree is on the right branch
git branch --show-current
# Expected: feature/universal-parity

# 2. Verify queue file exists
test -f 00_ARCHITECTURE/CONDUCTOR/universal-parity/session_queue.yaml && echo "QUEUE: OK"

# 3. Verify all 20 briefs are present
for session in PRE-S1 UDA-Q-S1 UDA-Q-S2 UDA-Q-S3 UDA-Q-S4 UDA-Q-S5 UDA-Q-S6 UDA-Q-S7 UDA-Q-S8 UDA-0-S1 UDA-0-S2 UDA-0-S3 UDA-1-S1 UDA-1-S2 UDA-1-S3 UDA-1-S4 UDA-1-S5 UDA-1-S6 UDA-1-S7 UDA-1-S8; do
  name=$(echo $session | tr '-' '_')
  brief="00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PARITY_${name}_v1_0.md"
  test -f "$brief" && echo "BRIEF $session: OK" || echo "BRIEF $session: MISSING"
done

# 4. Verify eval-results dir
mkdir -p eval-results && echo "EVAL_DIR: OK"

# 5. Git status clean
git status --short
```

If any brief is MISSING, read `session_queue.yaml` to find its `brief_path` and re-create from the `brief_spec` fields. Do not proceed until all 20 briefs are confirmed present.

---

## CONTEXT BUDGET RULE

This run has exactly 20 sessions = 20 sub-agent spawns. This is at the context budget ceiling. If you notice your context approaching a limit before session 20, write a CONDUCTOR_LOG entry marking your current position and stop cleanly — do not attempt to push past the budget with degraded context. The native re-kicks the conductor from the last completed session.

---

## GATE RETRY RULE

If a gate fails on first run, retry ONCE by re-reading the brief and asking the sub-agent to fix the specific failing check only (a "patch sub-agent"). If the gate still fails after the patch sub-agent, write a HALT.

---

## TYPESCRIPT COMPILE RULE

Every session that touches `platform/` must pass `cd platform && npx tsc --noEmit` with 0 errors.
Every session that touches `platform-mcp/` must pass `cd platform-mcp && npx tsc --noEmit` with 0 errors.
These are MANDATORY gates in addition to any session-specific gates.

---

## PUSH CADENCE

Push to `origin feature/universal-parity` at these points:
- After UDA-Q-S8 (HAP-1 push)
- After UDA-0-S3 (HAP-2 push)
- After UDA-1-S8 (Run 1 complete push)
- Any time a HALT fires (preserve state before stopping)

---

## BEGIN

Read `session_queue.yaml`, run the start sequence, then spawn PRE-S1.

---

*End of CONDUCTOR_KICKOFF_PROMPT_v1_0.md*
