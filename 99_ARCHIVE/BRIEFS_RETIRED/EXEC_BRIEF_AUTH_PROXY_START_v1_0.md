---
brief_id: EXEC_BRIEF_AUTH_PROXY_START
version: 1.0
status: AUTHORED
authored_by: Cowork (Opus)
authored_at: 2026-04-28
target_executor: Claude Code session (Sonnet 4.6) in Anti-Gravity / VS Code
trigger_phrase: "Read EXEC_BRIEF_AUTH_PROXY_START_v1_0.md and execute it."
phase: operational
phase_name: Start Cloud SQL Auth Proxy + Verify
risk_classification: LOW (operational; no code changes)
parallelizable_with: [any code work — Auth Proxy is independent infrastructure]
output_artifact: /tmp/cloud_sql_proxy.log + stdout summary
---

# EXEC_BRIEF — Start Cloud SQL Auth Proxy

## Mission

Phase 12's pre-flight gate requires Cloud SQL Auth Proxy running locally. Native asked Cowork to author a Claude Code prompt that handles starting it cleanly. This brief discovers the GCP instance connection string via `gcloud`, detects which proxy binary is installed (modern `cloud-sql-proxy` or legacy `cloud_sql_proxy`), starts the proxy detached so it survives the Sonnet session, and verifies it's actually accepting connections on the standard port.

After this brief completes, native can immediately re-trigger Phase 12 with the pre-flight gate satisfied.

## Scope

**`may_touch`:**
- The OS process table (start a new background process)
- `/tmp/cloud_sql_proxy.log` (new — capture stdout/stderr from the proxy)
- `/tmp/auth_proxy_start_report.txt` (new — summary report)

**`must_not_touch`:**
- Any source file in the repo
- Any env file (the proxy reads service-account credentials from the user's gcloud login or `GOOGLE_APPLICATION_CREDENTIALS` env var; this brief doesn't change those)
- Any database content
- Any other running process (don't touch the dev server, don't touch any other proxy if one is running)

## Streams (5 sequential)

### Stream A — Pre-flight checks

1. Verify `gcloud` is installed:
   ```bash
   command -v gcloud >/dev/null 2>&1 && gcloud --version | head -1
   ```
   If missing, halt with: "gcloud SDK is not installed. Install from https://cloud.google.com/sdk/docs/install before re-running."

2. Verify gcloud is authenticated and has a default project:
   ```bash
   gcloud config get-value project 2>/dev/null
   gcloud auth list --filter=status:ACTIVE --format='value(account)' 2>/dev/null
   ```
   If no project or no active account, halt with: "Run `gcloud auth login` and `gcloud config set project <PROJECT_ID>` first."

3. Check whether a proxy process is already running:
   ```bash
   pgrep -fl 'cloud[_-]sql[_-]proxy' || echo "no proxy running"
   ```
   If a proxy IS already running, capture its PID and command line. **Do NOT kill it.** Skip to Stream D (verify) and report that the proxy was already running.

### Stream B — Detect proxy binary + discover instance connection name

1. Detect which proxy binary is installed. Try, in order:
   ```bash
   command -v cloud-sql-proxy   # modern (v2)
   command -v cloud_sql_proxy   # legacy (v1)
   ```
   Capture which one resolves. Note the version:
   ```bash
   <binary-name> --version 2>&1 | head -1
   ```
   If neither is installed, halt with: "Cloud SQL Auth Proxy is not installed. Install from https://cloud.google.com/sql/docs/postgres/sql-proxy#install before re-running."

2. Discover the instance connection name. The AM-JIS Cloud SQL instance is `amjis-postgres` in region `asia-south1` per project memory.
   ```bash
   gcloud sql instances describe amjis-postgres \
     --format='value(connectionName)' 2>&1
   ```
   Expected output format: `<PROJECT_ID>:asia-south1:amjis-postgres`. Capture it as `INSTANCE_CONNECTION_NAME`.

   If the command errors (instance not found, no permission), halt with the error message and the suggestion: "Run `gcloud sql instances list` to confirm the instance name and your gcloud account has access."

### Stream C — Start the proxy detached

1. Start the proxy with the detected binary, capturing logs to `/tmp/cloud_sql_proxy.log`:

   **For modern `cloud-sql-proxy` (v2):**
   ```bash
   nohup cloud-sql-proxy "$INSTANCE_CONNECTION_NAME" \
     --port=5432 \
     > /tmp/cloud_sql_proxy.log 2>&1 &
   echo "Started PID $!"
   disown
   ```

   **For legacy `cloud_sql_proxy` (v1):**
   ```bash
   nohup cloud_sql_proxy \
     -instances="$INSTANCE_CONNECTION_NAME=tcp:5432" \
     > /tmp/cloud_sql_proxy.log 2>&1 &
   echo "Started PID $!"
   disown
   ```

2. **Note on port 5432**: this is the standard Postgres port. If the dev environment expects a different port, the connection string in `lib/db/client.ts` will tell us. Read it once to confirm:
   ```bash
   grep -E "host|port" platform/src/lib/db/client.ts | head -10
   ```
   If the code expects a non-standard port (e.g., 5433), use that instead in the proxy command above.

3. Capture the proxy's PID for the report.

### Stream D — Verify the proxy is reachable

1. Wait up to 15 seconds for the proxy to be ready. Poll TCP connect on the port:
   ```bash
   for i in {1..15}; do
     if nc -z localhost 5432 2>/dev/null; then
       echo "Proxy reachable on localhost:5432"; break
     fi
     sleep 1
   done
   ```
   If after 15 seconds nothing responds, dump the proxy log and halt:
   ```bash
   tail -30 /tmp/cloud_sql_proxy.log
   ```

2. Optional deeper check — try a `psql` ping if `psql` is installed:
   ```bash
   command -v psql && PGPASSWORD="${DB_PASSWORD:-}" psql \
     -h localhost -p 5432 \
     -U "${DB_USER:-postgres}" -d "${DB_NAME:-amjis}" \
     -c "SELECT 1 as ping;" 2>&1 | tail -5
   ```
   This is non-blocking — even if psql isn't installed or env vars aren't set, the TCP probe in step 1 is sufficient evidence the proxy is up.

3. Re-confirm the proxy process is alive after the wait:
   ```bash
   pgrep -fl 'cloud[_-]sql[_-]proxy'
   ```
   Should return at least one PID. Capture it.

### Stream E — Report

Write `/tmp/auth_proxy_start_report.txt` with:

```
Cloud SQL Auth Proxy — Start Report
====================================
Date: <timestamp>
gcloud project: <project>
gcloud account: <account>
Binary: <cloud-sql-proxy or cloud_sql_proxy>
Binary version: <version line>
Instance connection: <INSTANCE_CONNECTION_NAME>
Local port: 5432 (or other if detected)
Process PID: <PID>
TCP reachable: ✅ / ✗
Log file: /tmp/cloud_sql_proxy.log

Status: READY for Phase 12 / OR: FAILED — see log

Native action:
  re-trigger Phase 12 with:
    Read EXEC_BRIEF_PHASE_12_v1_0.md and execute it.

  to stop the proxy later:
    pkill -f 'cloud[_-]sql[_-]proxy'
```

Print the report to stdout.

## Critical constraints

- **No code changes.** Pure operational brief.
- **Detached process.** Use `nohup ... & disown` so the proxy survives Sonnet's session.
- **No password management.** This brief does NOT set `DB_PASSWORD` or `GOOGLE_APPLICATION_CREDENTIALS`. The Auth Proxy uses the user's gcloud login by default. If the dev server expects a password env var separately, that's the user's `.env.local` setup, not this brief's territory.
- **Idempotent.** If a proxy is already running, leave it alone and report success.
- **Halt on missing prerequisites.** If `gcloud` isn't installed, isn't authenticated, or the proxy binary isn't installed, halt with a clear actionable message — do not attempt to install anything.
- **Surface failures verbosely.** If the proxy doesn't come up, dump the last 30 lines of its log to stdout so native can debug.

## Done criteria

1. `gcloud` is installed, authenticated, and has a project set (or brief halts cleanly with instructions).
2. Proxy binary is detected (or brief halts cleanly).
3. `INSTANCE_CONNECTION_NAME` is discovered via `gcloud sql instances describe`.
4. Proxy process is running detached, log captured to `/tmp/cloud_sql_proxy.log`.
5. TCP probe on localhost:5432 succeeds within 15 seconds.
6. `pgrep -fl 'cloud[_-]sql[_-]proxy'` returns at least one PID.
7. Report at `/tmp/auth_proxy_start_report.txt` exists and reflects the outcome.

## How native triggers

In a Claude Code session in Anti-Gravity (Sonnet 4.6 in VS Code extension):

> Read EXEC_BRIEF_AUTH_PROXY_START_v1_0.md and execute it.

Typical runtime: 5-15 seconds. After completion, immediately re-trigger Phase 12 with the standard trigger phrase.

## Status updates

- AUTHORED 2026-04-28
- IN_PROGRESS_STREAM_X — set when Sonnet picks up the brief
- COMPLETE — set when proxy is verified reachable on the expected port
