// @vitest-environment node
/**
 * Packet A2 ("Always record why it failed") — LIVE-DB counterpart.
 *
 * Before this packet, 301 of 2,271 (13.25%) build_run_assets rows in a failed
 * state ('error'/'aborted') carried NO error text at all — 295 of those 301
 * traced to exactly one code path (the watchdog's undispatched-run reaper),
 * whose message was already computed one statement earlier and simply never
 * passed into the companion build_run_assets UPDATE. Full measurement:
 * 00_ARCHITECTURE/briefs/nirmana/engine/measurements/A2_before_20260926T120820Z.json
 *
 * This suite drives the REAL route handler (POST /api/cockpit/watchdog) with its
 * REAL SQL against a REAL (throwaway) Postgres, seeding one failure at each of
 * the three watchdog call sites this packet fixed, plus the M-5 correction:
 *
 *   1. The orphan-run reaper (running > 30 min, no heartbeat) — used to write
 *      build_runs.last_error = NULL and never touch build_run_assets at all.
 *   2. The stuck-asset reaper (asset_throughput 'building' > 15 min, no data) —
 *      used to write asset_throughput.last_error but never touch build_run_assets.
 *   3. The undispatched-run reaper (planned > 10 min, never dispatched) — THE
 *      dominant defect, 295 of 301 records. build_runs.last_error was written
 *      unconditionally; the paired build_run_assets abort carried no error clause.
 *
 * CORRECTION (post independent gate review,
 * 00_ARCHITECTURE/briefs/nirmana/engine/reviews/A2_review_20260926T123936Z.md §C1/§C2):
 * this packet originally also "fixed" a fourth site — the "M-5" backstop, whose
 * WHERE clause required build_run_assets.state = 'running' (a value the column's
 * CHECK constraint does not permit, so the statement was dead code that could
 * never match a row). Correcting that predicate to 'building' resurrected logic
 * whose only time predicate was the age of the RUN, not the asset — it would have
 * stamped "writer never reported back" onto any currently-building asset under a
 * run older than 30 minutes, even while that asset's own heartbeat was perfectly
 * healthy. M-5 was therefore DELETED outright rather than repaired (site 2 above
 * already covers its genuine cohort with a real per-asset staleness gate). What
 * was "site 3 (M-5 backstop)" below is now a regression test proving that exact
 * healthy-under-an-old-run scenario stays untouched, and the negative test grew a
 * companion case for the same reason (see below).
 *
 * Each test below is written to FAIL against the pre-fix code (verified by hand
 * against the pre-fix route: sites 1/2/3 left build_run_assets.error NULL; the
 * former "site 3 (M-5)" test below is inverted from the pre-correction packet,
 * where it asserted the false stamp as correct).
 *
 * Requires a THROWAWAY database — same harness pattern as
 * tests/integration/watchdog_substep_lit_guard.db.test.ts, but its OWN disposable
 * database (`watchdog_a2_test`, not `watchdog_lit_test`): both files DROP/CREATE
 * the same table set in their own beforeAll/afterAll, so running both against one
 * physical database in the same vitest invocation races (parallel worker
 * processes stomping each other's schema mid-run) — that is a pre-existing
 * constraint of this one-throwaway-db-per-suite pattern, not something this
 * packet introduces. Run each DB-integration file separately, exactly as their
 * docstrings already prescribe (`npx vitest run <this one file>`).
 *
 *   createdb -h 127.0.0.1 -p 55432 -U postgres watchdog_a2_test
 *   WATCHDOG_A2_TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:55432/watchdog_a2_test \
 *     npx vitest run tests/integration/watchdog_failure_attribution.db.test.ts
 *
 * Skipped unless WATCHDOG_A2_TEST_DATABASE_URL is set.
 */
import { describe, it, expect, beforeAll, afterAll, beforeEach, vi } from 'vitest'
import { Pool } from 'pg'

import {
  ORPHAN_RUN_MESSAGE,
  STUCK_ASSET_MESSAGE,
  UNDISPATCHED_RUN_MESSAGE,
} from '@/app/api/cockpit/watchdog/route'

vi.mock('@/lib/auth/oidc', () => ({
  verifyOidcToken: vi.fn().mockResolvedValue({
    email: 'amjis-scheduler@madhav-astrology.iam.gserviceaccount.com',
    sub: 'watchdog-a2-test',
  }),
}))

const TEST_DB_URL = process.env.WATCHDOG_A2_TEST_DATABASE_URL
const CHART_A = '00000000-0000-4000-8000-0000000000a1'
const CHART_B = '00000000-0000-4000-8000-0000000000a2'
const CHART_C = '00000000-0000-4000-8000-0000000000a3'
const CHART_D = '00000000-0000-4000-8000-0000000000a4'

let pool: Pool

async function runWatchdog(): Promise<Record<string, number>> {
  const { POST } = await import('@/app/api/cockpit/watchdog/route')
  const res = await POST(
    new Request('http://localhost/api/cockpit/watchdog', {
      method: 'POST',
      headers: { Authorization: 'Bearer watchdog-a2-test-token' },
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
    }) as any
  )
  const body = await res.json()
  expect(res.status, `watchdog returned ${res.status}: ${JSON.stringify(body)}`).toBe(200)
  return body
}

describe.skipIf(!TEST_DB_URL)('watchdog — A2 failure-attribution fixes (live DB)', () => {
  beforeAll(async () => {
    if (!/watchdog_a2_test/.test(TEST_DB_URL!)) {
      throw new Error(
        'WATCHDOG_A2_TEST_DATABASE_URL must point at a disposable database named ' +
          '`watchdog_a2_test`. This suite creates and drops schema objects and ' +
          'must never run against production.'
      )
    }
    process.env.DATABASE_URL = TEST_DB_URL
    process.env.PUBSUB_DISABLED = '1'
    delete process.env.GOOGLE_CLOUD_PROJECT

    pool = new Pool({ connectionString: TEST_DB_URL })

    // Same minimal faithful schema as watchdog_substep_lit_guard.db.test.ts, with
    // the real build_run_assets_state_check CHECK constraint (production has it;
    // it is the load-bearing fact behind the M-5 dead-code finding).
    //
    // build_runs.chart_id is declared NOT NULL below, matching production
    // (0 of 769 rows NULL, re-checked read-only against prod structure). This
    // is the fact the stuck-asset fix's build_runs join actually relies on to
    // stay total and misattribution-free — NOT the
    // build_runs_one_active_per_chart_idx UNIQUE index alone. That index is a
    // PLAIN unique index (`ON build_runs (chart_id) WHERE state IN ('planned',
    // 'running', 'paused')`), so NULL chart_id values would be mutually
    // distinct under it and the join could fan out across several concurrently
    // active runs; it is chart_id's NOT NULL constraint, combined with the
    // index, that guarantees at most one 'running' run per chart and lets
    // `br.chart_id IS NOT DISTINCT FROM s.chart_id` resolve to exactly one row.
    // A nullable chart_id here would make this test bed laxer than production
    // in exactly the dimension that join's safety argument rests on
    // (A2_review_20260926T123936Z.md §C4).
    await pool.query(`
      DROP TABLE IF EXISTS build_run_assets, build_runs, build_substep_progress,
                           asset_throughput, asset_registry, _t_data CASCADE;

      CREATE TABLE asset_registry (
        asset_id     text PRIMARY KEY,
        count_sql    text,
        target_floor int,
        has_substeps boolean
      );

      CREATE TABLE asset_throughput (
        chart_id      uuid,
        asset_id      text NOT NULL REFERENCES asset_registry(asset_id),
        state         text NOT NULL DEFAULT 'dormant',
        last_built_at timestamptz,
        rows_written  int,
        last_error    text,
        CONSTRAINT asset_throughput_state_check
          CHECK (state = ANY (ARRAY['dormant'::text, 'building'::text, 'lit'::text,
                                    'stale'::text, 'error'::text, 'incomplete'::text]))
      );
      CREATE UNIQUE INDEX ON asset_throughput (COALESCE(chart_id, '00000000-0000-0000-0000-000000000000'::uuid), asset_id);

      CREATE TABLE build_runs (
        id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        chart_id   uuid NOT NULL,
        state      text,
        started_at timestamptz,
        ended_at   timestamptz,
        created_at timestamptz DEFAULT NOW(),
        last_error text
      );
      CREATE UNIQUE INDEX build_runs_one_active_per_chart_idx ON build_runs (chart_id)
        WHERE state = ANY (ARRAY['planned', 'running', 'paused']);

      CREATE TABLE build_run_assets (
        run_id   uuid REFERENCES build_runs(id) ON DELETE CASCADE,
        asset_id text,
        position int NOT NULL DEFAULT 0,
        state    text NOT NULL DEFAULT 'queued',
        started_at timestamptz,
        ended_at timestamptz,
        error    text,
        PRIMARY KEY (run_id, asset_id),
        CONSTRAINT build_run_assets_state_check
          CHECK (state = ANY (ARRAY['queued'::text, 'building'::text, 'complete'::text,
                                    'skipped'::text, 'error'::text, 'aborted'::text]))
      );

      CREATE TABLE build_substep_progress (
        chart_id          uuid NOT NULL,
        asset_id          text NOT NULL,
        substep_key       text NOT NULL,
        build_fingerprint text NOT NULL,
        rows_written      integer NOT NULL DEFAULT 0,
        completed_at      timestamptz NOT NULL DEFAULT now(),
        PRIMARY KEY (chart_id, asset_id, substep_key)
      );

      CREATE TABLE _t_data (chart_id uuid, asset_id text, n int);
    `)

    await pool.query(
      `INSERT INTO asset_registry (asset_id, has_substeps) VALUES ('_t_asset', false)`
    )
  })

  afterAll(async () => {
    if (!pool) return
    await pool.query(
      `DROP TABLE IF EXISTS build_run_assets, build_runs, build_substep_progress,
                            asset_throughput, asset_registry, _t_data CASCADE`
    )
    await pool.end()
  })

  beforeEach(async () => {
    await pool.query('TRUNCATE build_run_assets, build_runs, asset_throughput, build_substep_progress')
  })

  it('site 1 (orphan-run reaper): writes non-empty text to BOTH build_runs.last_error and the run\'s build_run_assets rows', async () => {
    const run = await pool.query<{ id: string }>(
      `INSERT INTO build_runs (chart_id, state, started_at, created_at)
       VALUES ($1, 'running', NOW() - INTERVAL '40 minutes', NOW() - INTERVAL '40 minutes')
       RETURNING id`,
      [CHART_A]
    )
    const runId = run.rows[0]!.id
    // One asset never got past 'queued', one was mid-flight ('building') when the
    // watchdog judged the whole run dead — both must come out with attributable text.
    await pool.query(
      `INSERT INTO build_run_assets (run_id, asset_id, position, state) VALUES
         ($1, '_t_asset', 0, 'queued')`,
      [runId]
    )
    await pool.query(
      `INSERT INTO build_run_assets (run_id, asset_id, position, state) VALUES
         ($1, '_t_asset_b', 1, 'building')`,
      [runId]
    )
    // No asset_throughput / build_substep_progress heartbeat at all -> genuinely orphaned.

    const body = await runWatchdog()
    expect(body.orphan_runs_failed).toBe(1)

    const runRow = await pool.query<{ state: string; last_error: string | null }>(
      'SELECT state, last_error FROM build_runs WHERE id = $1', [runId]
    )
    expect(runRow.rows[0]!.state).toBe('failed')
    expect(runRow.rows[0]!.last_error).toBe(ORPHAN_RUN_MESSAGE)
    expect(runRow.rows[0]!.last_error).not.toBeNull()
    expect(runRow.rows[0]!.last_error!.length).toBeGreaterThan(0)

    const bra = await pool.query<{ asset_id: string; state: string; error: string | null }>(
      'SELECT asset_id, state, error FROM build_run_assets WHERE run_id = $1 ORDER BY position', [runId]
    )
    expect(bra.rows[0]).toMatchObject({ asset_id: '_t_asset', state: 'aborted', error: ORPHAN_RUN_MESSAGE })
    expect(bra.rows[1]).toMatchObject({ asset_id: '_t_asset_b', state: 'error', error: ORPHAN_RUN_MESSAGE })
    // Neither row is the empty-error defect this packet closes.
    for (const row of bra.rows) {
      expect(row.error, `row ${row.asset_id} has empty error text`).not.toBeNull()
      expect(row.error!.trim().length).toBeGreaterThan(0)
    }
  })

  it('site 2 (stuck-asset reaper): asset_throughput AND build_run_assets both get the same attributable text', async () => {
    const run = await pool.query<{ id: string }>(
      `INSERT INTO build_runs (chart_id, state, started_at, created_at)
       VALUES ($1, 'running', NOW() - INTERVAL '5 minutes', NOW() - INTERVAL '5 minutes')
       RETURNING id`,
      [CHART_B]
    )
    const runId = run.rows[0]!.id
    await pool.query(
      `INSERT INTO build_run_assets (run_id, asset_id, position, state) VALUES ($1, '_t_asset', 0, 'building')`,
      [runId]
    )
    await pool.query(
      `INSERT INTO asset_throughput (chart_id, asset_id, state, last_built_at, rows_written)
       VALUES ($1, '_t_asset', 'building', NOW() - INTERVAL '20 minutes', 0)`,
      [CHART_B]
    )
    // No count_sql on _t_asset's registry row (NULL) -> presence probe finds
    // nothing -> classifyStuckCandidate returns 'error', not 'rescue-lit'.

    const body = await runWatchdog()
    expect(body.stuck_assets_failed).toBe(1)

    const at = await pool.query<{ state: string; last_error: string | null }>(
      'SELECT state, last_error FROM asset_throughput WHERE chart_id = $1 AND asset_id = $2',
      [CHART_B, '_t_asset']
    )
    expect(at.rows[0]).toMatchObject({ state: 'error', last_error: STUCK_ASSET_MESSAGE })

    const bra = await pool.query<{ state: string; error: string | null }>(
      'SELECT state, error FROM build_run_assets WHERE run_id = $1 AND asset_id = $2', [runId, '_t_asset']
    )
    // This is the actual defect: before the fix, this row stayed 'building' with
    // error=NULL forever, even though asset_throughput already knew why.
    expect(bra.rows[0]).toMatchObject({ state: 'error', error: STUCK_ASSET_MESSAGE })
    expect(bra.rows[0]!.error).not.toBeNull()
  })

  it('former "site 3 / M-5" scenario: a healthy in-flight asset under a 30+-minute-old run is NEVER stamped, now that M-5 is deleted', async () => {
    // This is the exact case the independent gate review (A2_review_20260926T123936Z.md
    // §C1/§C2) found the original M-5 "fix" got wrong: it resurrected a predicate
    // whose only time gate was the age of the RUN, not the asset, so it stamped
    // "writer never reported back" onto a currently-building asset whose own
    // heartbeat was completely healthy. This test used to assert that false
    // stamp as CORRECT behaviour; it is now inverted to assert the honest
    // outcome — a healthy row must come out untouched.
    //
    // A build_run_assets row left 'building' with error IS NULL, under a run that
    // has been running 30+ minutes, but WITHOUT a matching asset_throughput row
    // stale enough to trip the stuck-asset reaper (site 2) — isolates exactly the
    // scenario M-5 used to (wrongly) fire on.
    const run = await pool.query<{ id: string }>(
      `INSERT INTO build_runs (chart_id, state, started_at, created_at)
       VALUES ($1, 'running', NOW() - INTERVAL '35 minutes', NOW() - INTERVAL '35 minutes')
       RETURNING id`,
      [CHART_C]
    )
    const runId = run.rows[0]!.id
    await pool.query(
      `INSERT INTO build_run_assets (run_id, asset_id, position, state) VALUES ($1, '_t_asset', 0, 'building')`,
      [runId]
    )
    // A fresh heartbeat keeps this OUT of the site-2 stuck-asset reaper entirely,
    // and also keeps the run itself out of the site-1 orphan-run reaper. With
    // M-5 gone, nothing in the route should touch this row at all.
    await pool.query(
      `INSERT INTO asset_throughput (chart_id, asset_id, state, last_built_at, rows_written)
       VALUES ($1, '_t_asset', 'building', NOW() - INTERVAL '1 minute', 0)`,
      [CHART_C]
    )

    const body = await runWatchdog()
    expect(body.stuck_assets_failed).toBe(0)

    const bra = await pool.query<{ state: string; error: string | null }>(
      'SELECT state, error FROM build_run_assets WHERE run_id = $1 AND asset_id = $2', [runId, '_t_asset']
    )
    // Honest outcome: a healthy, actively-heartbeating asset is left completely
    // alone, no matter how old the run around it is.
    expect(bra.rows[0]!.state).toBe('building')
    expect(bra.rows[0]!.error).toBeNull()

    const at = await pool.query<{ state: string; last_error: string | null }>(
      'SELECT state, last_error FROM asset_throughput WHERE chart_id = $1 AND asset_id = $2',
      [CHART_C, '_t_asset']
    )
    expect(at.rows[0]!.state).toBe('building')
    expect(at.rows[0]!.last_error).toBeNull()
  })

  it('site 4 (undispatched-run reaper — the dominant defect, 295/301): propagates the SAME text to build_run_assets', async () => {
    const run = await pool.query<{ id: string }>(
      `INSERT INTO build_runs (chart_id, state, started_at, created_at)
       VALUES ($1, 'planned', NULL, NOW() - INTERVAL '15 minutes')
       RETURNING id`,
      [CHART_D]
    )
    const runId = run.rows[0]!.id
    await pool.query(
      `INSERT INTO build_run_assets (run_id, asset_id, position, state) VALUES ($1, '_t_asset', 0, 'queued')`,
      [runId]
    )

    const body = await runWatchdog()
    expect(body.undispatched_runs_failed).toBe(1)

    const runRow = await pool.query<{ state: string; last_error: string | null }>(
      'SELECT state, last_error FROM build_runs WHERE id = $1', [runId]
    )
    expect(runRow.rows[0]).toMatchObject({ state: 'failed', last_error: UNDISPATCHED_RUN_MESSAGE })

    const bra = await pool.query<{ state: string; error: string | null }>(
      'SELECT state, error FROM build_run_assets WHERE run_id = $1 AND asset_id = $2', [runId, '_t_asset']
    )
    // THE fix: pre-fix, this row was 'aborted' with error IS NULL.
    expect(bra.rows[0]).toMatchObject({ state: 'aborted', error: UNDISPATCHED_RUN_MESSAGE })
    expect(bra.rows[0]!.error).not.toBeNull()
  })

  it('the path that still correctly writes nothing: an active, healthy run is left completely untouched', async () => {
    // §N.8 requirement: a test that only ever sees populated text proves nothing.
    // This pins the negative case — a run with a fresh heartbeat and a queued
    // asset must NOT be touched by any of the four reapers.
    const run = await pool.query<{ id: string }>(
      `INSERT INTO build_runs (chart_id, state, started_at, created_at)
       VALUES ($1, 'running', NOW() - INTERVAL '2 minutes', NOW() - INTERVAL '2 minutes')
       RETURNING id`,
      [CHART_A]
    )
    const runId = run.rows[0]!.id
    await pool.query(
      `INSERT INTO build_run_assets (run_id, asset_id, position, state) VALUES ($1, '_t_asset', 0, 'queued')`,
      [runId]
    )
    await pool.query(
      `INSERT INTO asset_throughput (chart_id, asset_id, state, last_built_at, rows_written)
       VALUES ($1, '_t_asset', 'building', NOW(), 0)`,
      [CHART_A]
    )

    const body = await runWatchdog()
    expect(body.orphan_runs_failed).toBe(0)
    expect(body.undispatched_runs_failed).toBe(0)
    expect(body.stuck_assets_failed).toBe(0)

    const runRow = await pool.query<{ state: string; last_error: string | null }>(
      'SELECT state, last_error FROM build_runs WHERE id = $1', [runId]
    )
    expect(runRow.rows[0]).toMatchObject({ state: 'running', last_error: null })

    const bra = await pool.query<{ state: string; error: string | null }>(
      'SELECT state, error FROM build_run_assets WHERE run_id = $1', [runId]
    )
    expect(bra.rows[0]).toMatchObject({ state: 'queued', error: null })
  })

  it('§N.8 negative test, extended (A2_review_20260926T123936Z.md §C2): a healthy run OLDER than 30 minutes with a currently-building asset comes out of a tick with error IS NULL', async () => {
    // This is the specific hole the original M-5 "fix" lived in and the case the
    // §N.8 negative test above could NOT have caught, because it only ever
    // exercised a 2-minute-old run. A late-wave asset in a long, healthy, still-
    // legitimately-running build (any full rebuild routinely exceeds 30 minutes)
    // must not be stamped just because the RUN is old — only actual asset-level
    // staleness (site 2, above) may ever set this text. If anyone reintroduces a
    // run-age-only stamp (the exact shape M-5 was), this test fails.
    const run = await pool.query<{ id: string }>(
      `INSERT INTO build_runs (chart_id, state, started_at, created_at)
       VALUES ($1, 'running', NOW() - INTERVAL '40 minutes', NOW() - INTERVAL '40 minutes')
       RETURNING id`,
      [CHART_A]
    )
    const runId = run.rows[0]!.id
    await pool.query(
      `INSERT INTO build_run_assets (run_id, asset_id, position, state) VALUES ($1, '_t_asset', 0, 'building')`,
      [runId]
    )
    // Fresh heartbeat: keeps this asset out of site 2 (stuck-asset reaper) and
    // the run out of site 1 (orphan-run reaper) — the only two mechanisms that
    // may legitimately write this text, and neither should fire here.
    await pool.query(
      `INSERT INTO asset_throughput (chart_id, asset_id, state, last_built_at, rows_written)
       VALUES ($1, '_t_asset', 'building', NOW() - INTERVAL '30 seconds', 0)`,
      [CHART_A]
    )

    const body = await runWatchdog()
    expect(body.orphan_runs_failed).toBe(0)
    expect(body.stuck_assets_failed).toBe(0)

    const runRow = await pool.query<{ state: string; last_error: string | null }>(
      'SELECT state, last_error FROM build_runs WHERE id = $1', [runId]
    )
    expect(runRow.rows[0]).toMatchObject({ state: 'running', last_error: null })

    const bra = await pool.query<{ state: string; error: string | null }>(
      'SELECT state, error FROM build_run_assets WHERE run_id = $1 AND asset_id = $2', [runId, '_t_asset']
    )
    expect(bra.rows[0]).toMatchObject({ state: 'building', error: null })
  })

  it('is idempotent — a second tick after a fix does not re-touch already-terminal rows or duplicate side effects', async () => {
    const run = await pool.query<{ id: string }>(
      `INSERT INTO build_runs (chart_id, state, started_at, created_at)
       VALUES ($1, 'planned', NULL, NOW() - INTERVAL '15 minutes')
       RETURNING id`,
      [CHART_D]
    )
    const runId = run.rows[0]!.id
    await pool.query(
      `INSERT INTO build_run_assets (run_id, asset_id, position, state) VALUES ($1, '_t_asset', 0, 'queued')`,
      [runId]
    )

    const first = await runWatchdog()
    expect(first.undispatched_runs_failed).toBe(1)

    const second = await runWatchdog()
    expect(second.undispatched_runs_failed).toBe(0)

    const bra = await pool.query<{ state: string; error: string | null }>(
      'SELECT state, error FROM build_run_assets WHERE run_id = $1 AND asset_id = $2', [runId, '_t_asset']
    )
    expect(bra.rows[0]).toMatchObject({ state: 'aborted', error: UNDISPATCHED_RUN_MESSAGE })
  })
})
