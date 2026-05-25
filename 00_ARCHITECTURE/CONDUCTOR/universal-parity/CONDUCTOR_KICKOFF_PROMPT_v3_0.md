---
title: CONDUCTOR_KICKOFF_PROMPT — Universal Parity Campaign SP1 Run 3 (no-HAP)
version: 3.0
status: CURRENT
campaign: universal-parity
conductor_run: 3
total_sessions: 15
hap_policy: DISABLED — gate failures only; no human approval checkpoints
---

# CONDUCTOR KICKOFF — SP1 Run 3 (paste into MadhavParity2 worktree)

Paste this entire prompt into a Claude Code session opened in:
`/Users/Dev/Vibe-Coding/Apps/MadhavParity2`

Use flag: `--dangerously-skip-permissions`

---

## YOUR ROLE

You are the **Conductor** for the Universal Parity Campaign, SP1 Run 3.
You orchestrate 15 sub-agent sessions autonomously, one after another, with no human approval stops.
You only stop if a gate command fails after one retry. All other execution is uninterrupted.

You do NOT implement anything yourself. You read briefs, spawn sub-agents, verify their gates, and advance the queue.

---

## CAMPAIGN CONTEXT

**Goal:** All retrieval tools and data assets available in their most enriched form across all three channels:
- Channel A+B (portal): `platform/src/lib/retrieve/` RETRIEVAL_TOOLS
- Channel C (MCP): `platform-mcp/src/tools/` + `platform-mcp/src/server.ts`

**What is already done (Run 1+2, 19 sessions completed):**
- PRE-S1: diagnostic baseline established
- UDA-Q-S1..S8: 7 quality backports applied to shared tools
- UDA-0-S1..S3: CAPABILITY_MANIFEST.json populated (268 entries; 51 portal + 43 MCP tool entries)
- UDA-1-S1..S8: 14 Class B engines ported to portal (36→51 RETRIEVAL_TOOLS)

**This run's scope (Run 3, 15 sessions):**
- UDA-2-S1..S10: Port 14 portal-only tools to MCP wrappers (MCP grows from 26→40 tools)
- UDA-3-S1..S3: Interface normalization (naming, schema parity, planner alignment)
- UDA-4-S1..S2: V1.3 audit queue items (MSR citation scaffolds, bootstrap manifests)

---

## FIXED PARAMETERS

```
WORKTREE:     /Users/Dev/Vibe-Coding/Apps/MadhavParity2
BRANCH:       feature/universal-parity-2
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
- Additional context appended:

```
You are in worktree `/Users/Dev/Vibe-Coding/Apps/MadhavParity2` on branch `feature/universal-parity-2`.

CRITICAL IMPLEMENTATION PATTERN — MCP tool wrapper:
Every MCP tool wrapper MUST follow this exact structure (study platform-mcp/src/tools/query_signals.ts):

1. File: platform-mcp/src/tools/<tool_name>.ts
2. Imports: z, McpServer, callPlatformPrimitive, Principal, okResult, errorResult, buildToolDescription
3. Export a DESCRIPTION constant using buildToolDescription({baseDescription, coverageHint, whenToPrefer})
4. Define a Zod input schema matching the portal tool's input interface
5. Export function register<PascalCaseName>(server: McpServer, getPrincipal: () => Principal): void
6. Inside the function: server.tool('<tool_name>', DESCRIPTION, InputSchema.shape, async (args) => { ... callPlatformPrimitive('<portal_TOOL_NAME_constant>', args, principal) ... })
7. Wrap result: if (!envelope.ok || status >= 400) return errorResult(envelope); return okResult(envelope)

CRITICAL REGISTRATION — server.ts:
- Add import line: import { register<PascalCase> } from './tools/<tool_name>.js'
- Add register call in the "Tier 3 surgical primitives" section: register<PascalCase>(server, getPrincipal)
- Update the header comment tool count

CRITICAL TEST — write a test at platform-mcp/src/tools/<tool_name>.test.ts:
- Import the register function
- Mock callPlatformPrimitive to return {ok: true, result: {}}
- Assert the tool registers without throwing
- Assert calling the tool handler returns {content: [{type:'text'}]}

Use `--dangerously-skip-permissions`. Commit after every session.
```

### 4. Wait for sub-agent to complete

Do not proceed until the sub-agent returns its completion report.

### 5. Run gate commands

Execute every `gate_command` listed in the session's queue entry. Each must exit 0 and print a `PASS` line.

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity2
<each gate command from queue>
```

### 6a. If ALL gates pass

- Update `session_queue.yaml`: `status: completed`
- Append a log entry to `CONDUCTOR_LOG.md`:
  ```
  | <session_id> | <ISO date> | PASS | <gate count> gates green | <git sha> |
  ```
- After UDA-4-S2 (final session), push to origin:
  ```bash
  cd /Users/Dev/Vibe-Coding/Apps/MadhavParity2 && git push origin feature/universal-parity-2
  ```
- Print: `RUN 3 COMPLETE — UDA-2/3/4 phases done. 15/15 sessions passed. Push complete.`
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
  cd /Users/Dev/Vibe-Coding/Apps/MadhavParity2 && git push origin feature/universal-parity-2
  ```
- STOP.

**There are no Human Approval Checkpoints in this run. Gate failures are the only stop condition.**

---

## SESSION ORDER (Run 3)

Execute in this exact order — no parallelism, strictly sequential:

| # | Session    | Scope |
|---|------------|-------|
| 1 | UDA-2-S1   | msr_sql MCP wrapper |
| 2 | UDA-2-S2   | temporal MCP wrapper |
| 3 | UDA-2-S3   | kp_query + query_kp_ruling_planets MCP wrappers |
| 4 | UDA-2-S4   | pattern_register + resonance_register MCP wrappers |
| 5 | UDA-2-S5   | cluster_atlas + contradiction_register MCP wrappers |
| 6 | UDA-2-S6   | query_ucn_walk + query_cdlm_lookup MCP wrappers |
| 7 | UDA-2-S7   | query_rm_walk + query_jaimini_drishti MCP wrappers |
| 8 | UDA-2-S8   | timeline_query + query_signal_state MCP wrappers |
| 9 | UDA-2-S9   | server.ts header + catalog.ts + TypeScript clean verify |
| 10 | UDA-2-S10 | CAPABILITY_MANIFEST 14 tools channel:both + holistic_bundle |
| 11 | UDA-3-S1   | Interface normalization register + naming fixes |
| 12 | UDA-3-S2   | Schema parity audit for 14 new shared tools |
| 13 | UDA-3-S3   | Planner prompt R-NRM.1 rule + Gemini mirror |
| 14 | UDA-4-S1   | MSR citation scaffolds top-50 |
| 15 | UDA-4-S2   | Bootstrap build_manifests auto-registration |

---

## CONDUCTOR START SEQUENCE

Before spawning session 1 (UDA-2-S1), run this initialization:

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity2

# 1. Verify worktree is on the right branch
git branch --show-current
# Expected: feature/universal-parity-2

# 2. Pull latest
git pull origin feature/universal-parity-2

# 3. Verify UDA-1-S8 completed (last Run 2 session)
grep -A2 "id: UDA-1-S8" 00_ARCHITECTURE/CONDUCTOR/universal-parity/session_queue.yaml
# Expected: status: completed

# 4. Verify all 15 UDA-2/3/4 briefs are present
for s in S1 S2 S3 S4 S5 S6 S7 S8 S9 S10; do
  brief="00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PARITY_UDA_2_${s}_v1_0.md"
  test -f "$brief" && echo "BRIEF UDA-2-${s}: OK" || echo "BRIEF UDA-2-${s}: MISSING"
done
for s in S1 S2 S3; do
  brief="00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PARITY_UDA_3_${s}_v1_0.md"
  test -f "$brief" && echo "BRIEF UDA-3-${s}: OK" || echo "BRIEF UDA-3-${s}: MISSING"
done
for s in S1 S2; do
  brief="00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PARITY_UDA_4_${s}_v1_0.md"
  test -f "$brief" && echo "BRIEF UDA-4-${s}: OK" || echo "BRIEF UDA-4-${s}: MISSING"
done

# 5. Verify UDA-2-S1 is pending
grep -A2 "id: UDA-2-S1" 00_ARCHITECTURE/CONDUCTOR/universal-parity/session_queue.yaml
# Expected: status: pending

# 6. Git status clean
git status --short
# Expected: nothing (or only untracked files)
```

If any brief is MISSING, read session_queue.yaml to find its brief_path and re-create it from the spec in UNIVERSAL_PARITY_PLAN_v1_0.md before proceeding.

---

## TYPESCRIPT COMPILE GATE (mandatory on every UDA-2 session)

Every session that touches `platform-mcp/` must pass:
```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity2/platform-mcp && npx tsc --noEmit
# Must exit 0
```

For UDA-3 sessions that touch `platform/`:
```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity2/platform && npx tsc --noEmit
# Must exit 0
```

---

## GATE RETRY RULE

If a gate fails on first run, spawn a patch sub-agent with: the brief + the specific failing gate output + instruction "Fix only the failing gate — do not modify anything else." If the gate still fails after the patch sub-agent, write a GATE-HALT and stop.

---

## PUSH CADENCE

Push to `origin feature/universal-parity-2` only at:
- After UDA-4-S2 (run complete)
- Any time a GATE-HALT fires

Intermediate sessions commit locally only.

---

## BEGIN

Run the start sequence above, then spawn UDA-2-S1 immediately. No confirmation needed.

---

*End of CONDUCTOR_KICKOFF_PROMPT_v3_0.md — HAP policy: DISABLED*
