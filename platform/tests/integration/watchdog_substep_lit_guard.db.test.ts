// @vitest-environment node
/**
 * SAMĀPTI B-WATCHDOG-LIT · DVA Ruling 10 · finding F3 — LIVE-DB counterpart.
 *
 * Drives the REAL route handler (POST /api/cockpit/watchdog) with its REAL SQL
 * against a REAL Postgres, so the guard is proven end-to-end and not merely at
 * the extracted-predicate level: the candidate query, the has_substeps join, the
 * build_substep_progress subquery, the 'incomplete' CHECK constraint from
 * migration 474, and the withheld-promotion UPDATE all execute for real.
 *
 * Requires a THROWAWAY database. It is skipped unless WATCHDOG_TEST_DATABASE_URL
 * is set, and it refuses to run against anything that is not obviously disposable
 * (see the guard in beforeAll) — this suite CREATEs and DROPs schema objects and
 * must never touch production. Production build state is read-only, always.
 *
 *   initdb -D /tmp/pgdata -U postgres --auth=trust
 *   pg_ctl -D /tmp/pgdata -o "-p 55432 -k '' -c listen_addresses=127.0.0.1" start
 *   createdb -h 127.0.0.1 -p 55432 -U postgres watchdog_lit_test
 *   WATCHDOG_TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:55432/watchdog_lit_test \
 *     npx vitest run tests/integration/watchdog_substep_lit_guard.db.test.ts
 */
import { describe, it, expect, beforeAll, afterAll, beforeEach } from 'vitest'
import { Pool } from 'pg'

const TEST_DB_URL = process.env.WATCHDOG_TEST_DATABASE_URL
const CHART = '00000000-0000-4000-8000-0000000000aa'

// Fixture assets. Prefixed `_t_` so they can never collide with a real asset_id.
const HEAVY_PARTIAL = '_t_heavy_partial'      // the F3 shape: 78/303 substeps in
const LIGHT_RESCUABLE = '_t_light_rescuable'  // planless, rows present
const LIGHT_NODATA = '_t_light_nodata'        // planless, no rows
const HEAVY_NODATA = '_t_heavy_nodata'        // plan-bearing, no rows
const LIGHT_FRESH = '_t_light_fresh'          // planless, heartbeat still fresh

let pool: Pool

async function stateOf(assetId: string): Promise<string> {
  const r = await pool.query<{ state: string }>(
    'SELECT state FROM asset_throughput WHERE chart_id = $1 AND asset_id = $2',
    [CHART, assetId]
  )
  return r.rows[0]!.state
}

/** Re-seed every fixture to its pre-watchdog state. */
async function seed(): Promise<void> {
  await pool.query('TRUNCATE asset_throughput, build_substep_progress, _t_data')

  // 7800 rows — what 78 committed substeps of a 303-substep plan left behind.
  await pool.query(
    `INSERT INTO _t_data (chart_id, asset_id, n)
     SELECT $1, $2, g FROM generate_series(1, 7800) g`,
    [CHART, HEAVY_PARTIAL]
  )
  await pool.query(
    `INSERT INTO _t_data (chart_id, asset_id, n)
     SELECT $1, $2, g FROM generate_series(1, 500) g`,
    [CHART, LIGHT_RESCUABLE]
  )
  await pool.query(
    `INSERT INTO _t_data (chart_id, asset_id, n)
     SELECT $1, $2, g FROM generate_series(1, 500) g`,
    [CHART, LIGHT_FRESH]
  )

  // 78 of 303 substeps committed. The plan total is NOT recorded anywhere —
  // that absence is precisely why the route cannot prove completeness.
  await pool.query(
    `INSERT INTO build_substep_progress (chart_id, asset_id, substep_key, build_fingerprint)
     SELECT $1, $2, 'substep_' || g, 'fp_test' FROM generate_series(1, 78) g`,
    [CHART, HEAVY_PARTIAL]
  )

  for (const assetId of [HEAVY_PARTIAL, LIGHT_RESCUABLE, LIGHT_NODATA, HEAVY_NODATA]) {
    await pool.query(
      `INSERT INTO asset_throughput (chart_id, asset_id, state, last_built_at, rows_written)
       VALUES ($1, $2, 'building', NOW() - INTERVAL '20 minutes', 0)`,
      [CHART, assetId]
    )
  }
  // Heartbeat still inside the 15-minute window — must be left alone entirely.
  await pool.query(
    `INSERT INTO asset_throughput (chart_id, asset_id, state, last_built_at, rows_written)
     VALUES ($1, $2, 'building', NOW() - INTERVAL '2 minutes', 0)`,
    [CHART, LIGHT_FRESH]
  )
}

async function runWatchdog(): Promise<Record<string, number>> {
  const { POST } = await import('@/app/api/cockpit/watchdog/route')
  const res = await POST(
    new Request('http://localhost/api/cockpit/watchdog', {
      method: 'POST',
      headers: { 'x-watchdog-auth': process.env.WATCHDOG_SECRET! },
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
    }) as any
  )
  const body = await res.json()
  expect(res.status, `watchdog returned ${res.status}: ${JSON.stringify(body)}`).toBe(200)
  return body
}

describe.skipIf(!TEST_DB_URL)('watchdog stuck-asset reaper — live DB (F3 guard)', () => {
  beforeAll(async () => {
    // Refuse to run anywhere that is not plainly a throwaway.
    if (!/watchdog_lit_test/.test(TEST_DB_URL!)) {
      throw new Error(
        'WATCHDOG_TEST_DATABASE_URL must point at a disposable database named ' +
          '`watchdog_lit_test`. This suite creates and drops schema objects and ' +
          'must never run against production.'
      )
    }
    process.env.DATABASE_URL = TEST_DB_URL
    process.env.WATCHDOG_SECRET = 'test-watchdog-secret'
    process.env.PUBSUB_DISABLED = '1'
    delete process.env.GOOGLE_CLOUD_PROJECT

    pool = new Pool({ connectionString: TEST_DB_URL })

    // Minimal faithful schema: exactly the columns the watchdog route touches,
    // with migration 474's real CHECK constraint (the one that makes
    // 'incomplete' a legal state) and migration 436's build_substep_progress.
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
        chart_id   uuid,
        state      text,
        started_at timestamptz,
        ended_at   timestamptz,
        created_at timestamptz DEFAULT NOW(),
        last_error text
      );

      CREATE TABLE build_run_assets (
        run_id   uuid,
        asset_id text,
        state    text,
        ended_at timestamptz,
        error    text
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

    const countSql = (id: string) =>
      `SELECT COUNT(*) AS count FROM _t_data WHERE chart_id = $1 AND asset_id = '${id}'`
    await pool.query(
      `INSERT INTO asset_registry (asset_id, count_sql, target_floor, has_substeps) VALUES
         ($1, $6,  100, true),
         ($2, $7,  100, false),
         ($3, $8,  100, false),
         ($4, $9,  100, true),
         ($5, $10, 100, false)`,
      [
        HEAVY_PARTIAL, LIGHT_RESCUABLE, LIGHT_NODATA, HEAVY_NODATA, LIGHT_FRESH,
        countSql(HEAVY_PARTIAL), countSql(LIGHT_RESCUABLE), countSql(LIGHT_NODATA),
        countSql(HEAVY_NODATA), countSql(LIGHT_FRESH),
      ]
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

  beforeEach(seed)

  it('does NOT promote a mid-plan asset to lit — the F3 defect', async () => {
    // Pre-conditions: rows present, substeps partially committed, heartbeat stale.
    // This is exactly the state that used to yield 'lit'.
    const before = await pool.query(
      `SELECT (SELECT COUNT(*)::int FROM _t_data
                WHERE chart_id = $1 AND asset_id = $2) AS rows,
              (SELECT COUNT(*)::int FROM build_substep_progress
                WHERE chart_id = $1 AND asset_id = $2) AS substeps`,
      [CHART, HEAVY_PARTIAL]
    )
    expect(before.rows[0]).toEqual({ rows: 7800, substeps: 78 })
    expect(await stateOf(HEAVY_PARTIAL)).toBe('building')

    const body = await runWatchdog()

    expect(await stateOf(HEAVY_PARTIAL)).toBe('incomplete')
    expect(await stateOf(HEAVY_PARTIAL)).not.toBe('lit')
    expect(body.stuck_assets_withheld_incomplete).toBe(1)

    // The withheld row records why, and preserves the observed row count.
    const r = await pool.query<{ last_error: string; rows_written: number }>(
      'SELECT last_error, rows_written FROM asset_throughput WHERE chart_id = $1 AND asset_id = $2',
      [CHART, HEAVY_PARTIAL]
    )
    expect(r.rows[0]!.last_error).toMatch(/78 substep\(s\) committed/)
    expect(r.rows[0]!.last_error).toMatch(/NOT promoted to 'lit'/)
    expect(r.rows[0]!.rows_written).toBe(7800)
  })

  it('never claims completion in build_run_assets for a withheld asset', async () => {
    const run = await pool.query<{ id: string }>(
      `INSERT INTO build_runs (chart_id, state, started_at)
       VALUES ($1, 'running', NOW() - INTERVAL '20 minutes') RETURNING id`,
      [CHART]
    )
    await pool.query(
      `INSERT INTO build_run_assets (run_id, asset_id, state) VALUES ($1, $2, 'building')`,
      [run.rows[0]!.id, HEAVY_PARTIAL]
    )

    await runWatchdog()

    const bra = await pool.query<{ state: string }>(
      'SELECT state FROM build_run_assets WHERE asset_id = $1',
      [HEAVY_PARTIAL]
    )
    expect(bra.rows[0]!.state).not.toBe('complete')
    await pool.query('TRUNCATE build_run_assets, build_runs')
  })

  it('STILL rescues a planless asset with rows present (D-3 Part B intact)', async () => {
    const body = await runWatchdog()
    expect(await stateOf(LIGHT_RESCUABLE)).toBe('lit')
    expect(body.stuck_assets_rescued).toBe(1)
  })

  it('STILL errors assets with no data, plan-bearing or not (unchanged)', async () => {
    const body = await runWatchdog()
    expect(await stateOf(LIGHT_NODATA)).toBe('error')
    expect(await stateOf(HEAVY_NODATA)).toBe('error')
    expect(body.stuck_assets_failed).toBe(2)
  })

  it('leaves a fresh heartbeat completely alone', async () => {
    await runWatchdog()
    expect(await stateOf(LIGHT_FRESH)).toBe('building')
  })

  it('is idempotent — a second tick does not later promote the withheld asset', async () => {
    // The withheld asset leaves 'building', so it is no longer a candidate. This
    // pins that no subsequent tick can walk it up to 'lit' after the fact.
    await runWatchdog()
    expect(await stateOf(HEAVY_PARTIAL)).toBe('incomplete')
    const body2 = await runWatchdog()
    expect(await stateOf(HEAVY_PARTIAL)).toBe('incomplete')
    expect(body2.stuck_assets_withheld_incomplete).toBe(0)
  })
})
