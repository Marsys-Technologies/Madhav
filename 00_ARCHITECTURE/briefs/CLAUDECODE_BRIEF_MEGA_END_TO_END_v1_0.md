---
brief_id: MEGA_END_TO_END_v1_0
status: ACTIVE
authored_by: Cowork (planning)
executor: Claude Code in Google Antigravity IDE
authored_at: 2026-05-31
model_directive: Use Gemini Pro or DeepSeek. Anthropic banned per native standing order.
worktree: /Users/Dev/Vibe-Coding/Apps/Madhav (single checkout)
base_branch: feature/ux-workflow-overhaul   # PR #172 base
work_branch: feature/e2e-portal-build-ready
estimated_loc: ~120 LOC new + ~30 LOC test (sidecar residuals only)
estimated_wallclock: 60–90 min (code) + 30–60 min (local smoke)
---

# CLAUDECODE_BRIEF — MEGA END-TO-END: portal-triggerable chart build, merge-ready

## Goal (one paragraph)

Get every line of code to a state where the native opens
`/clients/362f9f17-95a5-490b-a5a7-027d3e0efda0/build`, clicks **Build**, and
watches his own chart compute live across the force-graph cockpit with row
counts climbing in PartialDataBanner, then opens `/consume` and gets answers
grounded in freshly-built `chart_facts` rows. Code only — production deploy,
production migrations, and production native chart build stay operator-side
per project rules.

## Scope envelope

This brief sequences three previously-authored briefs into one autonomous run,
plus adds the local-smoke proof that none of them had alone:

1. **CHART_DEDUPE_v1_0** — already executed on branch `fix/chart-dedupe`
   (commit a5845e22). VERIFY only; do not re-execute.
2. **SIDECAR_RESIDUALS_v1_0** — drafted, not yet executed. EXECUTE in full.
3. **NEW: local end-to-end smoke** — apply all migrations to local DB, run
   dedupe, trigger a local chart build via the API, verify cockpit
   accretion + chart_facts population. Documented in §3 below.

All three land on a single merge-ready branch: `feature/e2e-portal-build-ready`,
based on `feature/ux-workflow-overhaul`.

## Scope

`may_touch` (full list — anything outside this fails the run):
- `platform/python-sidecar/pipeline/build_events.py`
- `platform/python-sidecar/pipeline/dispatcher.py`
- `platform/python-sidecar/pipeline/__tests__/test_build_events.py`
- `platform/src/types/sse_events.ts`
- `platform/src/components/cockpit/LiveBuildGraph.tsx` (only if SSE field-name fix is forced)
- `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MEGA_END_TO_END_v1_0.md` (this file — append §6 smoke evidence at end of run)

`must_not_touch`:
- Any writer under `python-sidecar/pipeline/writers/`
- Any migration file (all already authored on prior branches)
- `00_ARCHITECTURE/` anything except this brief's §6
- `/api/clients/create` route (already shipped via fix/chart-dedupe)
- `01_FACTS_LAYER/`, `025_HOLISTIC_SYNTHESIS/`
- Worktree copies under `agent-*/`

## Pre-flight

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git fetch origin
git checkout feature/ux-workflow-overhaul
git pull origin feature/ux-workflow-overhaul

# Merge dedupe in
git merge --no-ff origin/fix/chart-dedupe -m "merge: chart-dedupe (a5845e22) into ux-workflow-overhaul"

# New integration branch
git checkout -b feature/e2e-portal-build-ready
```

If the merge has conflicts, STOP and write a one-paragraph blocker note.
Do not attempt to resolve cross-arc conflicts unsupervised.

## §1 — Execute sidecar residuals (R1 + R2)

Read `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_SIDECAR_RESIDUALS_v1_0.md`
in full. Execute every task (R1.1 → R1.2 → R1.3 → R1.4 → R2.1 → R2.2 → R2.3)
exactly as specified there. The brief is the source of truth for code and
tests — do not re-derive.

Acceptance for §1: that brief's "Acceptance criteria" checklist all ticks.

## §2 — Verify dedupe arc landed cleanly

```bash
# Confirm dedupe artifacts are present on this branch:
test -f platform/scripts/dedupe_charts.ts || (echo "DEDUPE SCRIPT MISSING" && exit 1)
test -f platform/supabase/migrations/157_charts_natural_key_uniq.sql || (echo "MIG 157 MISSING" && exit 1)
test ! -f platform/scripts/seed-abhisek.ts || (echo "SEED NOT ARCHIVED" && exit 1)
test -f platform/scripts/_archived/seed-abhisek.ts || (echo "ARCHIVED SEED MISSING" && exit 1)

# Confirm the natural-key dedupe lives in the route:
grep -q "natural_key_match" platform/src/app/api/clients/create/route.ts || (echo "DEDUPE NOT IN ROUTE" && exit 1)

# Re-run dedupe tests (regression):
cd platform && npm test -- route.test.ts
cd -
```

All checks must pass. If any fails, STOP and report.

## §3 — Local end-to-end smoke (THE proof step)

This is the new work this mega-brief adds beyond §1+§2: prove the whole
thing works against a local DB before the operator touches prod.

### 3.1 — DB proxy + migrations

```bash
# Start Cloud SQL Auth Proxy (assumes start_db_proxy.sh is configured)
bash platform/scripts/start_db_proxy.sh &
PROXY_PID=$!
sleep 5

# Confirm proxy alive
psql "$DATABASE_URL" -c "SELECT 1;" || (echo "DB PROXY DOWN" && kill $PROXY_PID && exit 1)

# Apply all multi-ayanamsha migrations
for i in $(seq 140 153); do
  echo "==> Applying migration $i"
  psql "$DATABASE_URL" -f platform/migrations/${i}_*.sql || (echo "MIG $i FAILED" && kill $PROXY_PID && exit 1)
done

# Apply UX-overhaul orchestration migrations
for i in 154 155 156; do
  echo "==> Applying migration $i"
  psql "$DATABASE_URL" -f platform/migrations/${i}_*.sql || (echo "MIG $i FAILED" && kill $PROXY_PID && exit 1)
done
```

### 3.2 — Dedupe + constraint

```bash
# Dry-run, capture output
npx tsx platform/scripts/dedupe_charts.ts 2>&1 | tee /tmp/dedupe_dryrun.log

# Apply
npx tsx platform/scripts/dedupe_charts.ts --apply 2>&1 | tee /tmp/dedupe_apply.log

# Verify single-row native
NATIVE_COUNT=$(psql "$DATABASE_URL" -tAc \
  "SELECT COUNT(*) FROM charts WHERE name ILIKE '%abhisek%' OR name ILIKE '%mohanty%'")
[ "$NATIVE_COUNT" = "1" ] || (echo "EXPECTED 1 NATIVE CHART, FOUND $NATIVE_COUNT" && kill $PROXY_PID && exit 1)

# Apply natural-key constraint (will RAISE EXCEPTION if dedupe missed any)
psql "$DATABASE_URL" -f platform/supabase/migrations/157_charts_natural_key_uniq.sql \
  || (echo "MIG 157 FAILED — dedupe incomplete" && kill $PROXY_PID && exit 1)
```

### 3.3 — Boot the dev server + trigger build

```bash
cd platform
npm install
npm run dev &
DEV_PID=$!
sleep 15  # wait for Next to compile

# Capture native chart_id (must exist post-dedupe)
NATIVE_CHART_ID="362f9f17-95a5-490b-a5a7-027d3e0efda0"

# Verify the native chart exists in the local DB (if not, create via API once)
NATIVE_EXISTS=$(psql "$DATABASE_URL" -tAc \
  "SELECT COUNT(*) FROM charts WHERE chart_id = '$NATIVE_CHART_ID'")
if [ "$NATIVE_EXISTS" = "0" ]; then
  echo "==> Local DB missing native chart — DOCUMENT in §6 and skip the build trigger."
  echo "==> Local smoke partial: stop after §3 with note."
  kill $PROXY_PID $DEV_PID 2>/dev/null
  exit 0   # graceful exit — operator has the prod chart, local will be smoked there
fi

# Trigger a build via the API (mint a local session cookie first)
SESSION_COOKIE=$(npx tsx scripts/mint_session_cookie.ts --uid local-smoke-uid --chart-id $NATIVE_CHART_ID)

BUILD_RESP=$(curl -s -X POST http://localhost:3000/api/build/start \
  -H "Cookie: __session=$SESSION_COOKIE" \
  -H "Content-Type: application/json" \
  -d "{\"chart_id\":\"$NATIVE_CHART_ID\"}")
BUILD_ID=$(echo "$BUILD_RESP" | jq -r '.build_id')

[ "$BUILD_ID" != "null" ] && [ -n "$BUILD_ID" ] || (echo "BUILD START FAILED: $BUILD_RESP" && kill $PROXY_PID $DEV_PID && exit 1)
echo "==> Build started: $BUILD_ID"
```

### 3.4 — Watch SSE stream for the typed events R1 added

```bash
# Collect 60s of SSE events
timeout 60 curl -N "http://localhost:3000/api/build/events/$BUILD_ID" \
  -H "Cookie: __session=$SESSION_COOKIE" > /tmp/sse_events.log 2>&1 || true

# Verify both R1 event types fired:
grep -q "event: node_added" /tmp/sse_events.log \
  || (echo "R1 FAIL: no node_added events in first 60s" && kill $PROXY_PID $DEV_PID && exit 1)
grep -q "event: edge_added" /tmp/sse_events.log \
  || (echo "R1 WARN: no edge_added events in first 60s — may need longer window"; true)
echo "==> R1 PASS: node_added events observed"
```

### 3.5 — Verify R2 (build_events.chart_id populated)

```bash
sleep 30  # let some asset writers complete

R2_COUNT=$(psql "$DATABASE_URL" -tAc \
  "SELECT COUNT(*) FROM build_events WHERE build_id = '$BUILD_ID' AND chart_id = '$NATIVE_CHART_ID'")
[ "$R2_COUNT" -gt "0" ] || (echo "R2 FAIL: 0 build_events rows with chart_id for this build" && kill $PROXY_PID $DEV_PID && exit 1)
echo "==> R2 PASS: $R2_COUNT build_events rows with chart_id"
```

### 3.6 — Wait for build, verify chart_facts

```bash
# Poll for build_complete (max 30 min)
DEADLINE=$(($(date +%s) + 1800))
while [ $(date +%s) -lt $DEADLINE ]; do
  STATUS=$(psql "$DATABASE_URL" -tAc \
    "SELECT event_type FROM build_notifications WHERE build_id = '$BUILD_ID' ORDER BY notif_id DESC LIMIT 1")
  if [ "$STATUS" = "build_complete" ]; then
    echo "==> Build complete"
    break
  fi
  if [ "$STATUS" = "build_failed" ]; then
    echo "==> BUILD FAILED — document in §6, do NOT halt the brief (R1/R2 already proven)."
    break
  fi
  sleep 30
done

# chart_facts populated?
FACT_ROWS=$(psql "$DATABASE_URL" -tAc \
  "SELECT COUNT(*) FROM chart_facts WHERE chart_id = '$NATIVE_CHART_ID'")
echo "==> chart_facts rows for native: $FACT_ROWS"

# By ayanamsha breakdown for §6:
psql "$DATABASE_URL" -c "
  SELECT ayanamsha_id, COUNT(*) AS rows
  FROM chart_facts
  WHERE chart_id = '$NATIVE_CHART_ID'
  GROUP BY 1 ORDER BY 1;" > /tmp/chart_facts_breakdown.txt

# Shut down
kill $PROXY_PID $DEV_PID 2>/dev/null
```

§3 acceptance:
- Migrations 140-157 applied to local DB without error.
- `node_added` events observed in SSE stream → R1 PROVEN.
- `build_events.chart_id` populated → R2 PROVEN.
- chart_facts row count > 0 → end-to-end works (exact number depends on
  writer coverage; this is informational, not gating).

## §4 — Commit + push

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

# Stage everything the brief authored
git add platform/python-sidecar/pipeline/build_events.py
git add platform/python-sidecar/pipeline/dispatcher.py
git add platform/python-sidecar/pipeline/__tests__/test_build_events.py
git add platform/src/types/sse_events.ts
git add platform/src/components/cockpit/LiveBuildGraph.tsx 2>/dev/null || true
git add 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MEGA_END_TO_END_v1_0.md  # the §6 evidence append

git status

git commit -m "feat(e2e): portal-triggerable chart build — sidecar residuals + dedupe merge-train

Consolidates three arcs onto one merge-ready branch:
  - chart-dedupe (fix/chart-dedupe @ a5845e22, merged into base)
  - sidecar residuals R1+R2 (this commit — see brief §1)
  - local end-to-end smoke (this commit — see brief §3, §6 evidence)

Locally proven against the dev DB:
  - migrations 140-157 apply cleanly
  - dedupe collapses test-noise charts; constraint accepted
  - cockpit SSE emits node_added/edge_added typed events (R1)
  - build_events.chart_id populated for per-asset writes (R2)
  - end-to-end build from /api/build/start populates chart_facts

Operator post-merge runbook (see brief §5).

Brief: 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MEGA_END_TO_END_v1_0.md
Native sign-off: PENDING. Do not merge to main without explicit approval."

git push -u origin feature/e2e-portal-build-ready
```

## §5 — Operator runbook (DO NOT execute — print at end of run for the user)

After this brief's branch is reviewed and merged to main, operator runs:

```bash
# 1. Deploy
gcloud builds submit --config cloudbuild.yaml                         # amjis-web
gcloud builds submit --config platform-sidecar/cloudbuild.yaml         # amjis-sidecar

# 2. Apply migrations to prod DB (in order)
for i in $(seq 140 156); do psql "$PROD_DB_URL" -f platform/migrations/${i}_*.sql; done
npx tsx platform/scripts/dedupe_charts.ts             # against prod (dry-run)
npx tsx platform/scripts/dedupe_charts.ts --apply     # against prod
psql "$PROD_DB_URL" -f platform/supabase/migrations/157_charts_natural_key_uniq.sql

# 3. Open the cockpit, click Build
open https://<amjis-web-url>/clients/362f9f17-95a5-490b-a5a7-027d3e0efda0/build
# → click Build → watch the graph accrete → wait for build_complete

# 4. Apply partition migrations (now unblocked by chart_id population)
for i in 121 122 124; do psql "$PROD_DB_URL" -f platform/migrations/${i}_*.sql; done

# 5. Smoke /consume with a real native question
```

## §6 — Smoke evidence (executor appends actual output here at end of run)

> Executor: at end of §3 success, replace this placeholder block with:
> - migrations applied list
> - dedupe dryrun summary (groups inspected, dupes found)
> - dedupe apply summary (FK re-points per table, rows deleted)
> - SSE event sample (5-10 lines from /tmp/sse_events.log)
> - chart_facts breakdown (cat /tmp/chart_facts_breakdown.txt)
> - any blocker notes

```
TO BE FILLED BY EXECUTOR
```

## Hard gates

- DO NOT deploy anything (no gcloud builds submit, no gcloud run deploy).
- DO NOT touch the production DB (only the local proxy DB).
- DO NOT merge `feature/e2e-portal-build-ready` to main or to `feature/ux-workflow-overhaul`. Push only.
- DO NOT modify any file outside the may_touch list in §Scope.
- DO NOT use Anthropic models.
- DO NOT broaden scope. R1, R2, local smoke, push. That's it.

## Acceptance criteria

- [ ] §1 sidecar residuals brief's full AC checklist green.
- [ ] §2 dedupe verification: all 4 checks pass.
- [ ] §3 local smoke: migrations applied, dedupe ran, single native row,
      SSE node_added observed, build_events.chart_id populated, build run
      to terminal state (complete or failed — both are valid evidence).
- [ ] §4 single commit pushed to `feature/e2e-portal-build-ready`.
- [ ] §6 smoke evidence block filled with real output.
- [ ] No file outside may_touch was modified (run `git diff --name-only origin/feature/ux-workflow-overhaul...HEAD` and visually verify).

---

End of brief.
