// @vitest-environment node
/**
 * terminalizeFailedRun — LIVE-DB counterpart (Suvarna E3.2 review fix 1).
 *
 * The helper's `state NOT IN ('completed','failed','stopped')` guard belongs on the
 * run UPDATE only (it stops a completed run being clobbered to 'failed'). The
 * companion build_run_assets abort must NOT ride on that guard: the pre-A2 code
 * aborted a run's still-queued assets unconditionally, and
 * `cockpit/runs/[id]/stop` sets a planned run straight to 'stopped' without touching
 * its assets — so a stopped/failed run would otherwise keep 'queued' assets forever.
 *
 * Requires a THROWAWAY database named `terminalize_run_test`:
 *   createdb -h 127.0.0.1 -p 55432 -U postgres terminalize_run_test
 *   TERMINALIZE_RUN_TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:55432/terminalize_run_test \
 *     npx vitest run tests/integration/terminalize_failed_run.db.test.ts
 * Skipped unless TERMINALIZE_RUN_TEST_DATABASE_URL is set.
 */
import { describe, it, expect, beforeAll, afterAll, beforeEach } from 'vitest'
import { Pool } from 'pg'

const TEST_DB_URL = process.env.TERMINALIZE_RUN_TEST_DATABASE_URL
const CHART = '00000000-0000-4000-8000-0000000000b1'

let pool: Pool

async function seedRun(state: string, lastError: string | null = null): Promise<string> {
  const run = await pool.query<{ id: string }>(
    `INSERT INTO build_runs (chart_id, state, last_error, ended_at)
     VALUES ($1, $2, $3, CASE WHEN $2 IN ('completed','failed','stopped') THEN NOW() ELSE NULL END)
     RETURNING id`,
    [CHART, state, lastError]
  )
  const runId = run.rows[0]!.id
  await pool.query(
    `INSERT INTO build_run_assets (run_id, asset_id, position, state) VALUES ($1, 'a_queued', 0, 'queued')`,
    [runId]
  )
  await pool.query(
    `INSERT INTO build_run_assets (run_id, asset_id, position, state) VALUES ($1, 'a_done', 1, 'complete')`,
    [runId]
  )
  return runId
}

async function assetStates(runId: string): Promise<Record<string, { state: string; error: string | null }>> {
  const { rows } = await pool.query<{ asset_id: string; state: string; error: string | null }>(
    'SELECT asset_id, state, error FROM build_run_assets WHERE run_id = $1', [runId]
  )
  return Object.fromEntries(rows.map(r => [r.asset_id, { state: r.state, error: r.error }]))
}

describe.skipIf(!TEST_DB_URL)('terminalizeFailedRun (live DB)', () => {
  let terminalizeFailedRun: (runId: string, message: string) => Promise<void>

  beforeAll(async () => {
    if (!/terminalize_run_test/.test(TEST_DB_URL!)) {
      throw new Error(
        'TERMINALIZE_RUN_TEST_DATABASE_URL must point at a disposable database named ' +
          '`terminalize_run_test`. This suite creates and drops schema objects.'
      )
    }
    process.env.DATABASE_URL = TEST_DB_URL
    pool = new Pool({ connectionString: TEST_DB_URL })
    await pool.query(`
      DROP TABLE IF EXISTS build_run_assets, build_runs CASCADE;
      CREATE TABLE build_runs (
        id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        chart_id   uuid NOT NULL,
        state      text,
        started_at timestamptz,
        ended_at   timestamptz,
        last_error text
      );
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
          CHECK (state = ANY (ARRAY['queued','building','complete','skipped','error','aborted']))
      );
    `)
    ;({ terminalizeFailedRun } = await import('@/lib/build/terminalizeFailedRun'))
  })

  afterAll(async () => {
    if (!pool) return
    await pool.query('DROP TABLE IF EXISTS build_run_assets, build_runs CASCADE')
    await pool.end()
  })

  beforeEach(async () => {
    await pool.query('TRUNCATE build_run_assets, build_runs CASCADE')
  })

  it('a planned run is failed and its queued assets aborted with the same text', async () => {
    const runId = await seedRun('planned')
    await terminalizeFailedRun(runId, 'dispatch boom')
    const run = await pool.query('SELECT state, last_error FROM build_runs WHERE id = $1', [runId])
    expect(run.rows[0]).toMatchObject({ state: 'failed', last_error: 'dispatch boom' })
    const a = await assetStates(runId)
    expect(a.a_queued).toEqual({ state: 'aborted', error: 'dispatch boom' })
    expect(a.a_done).toEqual({ state: 'complete', error: null })
  })

  it('an already-STOPPED run (stop route sets planned -> stopped without touching assets) keeps no queued assets', async () => {
    const runId = await seedRun('stopped')
    await terminalizeFailedRun(runId, 'dispatch boom after stop')
    const run = await pool.query('SELECT state, last_error FROM build_runs WHERE id = $1', [runId])
    // The run itself stays stopped — the guard still protects terminal runs.
    expect(run.rows[0]).toMatchObject({ state: 'stopped', last_error: null })
    const a = await assetStates(runId)
    expect(a.a_queued.state).toBe('aborted')
    expect(a.a_queued.error).toBe('dispatch boom after stop')
    expect(a.a_done).toEqual({ state: 'complete', error: null })
  })

  it('an already-FAILED run keeps its FIRST error text but still has its queued assets aborted', async () => {
    const runId = await seedRun('failed', 'first error')
    await terminalizeFailedRun(runId, 'second error')
    const run = await pool.query('SELECT state, last_error FROM build_runs WHERE id = $1', [runId])
    expect(run.rows[0]).toMatchObject({ state: 'failed', last_error: 'first error' })
    const a = await assetStates(runId)
    expect(a.a_queued.state).toBe('aborted')
  })

  it('a COMPLETED run is never clobbered to failed', async () => {
    const runId = await seedRun('completed')
    await terminalizeFailedRun(runId, 'late dispatch error')
    const run = await pool.query('SELECT state, last_error FROM build_runs WHERE id = $1', [runId])
    expect(run.rows[0]).toMatchObject({ state: 'completed', last_error: null })
    const a = await assetStates(runId)
    expect(a.a_done).toEqual({ state: 'complete', error: null })
  })

  it('is idempotent — a second call changes nothing', async () => {
    const runId = await seedRun('planned')
    await terminalizeFailedRun(runId, 'boom')
    await terminalizeFailedRun(runId, 'other')
    const run = await pool.query('SELECT state, last_error FROM build_runs WHERE id = $1', [runId])
    expect(run.rows[0]).toMatchObject({ state: 'failed', last_error: 'boom' })
    expect((await assetStates(runId)).a_queued).toEqual({ state: 'aborted', error: 'boom' })
  })
})
