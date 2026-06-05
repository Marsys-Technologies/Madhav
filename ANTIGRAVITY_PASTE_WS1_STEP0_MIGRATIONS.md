# WS-1 Step 0 — Apply migrations 118 / 124 / 125 / 126 / 127 — CC Prompt

> **Paste this entire block into your Claude Code chat in Google Antigravity IDE.**
> Brief: `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_WS1_DRIVABLE_PORTAL_v1_0.md` (§4.1)
> Branch: `feature/ws1-drivable-portal` (cut from tag `legacy-cleanup-arc-complete`)
> Repo: `/Users/Dev/Vibe-Coding/Apps/Madhav`

---

You are Claude Code in Google Antigravity IDE. WS-0C-2 sealed with 55 hits to build-orchestrator tables marked DEFERRED — code is correct, schema is incomplete. Step 0 applies the five outstanding migrations (118, 124, 125, 126, 127) to prod, converts the DEFERRED residual to valid code, and commits any code touch-ups required after the schema lands.

**Destructive operation.** Per the durable rule: read each migration before applying, dry-run where possible, apply one at a time, verify between each. No backup; commits are the audit trail.

## Step 0.A — Branch + proxy

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git fetch origin --tags
git tag -l 'legacy-cleanup-arc-complete' | grep -q . && echo "tag found" || { echo "Tag missing — halt"; exit 1; }
git checkout -b feature/ws1-drivable-portal legacy-cleanup-arc-complete

# Proxy
bash platform/scripts/start_db_proxy.sh &
PROXY_PID=$!
sleep 3
export PROD_DB_URL="postgresql://amjis_app@127.0.0.1:5433/amjis"
psql_prod() { psql "$PROD_DB_URL" -v ON_ERROR_STOP=1 "$@"; }
psql_prod -c "SELECT current_database(), now();" || { echo "Proxy fail"; exit 1; }
```

## Step 0.B — Locate + read each migration

```bash
# Find the 5 migration files
for n in 118 124 125 126 127; do
  find platform/supabase/migrations -maxdepth 1 -name "${n}_*.sql" -o -name "${n}.sql" 2>/dev/null
done | tee /tmp/ws1_step0_migrations.txt
cat /tmp/ws1_step0_migrations.txt

# If any number returns no file, halt and report — the brief assumed they exist; if not, the
# DEFERRED status of WS-0C-2 is misattributed.
test "$(wc -l < /tmp/ws1_step0_migrations.txt)" -ge 5 || { echo "Missing migrations — halt"; exit 1; }

# Read each — understand what it does before applying
while IFS= read -r mig; do
  echo "=== $mig ==="
  cat "$mig"
  echo "=== end $mig ==="
done < /tmp/ws1_step0_migrations.txt
```

For each migration, classify:
- **Pure additive** (`CREATE TABLE`, `CREATE INDEX`, `ADD COLUMN`) → safe to apply.
- **Destructive** (`DROP`, `ALTER ... DROP`, type changes that could lose data) → HALT; report each destructive op; do NOT apply without explicit native sign-off.
- **References tables that don't exist in current prod** → check upstream migrations; if a missing dependency surfaces, halt.

Write `/tmp/ws1_step0_classification.md` capturing the classification per migration.

## Step 0.C — Pre-apply schema snapshot

```bash
# Snapshot the existing schema for the tables these migrations will touch.
# (Refine the table list from Step 0.B based on what each migration references.)
psql_prod -c "\dt builds build_steps build_events build_notifications notification_views engine_versions" \
  2>&1 | tee /tmp/ws1_step0_schema_pre.txt

# Per-table column dump for any table the migrations will ALTER
for t in builds build_steps build_events; do
  psql_prod -c "\d $t" 2>&1 | head -40
done | tee -a /tmp/ws1_step0_schema_pre.txt
```

If any of these tables already has the columns/indexes the migration adds, the migration may already be partially applied — halt and report; we don't want to re-apply.

## Step 0.D — Check the migration tracker

```bash
# Supabase tracks applied migrations in supabase_migrations.schema_migrations (or similar).
# Find the actual tracker:
psql_prod -c "
SELECT table_schema, table_name FROM information_schema.tables
WHERE table_name LIKE '%migration%' OR table_name LIKE '%schema_version%'
ORDER BY table_schema, table_name;
"

# For each found tracker, check whether 118/124/125/126/127 are already recorded as applied:
# (refine query based on the tracker's schema)
psql_prod -c "SELECT version FROM supabase_migrations.schema_migrations WHERE version IN ('118','124','125','126','127') ORDER BY version;" \
  2>&1 | tee /tmp/ws1_step0_tracker.txt
# If any are recorded as applied but the schema doesn't reflect it (per Step 0.C) → halt; tracker drift.
# If any are recorded as applied AND schema matches → skip those during Step 0.E.
```

## Step 0.E — Apply one at a time

For each migration in `/tmp/ws1_step0_migrations.txt`, in numeric order:

```bash
apply_migration() {
  local mig="$1"
  local num=$(basename "$mig" | grep -oE '^[0-9]+')
  echo "=== Applying $num: $mig ==="

  # Run in a transaction so failure rolls back the migration only (not the connection)
  psql "$PROD_DB_URL" -v ON_ERROR_STOP=1 --single-transaction -f "$mig" 2>&1 \
    | tee /tmp/ws1_step0_apply_${num}.txt

  if [ "${PIPESTATUS[0]}" -ne 0 ]; then
    echo "FAIL: $num errored; transaction rolled back"
    return 1
  fi

  # Verify the tracker recorded it (if the migration is self-recording per Supabase convention)
  psql_prod -c "SELECT version FROM supabase_migrations.schema_migrations WHERE version = '$num';"
  # If not auto-recorded (migration is hand-written without the Supabase footer), insert manually:
  #   psql_prod -c "INSERT INTO supabase_migrations.schema_migrations (version) VALUES ('$num');"

  # Per-migration post-apply check
  echo "Post-apply schema for $num:"
  psql_prod -c "\dt builds build_steps build_events build_notifications notification_views engine_versions" 2>&1 | head -20

  return 0
}

# Apply in numeric order
while IFS= read -r mig; do
  apply_migration "$mig" || { echo "Halt — migration $mig failed"; break; }
done < <(sort -t/ -k4 -n /tmp/ws1_step0_migrations.txt)
```

**Halt rules during apply:**
- Any migration fails (the `--single-transaction` flag rolls back; the schema is unchanged).
- A migration completes but the tracker doesn't record it AND the migration didn't auto-insert.
- A migration completes but the expected tables/columns don't appear in `\dt` / `\d`.
- A migration creates a table whose name was in our LEGACY_TABLES kill list — that means we dropped something the new migration recreates; surface the conflict.

## Step 0.F — Re-run the WS-0C-2 DEFERRED grep

```bash
# The 55-hit DEFERRED residual from WS-0C-2 was specifically on these table names.
# After the migrations apply, the cited tables exist; the code becomes valid.
# Confirm by running a DB-existence check on the DEFERRED tables:
psql_prod -c "
SELECT table_name,
       CASE WHEN EXISTS (
         SELECT 1 FROM information_schema.tables
         WHERE table_schema='public' AND table_name = t.table_name
       ) THEN 'EXISTS' ELSE 'DROPPED' END AS status
FROM (VALUES ('builds'),('build_steps'),('build_events'),('build_notifications'),
             ('notification_views'),('engine_versions')) AS t(table_name)
ORDER BY status, table_name;
"
# All 6 should return EXISTS. Any DROPPED means a migration didn't land — investigate.
```

## Step 0.G — Code touch-up + commit

If any code citation requires re-pointing now that the schema is complete (e.g., a route that was stubbed in WS-0C-2 can now query the real table), make those edits in the same commit. Otherwise, the commit is migration-application-only with no source-tree changes — that's also valid (the migrations are tracked in the DB, not in code).

Typecheck (sanity — no code changes expected, but verify):
```bash
cd platform && npm run typecheck 2>&1 | grep -E "error TS|Found [0-9]+ error" | head && cd ..
```

Commit:
```bash
git add -A
git status   # should show migration tracker activity if any source files changed; otherwise no-op

# If no source changes, the commit is purely a milestone marker:
git commit --allow-empty -m "chore(ws1-step0): apply migrations 118/124/125/126/127 to prod

Activates the build orchestrator schema completion that WS-0C-2 left
DEFERRED. After this commit:
- build_notifications, notification_views, engine_versions exist in prod
- The 55-hit DEFERRED residual from WS-0C-2 now resolves against live
  schema; no further code changes needed for those citations
- S2's SSE wiring (next sub-stream) can read from a complete build
  orchestrator state

Applied: 118, 124, 125, 126, 127 (in numeric order, single-transaction each)
Verification: all 6 DEFERRED tables now EXIST in prod
Pre-apply tracker drift: [none / list any]

Refs WS-1 brief §4.1, predecessor tag legacy-cleanup-arc-complete"

git push origin feature/ws1-drivable-portal
```

## Step 0.H — Closeout

```bash
kill $PROXY_PID 2>/dev/null
```

Report:
- The 5 migrations applied successfully (or which failed + why).
- The DEFERRED-tables EXISTS check from Step 0.F.
- Any tracker drift surfaced in Step 0.D.
- The commit SHA.

**STOP. Do NOT proceed to S1 yet.** Native reviews Step 0's report. If clean, S1 paste prompt comes next.

---

## Hard stops (halt and report — do not attempt unauthorized fix)

- Any migration file in 118/124/125/126/127 is missing from `platform/supabase/migrations/`.
- Step 0.B classification finds a destructive migration (DROP, type change, etc.).
- Pre-apply schema shows the migration's target tables in an unexpected state (e.g., partially applied).
- Step 0.D shows tracker says a migration is applied but Step 0.C shows the schema doesn't match.
- Step 0.E migration fails — transaction rolls back; halt and report; do NOT retry blindly.
- A migration creates a table whose name was in WS-0's kill list (conflict).
- Step 0.F shows any of the 6 DEFERRED tables still DROPPED after apply.
- More than 3 attempts on any single migration.

Begin with Step 0.A.
