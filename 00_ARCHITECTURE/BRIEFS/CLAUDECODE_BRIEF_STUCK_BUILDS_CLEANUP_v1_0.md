---
brief_id: STUCK_BUILDS_CLEANUP_v1_0
status: ACTIVE
authored_by: Cowork — under explicit native authorization
                ("do a complete diagnostic and fix it" + follow-up
                 amendment 2026-05-31 to extend scope to stuck builds)
executor: Claude Code in Google Antigravity IDE
authored_at: 2026-05-31
model_directive: Use Gemini Pro or DeepSeek. Anthropic banned.
worktree: /Users/Dev/Vibe-Coding/Apps/Madhav (main checkout)
work_branch: NONE — operator-replacement task; commits only if app code changes
prod_db_write_authorization: GRANTED for this task
  - tables in scope: builds, build_steps, build_notifications
  - scope: rows where chart_id = '362f9f17-95a5-490b-a5a7-027d3e0efda0'
           AND status IN ('running','queued','pending')
  - NO touch on: charts, chart_facts, profiles, any other table
relates_to: CLAUDECODE_BRIEF_DUPE_DIAGNOSTIC_AND_FIX_v1_0 (Case D outcome)
---

# CLAUDECODE_BRIEF — Stuck builds cleanup (operator-replacement task)

## Context

The duplicate-charts investigation closed as **Case D**: the DB has exactly 1
chart for native; the dashboard's "10-20 dupes" were 32 stuck build jobs piling
up against that single chart over the last 6h-39h, mix of `running` and
`queued`, never completing.

Native has authorized cleaning them up via SQL after first cancelling any
live Cloud Run executions. This brief is the contained execution plan.

Native chart: `362f9f17-95a5-490b-a5a7-027d3e0efda0`.

## Hard gates

- DO NOT touch `charts`, `chart_facts`, `profiles`, or any table other than
  `builds`, `build_steps`, `build_notifications`.
- DO NOT mark a DB build `cancelled` while its Cloud Run execution is still
  `Running`. Cancel the Cloud Run side first, wait, verify.
- DO NOT proceed past §2 backup unless backup row count equals the stuck-builds
  count from §1.
- DO NOT use Anthropic models.
- If any schema column referenced below doesn't exist (e.g. `cancel_reason`,
  `finished_at`), DROP THAT LINE and proceed — do not invent a column. Print
  what you dropped in the final report.

## §0 — Pre-flight (proxy + prod-DB confirm)

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform
mkdir -p /tmp/build_cleanup

# Start proxy if not already running
if ! nc -z 127.0.0.1 5433 2>/dev/null; then
  bash scripts/start_db_proxy.sh &
  sleep 5
fi

# Confirm prod
psql "$DATABASE_URL" -c "
  SELECT (SELECT COUNT(*) FROM charts) AS chart_rows,
         (SELECT COUNT(*) FROM builds WHERE chart_id='362f9f17-95a5-490b-a5a7-027d3e0efda0') AS native_builds_total;
" | tee /tmp/build_cleanup/00_db_check.txt
```

Gate G0: chart_rows must be ≥ 1 AND native_builds_total must be ≥ 32.

## §1 — Snapshot the stuck builds

```bash
psql "$DATABASE_URL" -c "
  SELECT build_id, status, started_at, finished_at,
         (SELECT COUNT(*) FROM build_steps WHERE build_id=b.build_id) AS step_count,
         (SELECT COUNT(*) FROM build_steps WHERE build_id=b.build_id AND status='complete') AS steps_complete
    FROM builds b
   WHERE chart_id = '362f9f17-95a5-490b-a5a7-027d3e0efda0'
     AND status IN ('running','queued','pending')
   ORDER BY started_at ASC NULLS FIRST;
" | tee /tmp/build_cleanup/01_stuck_builds.txt

STUCK_COUNT=$(psql "$DATABASE_URL" -tAc "
  SELECT COUNT(*) FROM builds
   WHERE chart_id='362f9f17-95a5-490b-a5a7-027d3e0efda0'
     AND status IN ('running','queued','pending');
")
echo "==> Stuck build count: $STUCK_COUNT"
```

If `$STUCK_COUNT` is 0, the dashboard was stale. HALT with that note.

## §2 — Cancel live Cloud Run executions FIRST

```bash
# List recent executions of the build job
gcloud run jobs executions list \
  --job=marsys-build-pipeline-job \
  --region=asia-south1 \
  --limit=60 \
  --format='value(name,status.conditions[0].type,status.completionTime,metadata.creationTimestamp)' \
  2>&1 | tee /tmp/build_cleanup/02_cloudrun_list.txt

# Pull names of executions that have no completionTime (still alive)
LIVE_EXECS=$(gcloud run jobs executions list \
  --job=marsys-build-pipeline-job \
  --region=asia-south1 \
  --limit=60 \
  --filter='-status.completionTime:*' \
  --format='value(name)' 2>/dev/null)

if [ -n "$LIVE_EXECS" ]; then
  echo "==> Live executions to cancel:"
  echo "$LIVE_EXECS"
  for EXEC in $LIVE_EXECS; do
    echo "==> Cancelling $EXEC"
    gcloud run jobs executions cancel "$EXEC" --region=asia-south1 --quiet
  done
  echo "==> Waiting 45s for cancellations to propagate"
  sleep 45
else
  echo "==> No live Cloud Run executions — DB cleanup is safe."
fi

# Verify no live executions remain
LIVE_AFTER=$(gcloud run jobs executions list \
  --job=marsys-build-pipeline-job \
  --region=asia-south1 \
  --limit=60 \
  --filter='-status.completionTime:*' \
  --format='value(name)' 2>/dev/null | wc -l | tr -d ' ')
echo "==> Live executions after cancel sweep: $LIVE_AFTER"
```

Gate G2: `LIVE_AFTER` must be 0. If not, HALT and report — don't update the DB
while jobs are still writing.

## §3 — Backup

```bash
TS=$(date +%Y%m%d_%H%M%S)
psql "$DATABASE_URL" -c "
  CREATE TABLE builds_backup_${TS} AS
  SELECT * FROM builds
   WHERE chart_id='362f9f17-95a5-490b-a5a7-027d3e0efda0'
     AND status IN ('running','queued','pending');
  SELECT COUNT(*) AS backed_up FROM builds_backup_${TS};
" | tee /tmp/build_cleanup/03_backup.txt
```

Gate G3: `backed_up` must equal `$STUCK_COUNT` from §1. Else HALT.

Also back up build_steps for the same build_ids:
```bash
psql "$DATABASE_URL" -c "
  CREATE TABLE build_steps_backup_${TS} AS
  SELECT * FROM build_steps
   WHERE build_id IN (
     SELECT build_id FROM builds_backup_${TS}
   );
  SELECT COUNT(*) AS steps_backed_up FROM build_steps_backup_${TS};
" | tee -a /tmp/build_cleanup/03_backup.txt
```

## §4 — Cleanup SQL (atomic, with sanity gate inside transaction)

First inspect actual columns to know what to update:
```bash
psql "$DATABASE_URL" -c "\d builds"     | tee /tmp/build_cleanup/04_builds_cols.txt
psql "$DATABASE_URL" -c "\d build_steps" | tee /tmp/build_cleanup/04_steps_cols.txt
```

Build the SQL based on actual columns. Template:

```bash
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 <<SQL 2>&1 | tee /tmp/build_cleanup/05_cleanup.log
BEGIN;

WITH stuck AS (
  SELECT build_id FROM builds
   WHERE chart_id='362f9f17-95a5-490b-a5a7-027d3e0efda0'
     AND status IN ('running','queued','pending')
)
, _b AS (
  UPDATE builds
     SET status='cancelled'
         /* IF column exists: */, finished_at = COALESCE(finished_at, NOW())
         /* IF column exists: */, cancel_reason = 'stale_cleanup_2026-05-31'
   WHERE build_id IN (SELECT build_id FROM stuck)
   RETURNING build_id
)
, _s AS (
  UPDATE build_steps
     SET status='cancelled'
         /* IF column exists: */, completed_at = COALESCE(completed_at, NOW())
   WHERE build_id IN (SELECT build_id FROM stuck)
     AND status IN ('running','pending')
   RETURNING build_id
)
, _n AS (
  INSERT INTO build_notifications (build_id, event_type, payload)
  SELECT build_id, 'build_cancelled',
         jsonb_build_object('reason', 'stale_cleanup_2026-05-31',
                            'cancelled_at', NOW()::text)
    FROM stuck
  RETURNING notif_id
)
SELECT (SELECT COUNT(*) FROM _b) AS builds_cancelled,
       (SELECT COUNT(*) FROM _s) AS steps_cancelled,
       (SELECT COUNT(*) FROM _n) AS notifications_emitted;

DO \$\$
DECLARE remaining int;
BEGIN
  SELECT COUNT(*) INTO remaining FROM builds
   WHERE chart_id='362f9f17-95a5-490b-a5a7-027d3e0efda0'
     AND status IN ('running','queued','pending');
  IF remaining > 0 THEN
    RAISE EXCEPTION 'Expected 0 stuck builds after cleanup, found %', remaining;
  END IF;
END \$\$;

COMMIT;
SQL
```

**Adaptation rule:** before running the heredoc, look at /tmp/build_cleanup/04_builds_cols.txt
+ 04_steps_cols.txt and DROP any line whose column doesn't exist. Record what
you dropped in the final report.

## §5 — Verify

```bash
psql "$DATABASE_URL" -c "
  SELECT status, COUNT(*) AS rows
    FROM builds
   WHERE chart_id='362f9f17-95a5-490b-a5a7-027d3e0efda0'
   GROUP BY 1 ORDER BY 1;
" | tee /tmp/build_cleanup/06_post_state.txt

# Confirm no live Cloud Run executions either
gcloud run jobs executions list \
  --job=marsys-build-pipeline-job \
  --region=asia-south1 \
  --limit=10 \
  --filter='-status.completionTime:*' \
  --format='value(name)' 2>/dev/null \
  | tee /tmp/build_cleanup/07_cloudrun_final.txt
```

§5 acceptance:
- Zero rows with status in (running, queued, pending).
- /tmp/build_cleanup/07_cloudrun_final.txt empty.

## §6 — Lifecycle: seal the prior brief

Update `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_DUPE_DIAGNOSTIC_AND_FIX_v1_0.md`:
1. Flip frontmatter `status: ACTIVE` → `status: COMPLETE`.
2. Add new section `## §7 — Outcome (session close 2026-05-31)` at end:

```markdown
## §7 — Outcome (session close 2026-05-31)

Classification: **Case D** (no duplicate charts in DB).

Root cause: native was viewing the "Builds In Progress" panel, not the chart
roster. DB had exactly 1 chart for native + 32 stuck build jobs against
chart_id 362f9f17… (mix of running/queued, ages 6h–39h).

Resolution path:
- This brief: confirmed no dupes (Case D); no chart-table changes made.
- Follow-up brief CLAUDECODE_BRIEF_STUCK_BUILDS_CLEANUP_v1_0.md cancelled
  the 32 stuck builds + their build_steps; emitted build_cancelled
  notifications.

Open follow-up (NEW brief required, NOT in this brief's scope): the build
orchestrator left jobs stuck for 6h–39h without timeout/auto-cancel. That's
a reliability bug. Author BUILD_TIMEOUT_HARDENING brief next session.
```

3. Update CURRENT_STATE_v1_0.md with one line under the most recent changelog
entry: `**Dupe-charts investigation closed Case D — see CLAUDECODE_BRIEF_DUPE_DIAGNOSTIC_AND_FIX §7. Stuck-builds cleanup via STUCK_BUILDS_CLEANUP brief.**`

4. Commit both file edits to a new branch `chore/dupe-investigation-closeout`:

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git checkout main
git pull origin main
git checkout -b chore/dupe-investigation-closeout
git add 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_DUPE_DIAGNOSTIC_AND_FIX_v1_0.md
git add 00_ARCHITECTURE/CURRENT_STATE_v1_0.md
git commit -m "chore(governance): seal DUPE_DIAGNOSTIC_AND_FIX brief — Case D outcome

Closes the duplicate-charts investigation: no dupes in DB. Surfaced 32 stuck
build jobs as the real symptom; cleaned up via STUCK_BUILDS_CLEANUP brief
(operator-replacement task, no app code change).

Open follow-up: BUILD_TIMEOUT_HARDENING brief to fix the orchestrator
reliability bug that lets builds stay stuck for 6h–39h."
git push -u origin chore/dupe-investigation-closeout
```

## §7 — Final report (executor prints to console)

```
=== STUCK BUILDS CLEANUP REPORT ===
Cloud Run live executions cancelled:   <N>
DB stuck builds (pre):                 <STUCK_COUNT>
Backup table:                          builds_backup_<TS> (<rows> rows)
Backup table (steps):                  build_steps_backup_<TS> (<rows> rows)
Builds marked cancelled:               <count>
Build steps marked cancelled:          <count>
build_cancelled notifications emitted: <count>
Stuck builds remaining:                0 (must be 0)
Columns dropped from cleanup SQL:      <list, e.g. cancel_reason on builds>
Files preserved at:                    /tmp/build_cleanup/
Brief sealed:                          DUPE_DIAGNOSTIC_AND_FIX_v1_0 (status COMPLETE)
Governance commit:                     <commit_sha on chore/dupe-investigation-closeout>
=== END REPORT ===

Operator follow-up:
  1. Hard-refresh dashboard tab (Cmd-Shift-R). "Builds In Progress" should drop to 0.
  2. Review + merge PR opened from chore/dupe-investigation-closeout (docs only).
  3. Next Cowork session: request BUILD_TIMEOUT_HARDENING brief — the real fix.

Backup restore (if anything went wrong):
  psql "$DATABASE_URL" -c "
    UPDATE builds b SET status = bb.status, finished_at = bb.finished_at
      FROM builds_backup_<TS> bb
     WHERE b.build_id = bb.build_id;
  "
```

## Acceptance criteria

- [ ] §0 prod DB confirmed.
- [ ] §1 stuck-build snapshot saved with count.
- [ ] §2 zero live Cloud Run executions remain.
- [ ] §3 backup row count equals §1 count (both builds + build_steps).
- [ ] §4 cleanup SQL committed; sanity check inside transaction passed.
- [ ] §5 verify shows 0 stuck builds remaining; Cloud Run also clear.
- [ ] §6 prior brief sealed; CURRENT_STATE one-liner appended; commit pushed.
- [ ] §7 final report printed to console.

---

End of brief.
