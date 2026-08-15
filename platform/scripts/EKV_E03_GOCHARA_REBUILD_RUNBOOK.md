# EKV E-03 Gochara Rebuild Runbook

**Lane**: B-09 → E-03 hand-off
**Asset**: `ka_gochara`
**Chart**: `482012f1-710e-4a25-994a-93821f5871aa` (Abhisek Mohanty, canonical native)
**Table**: `kala_gochara_windows_v2` (generation='2.0'; the protected v1 table `kala_gochara_windows` is never touched by this writer)
**Authored**: 2026-08-16, EKAVĀKYATĀ campaign B-09

---

## Prerequisites

Before running ANY step in this runbook, verify ALL of the following:

1. **B-01/02/03/04 lanes merged to main and deployed.**
   B-02 (nodal aspect fix) must be live — this is the fix that F-52 validates.
   Check: `gcloud run jobs describe brahma-build-pipeline-job --region=asia-south1`
   and confirm the image digest matches the post-B-02 deploy.

2. **`ka_gochara` is in a non-lit state, or you have a valid reason to force-rebuild.**
   Check: `SELECT state FROM asset_throughput WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa' AND asset_id = 'ka_gochara';`
   Expected: `dormant` or `NOT_FOUND`. If `lit`, use `--force` flag on dispatch script.

3. **cloud-sql-proxy running on 127.0.0.1:5433.**
   Start if needed: `cloud-sql-proxy <connection-name> --port=5433`

4. **DATABASE_URL set from gcloud secrets (never from .env.local for prod ops).**
   ```
   export DATABASE_URL=$(gcloud secrets versions access latest \
     --secret=DATABASE_URL --project=<project>)
   ```

5. **No active build_runs for this chart.**
   Check: `SELECT id, state, triggered_by FROM build_runs WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa' AND state IN ('planned', 'running');`
   Expected: 0 rows. If active runs exist, wait for them to complete or stop them via `stop_requested_at`.

---

## Step 1 — Canary Dispatch

Run the canary dispatch script:

```bash
python3 platform/scripts/dispatch_ekv_e03_gochara_canary_482012f1.py
```

The script will:
- Verify preconditions (non-lit state, no active runs).
- Create a `build_run` tagged `ekv-e03-gochara-canary-482012f1`.
- Print `run_id` to stderr.
- Print a `gcloud run jobs execute` command to stderr for copy-paste.

Copy the printed `gcloud` command and execute it in your terminal:

```
gcloud run jobs execute brahma-build-pipeline-job \
  --region=asia-south1 \
  --update-env-vars RUN_ID=<run_id>
```

### Watch substep progress

Poll `build_substep_progress` for `ka_gochara`:

```sql
SELECT substep_key, state, started_at, completed_at, rows_written
FROM build_substep_progress
WHERE run_id = '<run_id>'
ORDER BY position;
```

Also watch `asset_throughput`:

```sql
SELECT state, last_updated_at
FROM asset_throughput
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
  AND asset_id = 'ka_gochara';
```

`ka_gochara` uses the HEAVY writer shape (one substep per event_class from `gochara_resonance_map`). You will see substep rows appear for each event class (MARRIAGE, CAREER, HEALTH, etc.).

---

## Step 2 — F-52 Canary Assertion

**After the canary build completes** (or while it is running for event classes that finish early), run the F-52 verification:

**F-52 criterion**: Nodal terms (Rahu/Ketu) must appear in the native's MARRIAGE window. The B-02 fix (nodal aspect wiring) is the change that should cause nodes to appear here. If nodes do NOT appear, the fix is not functioning correctly.

### Option A — Automated check (if verify script exists)

```bash
python3 platform-mcp/scripts/verify_gochara_nodal.py \
  --chart-id 482012f1 \
  --event-class MARRIAGE
```

Expected output: at least one row with `Rahu` or `Ketu` in `term_breakdown` or `contributing_systems`.

### Option B — Manual SQL check

```sql
SELECT
  window_start, window_end, peak_date, valence,
  term_breakdown, contributing_systems
FROM kala_gochara_windows_v2
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
  AND generation = '2.0'
  AND event_class = 'MARRIAGE'
  AND (
    term_breakdown::text ILIKE '%rahu%'
    OR term_breakdown::text ILIKE '%ketu%'
    OR contributing_systems::text ILIKE '%rahu%'
    OR contributing_systems::text ILIKE '%ketu%'
  )
ORDER BY window_start;
```

**F-52 PASS**: query returns >= 1 row.
**F-52 FAIL**: query returns 0 rows → **STOP. Do NOT proceed to full dispatch.** Diagnose why B-02 nodal aspects are not contributing. Check: Is B-02 actually deployed? Are resonance targets for MARRIAGE populated in `gochara_resonance_map`? Are nodal arc contacts present in `bg_gochara_arcs`?

---

## Step 3 — Stall Watch (35-min rule)

**S7/SM-R-4 discipline**: If at T+35 minutes from dispatch there are ZERO new substep rows in `build_substep_progress` for this `run_id`, stop execution and diagnose.

### Monitoring query

```sql
SELECT
  COUNT(*) AS total_substeps,
  COUNT(*) FILTER (WHERE state = 'complete') AS done,
  MAX(completed_at) AS last_completion
FROM build_substep_progress
WHERE run_id = '<run_id>';
```

### 35-min stall action

If last_completion IS NULL or has not advanced in 35 minutes:

1. **Do NOT use `pg_terminate_backend`** — use the graceful stop mechanism:
   ```sql
   UPDATE build_runs
   SET stop_requested_at = now()
   WHERE id = '<run_id>';
   ```
2. Check Cloud Run job logs: `gcloud run jobs executions describe <execution_id> --region=asia-south1`
3. Check for lock contention: `SELECT * FROM pg_locks WHERE NOT granted;`
4. Do NOT re-dispatch until root cause is identified.

---

## Step 4 — Full Dispatch

**Precondition**: F-52 PASSED and canary build completed without stall.

Run the full dispatch script:

```bash
python3 platform/scripts/dispatch_ekv_e03_gochara_full_482012f1.py
```

The script will:
- Mark `ka_gochara` as `dormant` (so the orchestrator treats this as a genuine rebuild).
- Create a `build_run` tagged `ekv-e03-gochara-full-482012f1`.
- Print `run_id` to stderr.
- Print the `gcloud` execute command.

Execute the printed `gcloud` command. Apply the same 35-min stall watch (Step 3) using the new `run_id`.

---

## Step 5 — Post-Dispatch Validation

After the full build completes:

**1. Assert `ka_gochara` is lit:**

```sql
SELECT state
FROM asset_throughput
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
  AND asset_id = 'ka_gochara';
```

Expected: `lit`

**2. Assert rows exist in `kala_gochara_windows_v2`:**

```sql
SELECT COUNT(*), MIN(window_start), MAX(window_end)
FROM kala_gochara_windows_v2
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
  AND generation = '2.0';
```

Expected: COUNT > 0

**3. Assert F-52 still passes (re-run Step 2 Option B).**

**4. Check `kala_gochara_v2_build_state` for per-class horizon coverage:**

```sql
SELECT event_class, contacts_evaluated, rows_written, horizon_start_date, horizon_end_date, horizon_status
FROM kala_gochara_v2_build_state
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
  AND generation = '2.0'
ORDER BY event_class;
```

---

## DATA-REBUILD-IN-FLIGHT Protocol

If the build is still running at hand-back time (end of E-03 session):

1. Write the following entry in `LEDGER_E.md`:
   ```
   DATA-REBUILD-IN-FLIGHT: ka_gochara (chart 482012f1, run_id=<run_id>, triggered_by=ekv-e03-gochara-full-482012f1)
   ```
2. **E-04 battery treats this as non-blocking** — downstream lanes that read `kala_gochara_windows_v2` should note the in-flight state and may proceed with pre-rebuild data if they need read-only access, but should not write to or depend on the post-rebuild final state.
3. When the build completes, update `LEDGER_E.md`: remove the `DATA-REBUILD-IN-FLIGHT` line and add a completion note with the final row count from Step 5.

---

## Diagnostic Quick-Reference

| Symptom | Check |
|---|---|
| No substep rows at T+5 | Cloud Run execution started? Check `gcloud run jobs executions list` |
| F-52 returns 0 rows | B-02 deployed? `gochara_resonance_map` MARRIAGE targets populated? `bg_gochara_arcs` has Rahu/Ketu arcs? |
| Stall at specific event class | Check per-class build state: `SELECT * FROM kala_gochara_v2_build_state WHERE event_class='...'` |
| `ka_gochara` stays `dormant` after run | Check `build_runs` for error state; check Cloud Run logs |
| Collision warnings in logs | Expected and non-fatal per writer docstring; check `collisions` count in WriterResult notes |

---

*Generated by EKV B-09 for E-03 Stream operator use. Asset: `ka_gochara`. Campaign: EKAVĀKYATĀ.*
