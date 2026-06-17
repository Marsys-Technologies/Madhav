---
brief_id: EXEC_BRIEF_PHASE_13_VERIFY
version: 1.0
status: AUTHORED
authored_by: Cowork (Opus)
authored_at: 2026-04-28
target_executor: Claude Code session (Sonnet 4.6) in Anti-Gravity / VS Code
trigger_phrase: "Read EXEC_BRIEF_PHASE_13_VERIFY_v1_0.md and execute it."
phase: 13.verify
phase_name: Phase 13 Restart + Verify Fix Took Effect
risk_classification: LOW (operational + diagnostic; no code changes)
parallelizable_with: []
depends_on: [EXEC_BRIEF_PHASE_13_RETRIEVAL_AUDIT_v1_0.md (COMPLETE)]
output_artifact: platform/scripts/cutover/phase13_verify_report.md
---

# EXEC_BRIEF — Phase 13 Verify — Restart + Confirm Fix Active

## Mission

Phase 13 audit shipped three fixes (vector_search.ts SQL repair, top_K bump, audit_log migration). Native re-ran the D1 query and got an identical broken response with the same `[EXTERNAL_COMPUTATION_REQUIRED]` markers. This means either (a) the fix is on disk but the dev server's compiled bundle is stale, or (b) the fix didn't actually fix what it intended to fix.

This brief restarts the dev server cleanly, verifies the SQL change is in memory, runs a fresh test query directly against the API, and inspects the resulting `audit_log` row to confirm `vector_search` is now succeeding. If the fix is loaded and working, the report says so. If the fix is loaded but still failing, the report dumps the actual SQL error and points at the next debugging step.

## Pre-flight gate

1. **Cloud SQL Auth Proxy MUST be running** (`pgrep -fl 'cloud[_-]sql[_-]proxy'` returns at least one PID). If not, halt with: "Start Auth Proxy first."
2. Verify the Phase 13 fix is on disk in `vector_search.ts`:
   ```bash
   grep -c "native_id" platform/src/lib/retrieve/vector_search.ts
   ```
   Should return `0` (the phantom column reference is gone). If non-zero, halt with: "Phase 13 SQL fix is not on disk — re-run Phase 13 brief first."
3. Verify the top_K bump is on disk:
   ```bash
   grep "VECTOR_SEARCH_TOP_K_DEFAULT" platform/src/lib/config/feature_flags.ts
   ```
   Should show `20`. If `10`, halt: "top_K bump not applied."
4. Verify migration 011 is applied to live DB:
   ```sql
   -- via psql with Auth Proxy
   SELECT to_regclass('public.audit_log') IS NOT NULL AS audit_log_exists;
   ```
   Should return `true`. If `false`, halt: "Migration 011 not applied."

If any check fails, print the failure and STOP.

## Scope

**`may_touch` (operations):**
- OS process table (kill stale dev server processes)
- `platform/.next/` (delete to force fresh build)
- `/tmp/marsys_dev_server.log` (capture restart output)
- `platform/scripts/cutover/phase13_verify_report.md` (new report)
- `platform/scripts/cutover/phase13_verify_audit_row.json` (new evidence dump)

**`must_not_touch`:**
- Any source file (this is verification, not new fixes)
- Any feature flag, env file, or `.env.local`
- Any DB content (read-only inspection of audit_log)
- The chart record, msr_signals, rag_chunks, rag_embeddings (read-only)

## Streams (5 sequential)

### Stream A — Stop stale dev server + clear cache + restart

1. Find and kill any node/next process bound to port 3000-3002:
   ```bash
   lsof -i :3000 -i :3001 -i :3002 2>/dev/null | grep -E "node|next|LISTEN" | awk '{print $2}' | sort -u
   ```
   For each PID, capture `ps -p <PID> -o command=`, then `kill -TERM <PID>`. Wait 3 seconds. If still alive, `kill -KILL <PID>`. Verify ports are free.

2. Clear Next.js build cache:
   ```bash
   rm -rf platform/.next
   ```

3. Start fresh dev server detached, capturing logs:
   ```bash
   cd platform
   nohup npm run dev > /tmp/marsys_dev_server.log 2>&1 &
   echo "Started PID $!"
   disown
   cd ..
   ```

4. Poll for readiness up to 60 seconds, checking ports 3000 and 3001:
   ```bash
   for i in {1..30}; do
     if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null | grep -q "200\|301\|302\|307"; then
       echo "Server up on port 3000"; export PORT=3000; break
     elif curl -s -o /dev/null -w "%{http_code}" http://localhost:3001 2>/dev/null | grep -q "200\|301\|302\|307"; then
       echo "Server up on port 3001"; export PORT=3001; break
     fi
     sleep 2
   done
   ```
   If no port responds in 60s, dump `tail -50 /tmp/marsys_dev_server.log` and halt.

**Stream A output:** killed PIDs, cleared `.next`, fresh PID, port the server bound to, first 30 lines of dev server log.

### Stream B — Trigger a test query directly against the API

The native is going to keep getting the same response from the existing chat thread because the chat session caches state. We bypass that by calling `/api/chat/consume` directly with curl, using the native's session cookie.

1. Read the SMOKE_SESSION_COOKIE and SMOKE_CHART_ID environment variables. If either is unset, halt with: "Set SMOKE_SESSION_COOKIE (paste __session cookie value from browser DevTools) and SMOKE_CHART_ID environment variables, then re-run."

2. Construct a fresh test query (do NOT reuse an existing chat thread). Use curl with a new conversation_id:
   ```bash
   NEW_CONV_ID=$(uuidgen)
   curl -s -X POST "http://localhost:${PORT:-3000}/api/chat/consume" \
     -H "Content-Type: application/json" \
     -H "Cookie: __session=${SMOKE_SESSION_COOKIE}" \
     -d "{
       \"chartId\": \"${SMOKE_CHART_ID}\",
       \"conversationId\": \"${NEW_CONV_ID}\",
       \"messages\": [{\"role\": \"user\", \"content\": \"What is my D1 chart? List Sun, Moon, and Ascendant with sign, degree, and house.\"}],
       \"model\": \"claude-sonnet-4-6\",
       \"style\": \"acharya\"
     }" \
     -o /tmp/phase13_verify_response.txt \
     -w "HTTP %{http_code}\n"
   echo "New conversation_id: $NEW_CONV_ID"
   ```

3. If the HTTP status is non-2xx, halt and dump `/tmp/phase13_verify_response.txt`.

4. Wait 5 seconds for audit row to land (audit writes are best-effort and async).

**Stream B output:** new conversation_id, HTTP status, response excerpt (first 1000 chars of response body).

### Stream C — Inspect the audit row

1. Pull the most recent audit row matching the new conversation_id:
   ```sql
   SELECT 
     id,
     query_id,
     query_text,
     query_class,
     bundle_keys,
     jsonb_pretty(tools_called) AS tools,
     synthesis_input_tokens,
     synthesis_output_tokens,
     LEFT(final_output, 800) AS output_preview,
     created_at
   FROM audit_log
   ORDER BY created_at DESC
   LIMIT 1;
   ```
   Capture full row to `platform/scripts/cutover/phase13_verify_audit_row.json`.

2. **Critical inspections:**
   a. Is `vector_search` in `tools_called`? If NO, the router didn't authorize it — Fix A's authorization is incomplete or didn't take effect.
   b. If YES, what does the `vector_search` entry's result count look like? Look in the `params_hash` and any nested result metadata. If 0 rows returned, the SQL is still failing (fix didn't take effect or has a different bug). If 20 rows returned, the SQL is now working.
   c. What does `synthesis_input_tokens` show? If under 1500, the prompt was tiny (vector_search didn't inject content). If 4000-10000, content is flowing.
   d. Does `output_preview` contain `[EXTERNAL_COMPUTATION_REQUIRED]` markers? Compare to the user's previous response — fewer markers = improvement.

3. **Cross-check via dev server logs:** look for any SQL errors logged after the test query was submitted:
   ```bash
   tail -100 /tmp/marsys_dev_server.log | grep -iE "(error|warn|vector_search|rag_embeddings|sql)" | head -30
   ```

**Stream C output:** audit row JSON dump path, table summarizing tools_called / chunks_returned / synthesis_input_tokens / ECR-marker-count, any SQL errors from the dev log.

### Stream D — Diagnose

Synthesize Streams A-C into one of these verdicts:

- **Verdict A — Fix verified, problem solved.** Dev server has new code; vector_search returns 10-20 chunks; synthesis_input_tokens is substantial; final output has fewer or zero ECR markers. Native re-runs query in browser via fresh chat to confirm UX-side.
- **Verdict B — Fix loaded but still failing.** Dev server has new code; vector_search is called but returns 0 rows or errors. Dump the SQL error from server log. Likely additional schema mismatch (e.g., `e.embedding` column, JOIN keys, vector dimension mismatch). Recommend follow-up brief with the specific error text.
- **Verdict C — Fix not actually loaded.** Server logs show old SQL with `native_id` reference still firing. Investigation: is there a build cache somewhere `rm -rf .next` didn't catch (e.g., `node_modules/.cache`, Turbopack cache)? Or did the file get reverted somehow?
- **Verdict D — Different failure.** Tests show the LLM has the data but is still emitting ECR markers anyway (synthesis-prompt issue, not retrieval). Recommend a prompt-side fix.

**Stream D output:** verdict + cited evidence + recommended next action.

### Stream E — Report + native action

Write `platform/scripts/cutover/phase13_verify_report.md` with sections from each stream above + a clear closing "Native Action" section:

- If Verdict A: "Open browser, start a fresh chat at `/clients/<chart_id>/consume`, ask 'what is my D1 chart', confirm degrees and cusps now appear."
- If Verdict B/C/D: a specific debugging step or follow-up brief outline.

Print summary to stdout.

## Critical constraints

- **No code changes** during this verify pass. If a code change is needed, document it in the report and halt.
- **Detached server.** `nohup ... & disown` so the proxy survives Sonnet's session.
- **Real LLM call.** Stream B exercises the full pipeline against real APIs and the live DB — not mocks. This is the only way to know whether the fix actually works in production conditions.
- **Don't reuse existing chat threads.** A new `conversation_id` ensures no client-side state pollution from prior failures.
- **Cite specific evidence.** Every finding references either a captured response file, an audit row column, or a server log line.

## Done criteria

1. Pre-flight gate: all 4 conditions verified.
2. Stream A: stale processes killed, `.next` deleted, fresh server up on a known port.
3. Stream B: fresh test query submitted via curl with HTTP 2xx response.
4. Stream C: audit row captured; tools_called and synthesis_input_tokens inspected; SQL errors (if any) captured from dev log.
5. Stream D: verdict (A/B/C/D) determined with cited evidence.
6. Stream E: report written; Native Action section is specific and actionable.

## How native triggers

In a Claude Code session in Anti-Gravity (Sonnet 4.6 in VS Code extension), with `SMOKE_SESSION_COOKIE` and `SMOKE_CHART_ID` env vars set + Auth Proxy running:

> Read EXEC_BRIEF_PHASE_13_VERIFY_v1_0.md and execute it.

Typical runtime: 90-180 seconds (~60s for server boot + 30-60s for the live LLM call + audit inspection).

After completion, the report tells you exactly which verdict applies and what to do next.

## Status updates

- AUTHORED 2026-04-28
- IN_PROGRESS_STREAM_X — set when Sonnet picks up the brief
- COMPLETE — set when report exists with a clear verdict + native action
