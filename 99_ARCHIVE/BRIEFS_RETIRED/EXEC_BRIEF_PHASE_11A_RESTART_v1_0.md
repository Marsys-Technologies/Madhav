---
brief_id: EXEC_BRIEF_PHASE_11A_RESTART
version: 1.0
status: AUTHORED
authored_by: Cowork (Opus)
authored_at: 2026-04-28
target_executor: Claude Code session (Sonnet 4.6) in Anti-Gravity / VS Code
trigger_phrase: "Read EXEC_BRIEF_PHASE_11A_RESTART_v1_0.md and execute it."
phase: 11A.restart
phase_name: Phase 11A — Dev Server Restart + Singleton Refresh + Verify
risk_classification: LOW (operational, no code changes)
parallelizable_with: []
depends_on: [EXEC_BRIEF_PHASE_11A_INVESTIGATION_v1_0.md (COMPLETE — diagnosis confirms stale singleton root cause)]
output_artifact: platform/scripts/cutover/stage1_restart_report.md
---

# EXEC_BRIEF — Phase 11A Restart — Kill Stale Dev Server, Clear Cache, Verify New Pipeline UI

## Mission

The diagnosis at `platform/scripts/cutover/stage1_diagnosis.md` identified the root cause: the dev server has been running since before Phase 11A's flag flip (Apr 26 vs Apr 28), and the in-process `configService` singleton in `config/index.ts:62` cached `NEW_QUERY_PIPELINE_ENABLED=false` from before the flip. Every consume page render asks the singleton, which still says `false`, so the UI renders legacy.

**Fix: kill the stale server process, clear the Next.js cache, start a fresh server, verify the new pipeline UI is now being served.** Zero code changes. Zero env changes. This is a pure operational reset.

## Scope

**`may_touch`:**
- The OS process table (kill old node processes bound to dev server ports)
- `platform/.next/` (delete to force a clean rebuild)
- `platform/scripts/cutover/stage1_restart_report.md` (new — output report)
- `/tmp/marsys_dev_server.log` (new — captured stdout/stderr from the new dev server for inspection)

**`must_not_touch`:**
- Any source file under `platform/src/`
- Any config file (`feature_flags.ts`, env files, `next.config.js`, `package.json`, etc.)
- Any test file
- Any documentation file (CLAUDE.md, SESSION_LOG, CURRENT_STATE, etc.)
- Any database content
- The git working tree state (no commits, no stash)

## Streams (5 sequential)

### Stream A — Identify and stop the stale dev server

1. Identify processes bound to ports likely in use by the dev server. Run:
   ```bash
   lsof -i :3000 -i :3001 -i :3002 2>/dev/null | grep -E "node|next|LISTEN"
   ```
   Capture the output. Note PIDs of any node/next processes on these ports.
2. For each PID identified, capture the full command line via `ps -p <PID> -o command=`. This is the audit trail for which process is being killed.
3. Stop each process gracefully first with `kill -TERM <PID>`. Wait 3 seconds.
4. Re-check the port. If the process is still alive, escalate with `kill -KILL <PID>`.
5. Verify all three ports (3000, 3001, 3002) are now free:
   ```bash
   lsof -i :3000 -i :3001 -i :3002 2>/dev/null
   ```
   Output should be empty (or only show non-node processes if any).
6. **Edge case:** if `lsof` is not available, use `ss -ltnp` or `netstat -tlnp` as fallbacks. Document which one was used.

Stream A output: section "Stream A — Process Cleanup" in the report listing PIDs killed, command lines, and final port-free confirmation.

### Stream B — Clear Next.js build cache

1. From the repo root, delete the Next.js build directory:
   ```bash
   rm -rf platform/.next
   ```
2. Verify deletion:
   ```bash
   ls -la platform/.next 2>&1 | head -5
   ```
   Expected: "No such file or directory" or empty.
3. Do NOT touch `node_modules/`, `.turbo/`, or any other cache directory. Just `.next/`.

Stream B output: section "Stream B — Cache Cleared" with the `ls -la` confirmation.

### Stream C — Start fresh dev server (detached)

1. Confirm we're targeting `platform/` as the working directory:
   ```bash
   ls platform/package.json
   ```
2. Start the dev server detached, capturing stdout + stderr to a log file:
   ```bash
   cd platform
   nohup npm run dev > /tmp/marsys_dev_server.log 2>&1 &
   echo "Started PID $!"
   disown
   cd ..
   ```
   Capture the printed PID — this is the new server.
3. Wait for the server to be ready. Poll the health of port 3000 (or fallback 3001) every 2 seconds for up to 60 seconds:
   ```bash
   for i in {1..30}; do
     if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null | grep -q "200\|301\|302\|307"; then
       echo "Server up on port 3000"; break
     elif curl -s -o /dev/null -w "%{http_code}" http://localhost:3001 2>/dev/null | grep -q "200\|301\|302\|307"; then
       echo "Server up on port 3001"; break
     fi
     sleep 2
   done
   ```
4. If after 60s no port responds, **abort and surface the log file contents** to native:
   ```bash
   tail -50 /tmp/marsys_dev_server.log
   ```
5. Note the actual port the server bound to. (It may be 3000 if previously occupying processes were truly stopped, or 3001 if something else is occupying 3000.)

Stream C output: section "Stream C — Server Restart" with the new PID, the port, and the first 30 lines of the dev-server log to confirm a clean compile.

### Stream D — Verify the new pipeline UI is being served

1. Pick the port confirmed in Stream C. Call it `PORT`.
2. Probe the root consume page:
   ```bash
   curl -s -o /tmp/consume_root_html.txt -w "%{http_code}" http://localhost:${PORT}/consume
   ```
   Note the HTTP status. (Likely a redirect to login; that's fine — we just need the server alive and responding.)
3. **Critical inspection:** because feature-flag values are server-side rendered into the page payload, we can grep for hints. Read the captured HTML/payload:
   ```bash
   grep -i -E "NEW_QUERY_PIPELINE|pipelineEnabled|StreamingAnswer|DisclosureTierBadge" /tmp/consume_root_html.txt | head -10
   ```
   If `NEW_QUERY_PIPELINE_ENABLED=true` is reflected anywhere in the rendered output, that's positive confirmation the singleton is now reading the new default.
4. Run `npm test platform/tests/unit/config/index.test.ts` (read-only invocation) to confirm the unit tests still pass against the new defaults — this is a sanity check that the code state matches what the singleton should pick up.
5. **Do NOT attempt to authenticate or submit a query.** The native handles UI verification themselves with their session cookie. Stream D's job is just to prove the server is up, healthy, and serving the new code path.

Stream D output: section "Stream D — Server Health + New-Pipeline Indicators" with the HTTP probe result, grep findings, and unit-test confirmation.

### Stream E — Report + handoff to native

1. Synthesize Streams A-D into the report at `platform/scripts/cutover/stage1_restart_report.md`.
2. Final section "Native Action": exactly what the native should do next, in order:
   ```
   1. Open http://localhost:<PORT>/clients/362f9f17-95a5-490b-a5a7-027d3e0efda0/consume in browser
   2. Confirm sticky-header DisclosureTierBadge appears (likely "super_admin")
   3. Send a test query
   4. Confirm:
      a. Token-by-token streaming appears
      b. Citation chips (amber/sky/violet) render in the response
      c. The query appears in /audit list
   5. If all green: pipeline is healthy. Decide whether to trigger Phase 11B
      (legacy code deletion) or stay in Phase 11A state for further observation.
   6. If anything wrong: capture screenshot + console errors and decide whether
      this is a real bug (author follow-up brief) or a session/cookie issue.
   ```
3. Append a one-line entry to `platform/scripts/cutover/stage1_diagnosis.md` (which already exists) noting that the restart was performed and Stream D's findings.
4. Print a clean ✅/✗ summary to stdout.

Stream E output: the report file written + stdout summary.

## Critical constraints

- **No code changes.** This brief is purely operational.
- **No long-lived blocking processes.** Dev server must be detached (`nohup ... &; disown`) so it survives Sonnet's session.
- **Verify before claiming success.** Stream D actually probes the running server. Don't conclude "fixed" without HTTP evidence.
- **Surface failures clearly.** If the server doesn't come up, dump the log tail to the report so native can debug.
- **Don't break the user's working state.** No git stash, no env edits, no file moves. Only operations: kill processes, delete `.next`, start fresh server.

## Done criteria

1. Stream A: stale node/next processes on ports 3000-3002 are stopped; ports verified free.
2. Stream B: `platform/.next` deleted.
3. Stream C: fresh dev server running detached, log capturing to `/tmp/marsys_dev_server.log`, server responding on a known port.
4. Stream D: HTTP probe returns expected status; new-pipeline indicators present in served output; unit tests still pass.
5. Stream E: `stage1_restart_report.md` exists, internally consistent, ends with explicit Native Action steps.

## How native triggers

In a Claude Code session in Anti-Gravity (Sonnet 4.6 in VS Code extension):

> Read EXEC_BRIEF_PHASE_11A_RESTART_v1_0.md and execute it.

After Sonnet completes (typically 60-90 seconds — the bottleneck is waiting for Next.js's first compile), open the URL specified in Stream E's Native Action section and verify the badge appears + a query produces streaming + citations.

## Status updates

- AUTHORED 2026-04-28
- IN_PROGRESS_STREAM_X — set when Sonnet picks up the brief
- COMPLETE — set when stage1_restart_report.md exists and Stream D's probe was green
