---
title: CONDUCTOR_KICKOFF_PROMPT — Universal Parity Campaign SP1 Run 2 (no-HAP)
version: 2.0
status: CURRENT
campaign: universal-parity
conductor_run: 2
total_sessions: 8
hap_policy: DISABLED — gate failures only; no human approval checkpoints
---

# CONDUCTOR KICKOFF — SP1 Run 2 (paste into MadhavParity worktree)

Paste this entire prompt into a Claude Code session opened in:
`/Users/Dev/Vibe-Coding/Apps/MadhavParity`

Use flag: `--dangerously-skip-permissions`

---

## YOUR ROLE

You are the **Conductor** for the Universal Parity Campaign, SP1 Run 2.
You orchestrate 8 sub-agent sessions autonomously, one after another, with no human approval stops.
You only stop if a gate command fails after one retry. All other execution is uninterrupted.

You do NOT implement anything yourself. You read briefs, spawn sub-agents, verify their gates, and advance the queue.

---

## CAMPAIGN CONTEXT

**Goal:** All retrieval tools and data assets available in their most enriched form across all three channels:
- Channel A+B (portal): `platform/src/lib/retrieve/` RETRIEVAL_TOOLS
- Channel C (MCP): `platform-mcp/src/tools/` + `platform-mcp/src/server.ts`

**What is already done (Run 1, 12 sessions completed):**
- PRE-S1: diagnostic baseline established
- UDA-Q-S1..S8: 7 quality backports applied to shared tools
- UDA-0-S1..S3: CAPABILITY_MANIFEST.json populated (268 entries; 36 portal + 43 MCP tool entries; catalog.ts fixed 22→43)

**This run's scope (Run 2, 8 sessions):** UDA-1-S1 through UDA-1-S8
Port 14 Class B MCP-only engines to portal RETRIEVAL_TOOLS so Channel A+B has parity with Channel C.

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

For each session in order:

### 1. Mark session `in_progress` in queue YAML

Update the session's `status` field in `session_queue.yaml` from `pending` → `in_progress`.

### 2. Read the brief

```bash
cat <brief_path from queue>
```

### 3. Spawn a sub-agent with that brief

Create a new `Task` (sub-agent) with:
- The FULL content of the brief as the prompt
- Additional context appended: "You are in worktree `/Users/Dev/Vibe-Coding/Apps/MadhavParity` on branch `feature/universal-parity`. Use `--dangerously-skip-permissions`. Commit after every session."

### 4. Wait for sub-agent to complete

Do not proceed until the sub-agent returns its completion report.

### 5. Run gate commands

Execute every `gate_command` listed in the session's queue entry. Each must exit 0 and print a `PASS` line.

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
- After UDA-1-S8 (final session), push to origin:
  ```bash
  cd /Users/Dev/Vibe-Coding/Apps/MadhavParity && git push origin feature/universal-parity
  ```
- Print: `RUN 2 COMPLETE — UDA-1 phase done. 8/8 sessions passed. Push complete.`
- Stop.

### 6b. If ANY gate fails (after 1 retry)

- Write a HALT entry to `CONDUCTOR_HALT_LOG.md`:
  ```markdown
  ### GATE-HALT-<N>
  - **Session:** <session_id>
  - **Timestamp:** <ISO date>
  - **Reason:** Gate <gate_name> FAIL after 1 retry — <evidence>
  - **Blocking:** All subsequent sessions
  - **Required action:** Native must review, fix, and re-kick conductor from this session
  - **Resolution:** (pending)
  ```
- Update `session_queue.yaml`: `status: halted`
- Push current branch state:
  ```bash
  cd /Users/Dev/Vibe-Coding/Apps/MadhavParity && git push origin feature/universal-parity
  ```
- STOP.

**There are no Human Approval Checkpoints in this run. Gate failures are the only stop condition.**

---

## SESSION ORDER (Run 2)

Execute in this exact order — no parallelism, strictly sequential:

| # | Session   | Tools being ported |
|---|-----------|-------------------|
| 1 | UDA-1-S1  | query_transits_over_natal + query_yogas_active_now |
| 2 | UDA-1-S2  | get_planet_avastha + get_shadbala_full |
| 3 | UDA-1-S3  | query_jaimini_chara_dasha |
| 4 | UDA-1-S4  | query_planetary_period_predictions |
| 5 | UDA-1-S5  | query_dasamsha_career + query_shashtiamsha |
| 6 | UDA-1-S6  | query_eclipse_transits + query_planet_war |
| 7 | UDA-1-S7  | query_drekkana_drishti + query_remedies_prescribed |
| 8 | UDA-1-S8  | tara_balam_for_native + chandra_balam_for_native + muhurta_finder |

---

## CONDUCTOR START SEQUENCE

Before spawning session 1 (UDA-1-S1), run this initialization:

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity

# 1. Verify worktree is on the right branch
git branch --show-current
# Expected: feature/universal-parity

# 2. Pull latest (UDA-0 commits from prior run may need syncing)
git pull origin feature/universal-parity

# 3. Verify queue file and confirm UDA-0-S3 is completed
grep -A2 "id: UDA-0-S3" 00_ARCHITECTURE/CONDUCTOR/universal-parity/session_queue.yaml
# Expected: status: completed

# 4. Verify all 8 UDA-1 briefs are present
for s in S1 S2 S3 S4 S5 S6 S7 S8; do
  brief="00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PARITY_UDA_1_${s}_v1_0.md"
  test -f "$brief" && echo "BRIEF UDA-1-${s}: OK" || echo "BRIEF UDA-1-${s}: MISSING"
done

# 5. Verify UDA-1-S1 is pending (not already completed or halted)
grep -A2 "id: UDA-1-S1" 00_ARCHITECTURE/CONDUCTOR/universal-parity/session_queue.yaml
# Expected: status: pending

# 6. Git status clean
git status --short
# Expected: nothing (or only untracked eval files)
```

If any UDA-1 brief is MISSING, read `session_queue.yaml` to find its `brief_path` and `brief_spec`, then re-create it from spec before proceeding. Do not spawn any sub-agent until all 8 briefs are confirmed present.

---

## IMPORTANT: Class B vs Class A distinction

UDA-1 sessions port **Class B** tools — these have a compute engine in `platform/scripts/` Python sidecar but NO portal `RETRIEVAL_TOOL` wrapper yet. The sub-agent must:

1. Find the existing Python compute script in `platform/scripts/temporal/` or `platform/scripts/compute/`
2. Confirm the `/api/retrieve/<tool>` route exists (or create it)
3. Write the TypeScript `RETRIEVAL_TOOL` in `platform/src/lib/retrieve/<tool>.ts`
4. Register it in `platform/src/lib/retrieve/index.ts`
5. Write a unit test in `platform/src/lib/__tests__/retrieve/<tool>.test.ts`
6. Update `CAPABILITY_MANIFEST.json`: set `channel: both` for this tool (was `mcp`)

**Do not conflate with Class A** (engine already existed on both sides; UDA-1 is not Class A work).

For UDA-1-S8 specifically: `muhurta_finder` is Class A (engine exists; port only). `tara_balam_for_native` and `chandra_balam_for_native` are Class B (check for Python engine first; if absent, write stub + flag for Phase 8 engine build rather than blocking the session).

---

## TYPESCRIPT COMPILE GATE (mandatory on every session)

Every session that touches `platform/` must pass:
```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity/platform && npx tsc --noEmit
# Must exit 0
```

Every session that touches `platform-mcp/` must pass:
```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity/platform-mcp && npx tsc --noEmit
# Must exit 0
```

These are mandatory gates in addition to session-specific gates. A TypeScript compile error is a gate failure and triggers the retry + HALT sequence.

---

## GATE RETRY RULE

If a gate fails on first run, spawn a patch sub-agent with: the brief + the specific failing gate output + instruction "Fix only the failing gate — do not modify anything else." If the gate still fails after the patch sub-agent, write a GATE-HALT and stop.

---

## PUSH CADENCE

Push to `origin feature/universal-parity` only at:
- After UDA-1-S8 (run complete)
- Any time a GATE-HALT fires

Intermediate sessions commit locally only. Do not push after each session — it slows the run.

---

## CONTEXT BUDGET RULE

This run has 8 sessions = 8 sub-agent spawns, well within the context budget. If context approaches a limit before session 8, write a `CONDUCTOR_LOG.md` entry marking current position and stop cleanly.

---

## BEGIN

Run the start sequence above, then spawn UDA-1-S1 immediately. No confirmation needed.

---

*End of CONDUCTOR_KICKOFF_PROMPT_v2_0.md — HAP policy: DISABLED*
