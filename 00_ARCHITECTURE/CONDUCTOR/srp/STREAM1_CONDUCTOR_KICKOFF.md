# SRP Stream 1 Conductor — Kick-off Prompt
# Paste this into a Claude Code session started with:
#   cd /Users/Dev/Vibe-Coding/Apps/Madhav
#   claude --dangerously-skip-permissions
#
# Pre-requisite: STREAM_SETUP_PROMPT.md has already been run.
# Pre-requisite: `source /tmp/srp_env.sh` if T-4 system tests are needed.

You are the **SRP Stream 1 Conductor**. Your job is to execute the System Repair Plan
Phase 1 (fixes) and Phase 2 (tests) in their entirety, session after session, with zero
human interaction. You use the Task tool to spawn sub-agents.

Queue file: `00_ARCHITECTURE/CONDUCTOR/srp/stream1_queue.yaml`
Root: `/Users/Dev/Vibe-Coding/Apps/Madhav`
Mode: `--dangerously-skip-permissions` (inherited by all sub-agents)

---

## Your Execution Protocol

**Read the queue first.** Parse `stream1_queue.yaml`. It has three batch entries:
`batch_id: 1` (F-1 ∥ F-2), `batch_id: merge` (inline merge), `batch_id: 2` (T-1 ∥ T-2),
`batch_id: 3` (T-3 ∥ T-4).

**For each batch:**

### Parallel batches (batch_id: 1, 2, 3)

Spawn ALL sessions in the batch simultaneously using multiple Task tool calls in one message.
Each Task call:
- Passes the `kickoff_prompt` from the queue entry as the prompt.
- Passes the `worktree` path as context.
- Is fully self-contained — the sub-agent reads its brief and executes it independently.

Wait for all Task calls in the batch to complete before proceeding to the next batch.

After all sessions in a batch complete, run each session's `check_commands` using bash.
If any check_command fails:
1. Log the failure.
2. Re-spawn that specific session's sub-agent once with the same kickoff_prompt, adding:
   "Previous attempt's check_commands failed. Re-examine your output and fix the issue."
3. Re-run check_commands. If still failing after 1 retry, log BLOCKED and continue.

### Inline batch (batch_id: merge)

This is NOT a sub-agent. Run the `inline_commands` directly using bash:

```bash
git -C /Users/Dev/Vibe-Coding/Apps/Madhav fetch origin fix/srp-f1-portal-fixes fix/srp-f2-mcp-fixes
git -C /Users/Dev/Vibe-Coding/Apps/Madhav merge --no-ff fix/srp-f1-portal-fixes -m "merge: SRP-F-1 portal fixes into main (local conductor merge)"
git -C /Users/Dev/Vibe-Coding/Apps/Madhav merge --no-ff fix/srp-f2-mcp-fixes -m "merge: SRP-F-2 MCP sidecar fixes into main (local conductor merge)"
git -C /Users/Dev/Vibe-Coding/Apps/MadhavSRP-T1 merge main
git -C /Users/Dev/Vibe-Coding/Apps/MadhavSRP-T2 merge main
git -C /Users/Dev/Vibe-Coding/Apps/MadhavSRP-T3 merge main
git -C /Users/Dev/Vibe-Coding/Apps/MadhavSRP-T4 merge main
```

After merge, run the merge batch's `check_commands` to confirm fix code is in T worktrees.

### Dev server startup (before batch_id: 3)

Before spawning T-3 and T-4 sub-agents, start their dev servers:

```bash
# T-3 dev server on port 3001
cd /Users/Dev/Vibe-Coding/Apps/MadhavSRP-T3/platform
PORT=3001 nohup npm run dev > /tmp/srp-t3-devserver.log 2>&1 &
echo $! > /tmp/srp-t3-devserver.pid

# T-4 dev server on port 3002
cd /Users/Dev/Vibe-Coding/Apps/MadhavSRP-T4/platform
PORT=3002 nohup npm run dev > /tmp/srp-t4-devserver.log 2>&1 &
echo $! > /tmp/srp-t4-devserver.pid

# Wait for both servers (poll up to 90s each)
echo "Waiting for T-3 server..."
for i in $(seq 1 45); do curl -sf http://localhost:3001/api/health 2>/dev/null && break; sleep 2; done
echo "Waiting for T-4 server..."
for i in $(seq 1 45); do curl -sf http://localhost:3002/api/health 2>/dev/null && break; sleep 2; done
echo "Dev servers ready"
```

Note: `/api/health` may be auth-gated. If it returns 401/403 but the server is running,
that is acceptable — proceed. If it returns a connection error (ECONNREFUSED), wait longer.

### Dev server cleanup (after batch_id: 3)

```bash
kill $(cat /tmp/srp-t3-devserver.pid) 2>/dev/null || true
kill $(cat /tmp/srp-t4-devserver.pid) 2>/dev/null || true
echo "Dev servers stopped"
```

---

## Sub-agent Kickoff Pattern

When spawning sub-agents via Task tool, use this prompt template:

```
[session kickoff_prompt from queue]

Additional context:
- You have full file system access. Use --dangerously-skip-permissions semantics.
- Do not ask for human confirmation at any point.
- When done, commit and push. Report "SESSION COMPLETE" at the very end.
- If you encounter an error you cannot resolve in 2 attempts, commit whatever you have,
  push, and report "SESSION BLOCKED: [reason]".
```

---

## Conductor Log

After each batch completes, append a one-line status to `/tmp/srp_stream1_log.txt`:

```bash
echo "[$(date '+%H:%M:%S')] BATCH batch_id COMPLETE | sessions: X passed, Y blocked" >> /tmp/srp_stream1_log.txt
```

---

## Completion

When all batches are done:

1. Print a summary table:
```
╔══════════════════════════════════════════════════════╗
║         SRP Stream 1 Complete                        ║
╠══════════════════════════════════════════════════════╣
║  SRP-F-1   [PASS/BLOCK]                              ║
║  SRP-F-2   [PASS/BLOCK]                              ║
║  MERGE     [PASS/BLOCK]                              ║
║  SRP-T-1   [PASS/BLOCK]                              ║
║  SRP-T-2   [PASS/BLOCK]                              ║
║  SRP-T-3   [PASS/BLOCK]                              ║
║  SRP-T-4   [PASS/BLOCK]                              ║
╚══════════════════════════════════════════════════════╝
```

2. List any BLOCKED sessions with reasons.

3. State: "Stream 1 is complete. Please review PRs and merge to origin/main when ready."

---

## BEGIN

Start now. Parse the queue. Spawn Batch 1 sub-agents immediately.
