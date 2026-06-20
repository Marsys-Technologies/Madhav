---
brief_id: CHART_DEDUPE_v1_0
status: ACTIVE
authored_by: Cowork (planning)
executor: Claude Code in Google Antigravity IDE
authored_at: 2026-05-31
model_directive: Use Gemini Pro / DeepSeek. Anthropic banned per native standing order.
worktree: /Users/Dev/Vibe-Coding/Apps/Madhav (main checkout — no parallel streams needed)
branch: fix/chart-dedupe
estimated_loc: ~250 LOC across 5 files
---

# CLAUDECODE_BRIEF — Chart Duplicate Remediation

## Context (read first)

The dashboard at https://storage.googleapis.com/marsys-tracker-public/data_progress.html
shows many duplicate "Abhisek Mohanty" charts. Root cause investigation (Cowork, 2026-05-31):

1. `platform/src/app/api/clients/create/route.ts` validates input + rate-limits to 5/hr,
   but has **no uniqueness check** on `(owner_id, name, birth_date, birth_time, lat, lng)`.
   Every form submit without an `X-Idempotency-Key` header → fresh INSERT → new UUID.
   The portal entry form does NOT send that header. Five distinct submissions in one
   hour produce five duplicate rows before the rate limit even bites.

2. `platform/scripts/seed-abhisek.ts` dedupes only on `(client_id, name)`. Multiple
   agent worktrees with potentially-different `SUPER_ADMIN_EMAIL` env values would
   each produce their own `client_id` and bypass the dedupe.

3. No DB-level UNIQUE constraint exists on the natural key.

The native chart UUID we want to preserve as canonical for Abhisek Mohanty is:
`362f9f17-95a5-490b-a5a7-027d3e0efda0`

## Scope

`may_touch`:
- `platform/src/app/api/clients/create/route.ts`
- `platform/supabase/migrations/157_charts_natural_key_uniq.sql` (NEW — 154/155/156 consumed by UX-overhaul PR #172)
- `platform/scripts/dedupe_charts.ts` (NEW)
- `platform/scripts/_archived/seed-abhisek.ts` (MOVE from `platform/scripts/seed-abhisek.ts`)
- `platform/src/app/api/clients/create/__tests__/route.test.ts` (extend; create if absent)

`must_not_touch`:
- Anything under `00_ARCHITECTURE/`
- Anything under `01_FACTS_LAYER/` or `025_HOLISTIC_SYNTHESIS/`
- Any other API route
- Any `chart_facts`, `build_events`, or asset writer code
- Any worktree copy of `seed-abhisek.ts` under `/Users/Dev/Vibe-Coding/Apps/Madhav/agent-*` (out of scope; they're stale worktrees)

## Pre-flight

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git fetch origin
git checkout main
git pull origin main
git checkout -b fix/chart-dedupe
```

## Task 1 — API pre-INSERT dedupe (route.ts)

In `platform/src/app/api/clients/create/route.ts`, between the **rate-limit block**
(ends ~line 276) and the **idempotency-key check** (begins ~line 279), add:

```ts
// ── Natural-key dedupe (always-on; X-Idempotency-Key remains optional override) ──
const naturalKeyResult = await query<{ chart_id: string; client_id: string }>(
  `SELECT chart_id, client_id
     FROM charts
    WHERE owner_id = $1
      AND lower(trim(name)) = lower(trim($2))
      AND birth_date = $3
      AND birth_time = $4
      AND ROUND(birth_lat::numeric, 4) = ROUND($5::numeric, 4)
      AND ROUND(birth_lng::numeric, 4) = ROUND($6::numeric, 4)
    ORDER BY created_at ASC
    LIMIT 1`,
  [user.uid, name, birth_date, birth_time, lat, lon],
)
if (naturalKeyResult.rows[0]) {
  const row = naturalKeyResult.rows[0]
  return NextResponse.json({
    chart_id: row.chart_id,
    client_id: row.client_id ?? null,
    redirect_url: `/clients/${row.chart_id}/build`,
    ayanamshas,
    idempotent: true,
    dedupe_reason: 'natural_key_match',
  })
}
```

Acceptance: identical form submission within the rate window returns the existing
`chart_id` with HTTP 200 + `idempotent: true`. No new row created.

## Task 2 — DB UNIQUE constraint (migration)

Create `platform/supabase/migrations/157_charts_natural_key_uniq.sql`:

```sql
-- 157_charts_natural_key_uniq.sql
-- Enforce natural-key uniqueness on charts: same owner cannot create two charts
-- with the same name + birth_date + birth_time + lat/lng (4dp ~= 11m precision).
-- Run AFTER dedupe_charts.ts has cleaned existing duplicates, or the index
-- creation will fail with a uniqueness violation.

BEGIN;

-- Defensive: confirm no duplicates remain before adding the constraint.
DO $$
DECLARE dup_count int;
BEGIN
  SELECT COUNT(*) INTO dup_count
  FROM (
    SELECT 1
    FROM charts
    GROUP BY owner_id, lower(trim(name)), birth_date, birth_time,
             ROUND(birth_lat::numeric, 4), ROUND(birth_lng::numeric, 4)
    HAVING COUNT(*) > 1
  ) d;
  IF dup_count > 0 THEN
    RAISE EXCEPTION 'Cannot add unique index: % duplicate natural-key groups remain. Run dedupe_charts.ts first.', dup_count;
  END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS charts_natural_key_uniq
ON charts (
  owner_id,
  lower(trim(name)),
  birth_date,
  birth_time,
  ROUND(birth_lat::numeric, 4),
  ROUND(birth_lng::numeric, 4)
);

COMMENT ON INDEX charts_natural_key_uniq IS
  'Prevents duplicate chart creation per owner. Lat/lng rounded to 4dp (~11m) to absorb float noise.';

COMMIT;
```

Migration is **not auto-applied**. Operator will run it after Task 3 cleanup.

## Task 3 — Dedupe script with dry-run default

Create `platform/scripts/dedupe_charts.ts`:

Requirements:
- Default mode is **dry-run** (prints planned actions, makes zero writes).
- `--apply` flag required to actually mutate.
- For each `(owner_id, lower(trim(name)), birth_date, birth_time, round(lat,4), round(lng,4))`
  group with COUNT > 1:
  - Canonical = oldest `created_at`. **Exception:** if any row in the group has
    `chart_id = '362f9f17-95a5-490b-a5a7-027d3e0efda0'`, that one is canonical regardless of age.
  - Re-point FK references in ALL dependent tables (enumerate by querying
    `pg_constraint` for `referenced_table = 'charts'` and `referenced_column = 'chart_id'`
    — print the list before mutating; do not hardcode).
  - DELETE the duplicate rows from `charts`.
- Wrap mutations in a single transaction per natural-key group; rollback on error in
  that group and continue with the next group.
- Print a summary: groups inspected, groups with dupes, rows re-pointed per dependent table,
  rows deleted, errors.
- Connect via the same `DATABASE_URL` pattern that `seed-abhisek.ts` uses
  (Cloud SQL Auth Proxy on :5433).

Run signature:
```bash
cd platform
npx tsx scripts/dedupe_charts.ts            # dry-run
npx tsx scripts/dedupe_charts.ts --apply    # commits
```

## Task 4 — Retire seed-abhisek.ts

```bash
mkdir -p platform/scripts/_archived
git mv platform/scripts/seed-abhisek.ts platform/scripts/_archived/seed-abhisek.ts
```

Add a one-line header comment to the moved file:
```ts
// ARCHIVED 2026-05-31 — duplicate-chart hazard. Use POST /api/clients/create
// (form-driven) for chart creation. See 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_CHART_DEDUPE_v1_0.md.
```

Do **NOT** modify the worktree copies under `/Users/Dev/Vibe-Coding/Apps/Madhav/agent-*/`.
Those are stale worktrees; they'll go when the worktree is cleaned up.

## Task 5 — Tests

Extend `platform/src/app/api/clients/create/__tests__/route.test.ts` (create
the file if it doesn't exist; mock `query` from `@/lib/db/client` and
`getServerUser` from `@/lib/firebase/server`):

1. **Test: natural-key match returns existing chart, no INSERT.**
   Mock `query` so the natural-key SELECT returns one row. Assert response is
   `{ chart_id, idempotent: true, dedupe_reason: 'natural_key_match' }` and
   that NO INSERT query was executed.

2. **Test: trailing whitespace and case variation still dedupe.**
   Submit `name = '  abhisek mohanty  '`; mock the natural-key SELECT to return
   a row matching `'Abhisek Mohanty'`. Assert dedupe response.

3. **Test: different birth_time produces fresh insert.** Mock natural-key SELECT
   returns empty; assert INSERT runs.

4. **Test: lat/lng float noise within 4dp dedupes.** Submit `lat = 20.29614`
   when existing is `20.2961`. Assert dedupe response.

Run:
```bash
cd platform
npm test -- route.test.ts
```

## Task 6 — Commit + push

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git add platform/src/app/api/clients/create/route.ts
git add platform/supabase/migrations/154_charts_natural_key_uniq.sql
git add platform/scripts/dedupe_charts.ts
git add platform/scripts/_archived/seed-abhisek.ts
git add platform/src/app/api/clients/create/__tests__/route.test.ts
git rm platform/scripts/seed-abhisek.ts 2>/dev/null || true

git status                                  # human-read before commit

git commit -m "fix(api): natural-key dedupe + migration 154 + dedupe script

- /api/clients/create now does pre-INSERT lookup on (owner_id, name, birth_date,
  birth_time, round(lat,4), round(lng,4)); returns existing chart on match.
- Migration 157 adds CREATE UNIQUE INDEX after pre-flight duplicate check.
- platform/scripts/dedupe_charts.ts walks dupes, re-points FKs, deletes.
  Default dry-run; --apply commits. Canonical override for native chart UUID
  362f9f17-95a5-490b-a5a7-027d3e0efda0.
- seed-abhisek.ts archived (duplicate-chart hazard).

Brief: 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_CHART_DEDUPE_v1_0.md
Native sign-off: PENDING (do not merge to main without explicit approval)."

git push -u origin fix/chart-dedupe
```

## Hard gate — DO NOT do these things

- Do NOT apply the migration (operator does it manually after dedupe).
- Do NOT run `dedupe_charts.ts --apply` (operator does it manually after dry-run review).
- Do NOT merge `fix/chart-dedupe` into main (human-gated per project policy).
- Do NOT modify any file outside the `may_touch` list above.
- Do NOT use Anthropic models. Use Gemini Pro or DeepSeek.

## Acceptance criteria (executor self-verifies before "done")

- [ ] `npm run build` succeeds in `platform/`.
- [ ] `npm test -- route.test.ts` passes; the 4 new tests all green.
- [ ] `grep -r "from '.*scripts/seed-abhisek'" platform/` returns zero hits
      (no live imports of the archived script).
- [ ] Migration 157 file parses (run `psql -f` against an empty test DB if
      sidecar available; otherwise visual review).
- [ ] `dedupe_charts.ts` runs in dry-run mode against current DB without error
      (operator-side; if no DB proxy, skip and document in commit body).
- [ ] PR description includes the dry-run output summary if step above ran.

## Operator post-merge steps (Cowork records, executor does NOT run)

1. `npx tsx platform/scripts/dedupe_charts.ts` — review dry-run output.
2. `npx tsx platform/scripts/dedupe_charts.ts --apply` — execute cleanup.
3. Apply migration 157 to production DB (via existing migration runner).
4. Verify dashboard count of "Abhisek Mohanty" charts equals 1.
5. Smoke-test: submit identical form twice; second submit returns same chart_id.

---

End of brief.
