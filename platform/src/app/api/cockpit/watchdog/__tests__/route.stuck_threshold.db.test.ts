// @vitest-environment node
/**
 * HYG-REAPER-LONG-SUBSTEP — the watchdog's per-asset stuck-asset threshold, proven
 * against the REAL route SQL on a disposable PostgreSQL database (N.8: the route's
 * statements are executed by Postgres; nothing here mirrors the predicate in JS).
 *
 * Evidence behind the numbers: J-3c (EXEC-J3C-REPROJECT-1) ka_gochara_v5 substep 34
 * verify:bereavement took 1,086.8 s (> the 900 s default window) on a healthy run.
 *
 * Runs only with KALA_ADMIN_DSN (the local disposable cluster, 127.0.0.1:55433); the
 * fixture creates and drops its own database. KALA_REQUIRE_DB=1 turns "no DSN" into a
 * failure instead of a skip.
 */
import { afterAll, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import { NextRequest } from 'next/server'
import { Client, Pool } from 'pg'

const adminDsn = process.env.KALA_ADMIN_DSN
const required = process.env.KALA_REQUIRE_DB === '1'
const run = adminDsn || required ? describe : describe.skip

let pool: Pool | null = null
const mockVerifyOidcToken = vi.fn()
vi.mock('@/lib/db/client', () => ({
  query: (text: string, params?: unknown[]) => pool!.query(text, params as unknown[]),
}))
vi.mock('@/lib/auth/oidc', () => ({ verifyOidcToken: mockVerifyOidcToken }))

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const DB_NAME = `wd_thresh_${process.pid}_${Date.now()}`
const SCHEMA = `
  CREATE TABLE asset_registry (asset_id text PRIMARY KEY, count_sql text, target_floor int, has_substeps boolean);
  CREATE TABLE build_runs (id uuid PRIMARY KEY DEFAULT gen_random_uuid(), chart_id uuid, state text,
    started_at timestamptz, ended_at timestamptz, last_error text, created_at timestamptz DEFAULT NOW());
  CREATE TABLE build_run_assets (run_id uuid, asset_id text, state text, ended_at timestamptz, error text);
  CREATE TABLE asset_throughput (chart_id uuid, asset_id text, state text, last_built_at timestamptz,
    last_error text, rows_written int);
  CREATE TABLE build_substep_progress (chart_id uuid, asset_id text, completed_at timestamptz);
  CREATE TABLE wd_data (chart_id uuid);
`

function makeReq(): NextRequest {
  return new NextRequest('http://localhost/api/cockpit/watchdog', {
    method: 'POST',
    headers: { Authorization: 'Bearer valid-google-id-token' },
  })
}

/** One in-flight run (started 40 min ago) with one 'building' asset silent for `staleMinutes`. */
async function seedBuilding(assetId: string, staleMinutes: number, opts: { dataRows?: boolean; hasSubsteps?: boolean } = {}) {
  await pool!.query(
    `INSERT INTO asset_registry (asset_id, count_sql, target_floor, has_substeps) VALUES ($1, $2, NULL, $3)`,
    [assetId, opts.dataRows ? 'SELECT COUNT(*) FROM wd_data WHERE chart_id = $1' : null, opts.hasSubsteps ?? true]
  )
  if (opts.dataRows) await pool!.query(`INSERT INTO wd_data VALUES ($1)`, [CHART])
  const run = await pool!.query<{ id: string }>(
    `INSERT INTO build_runs (chart_id, state, started_at) VALUES ($1, 'running', NOW() - INTERVAL '40 minutes') RETURNING id`,
    [CHART]
  )
  await pool!.query(
    `INSERT INTO build_run_assets (run_id, asset_id, state) VALUES ($1, $2, 'building')`,
    [run.rows[0].id, assetId]
  )
  await pool!.query(
    `INSERT INTO asset_throughput (chart_id, asset_id, state, last_built_at)
     VALUES ($1, $2, 'building', NOW() - make_interval(mins => $3))`,
    [CHART, assetId, staleMinutes]
  )
  return run.rows[0].id
}

async function states(assetId: string, runId: string) {
  const a = await pool!.query<{ state: string }>(`SELECT state FROM asset_throughput WHERE asset_id = $1`, [assetId])
  const b = await pool!.query<{ state: string }>(`SELECT state FROM build_run_assets WHERE asset_id = $1`, [assetId])
  const r = await pool!.query<{ state: string }>(`SELECT state FROM build_runs WHERE id = $1`, [runId])
  return { throughput: a.rows[0].state, runAsset: b.rows[0].state, run: r.rows[0].state }
}

run('watchdog per-asset stuck threshold (real SQL)', () => {
  beforeAll(async () => {
    if (!adminDsn) throw new Error('KALA_REQUIRE_DB=1 but KALA_ADMIN_DSN is not set')
    const u = new URL(adminDsn)
    if (u.hostname !== '127.0.0.1' || u.port !== '55433') {
      throw new Error('KALA_ADMIN_DSN must target the local disposable cluster 127.0.0.1:55433')
    }
    const admin = new Client({ connectionString: adminDsn })
    await admin.connect()
    await admin.query(`CREATE DATABASE ${DB_NAME}`)
    await admin.end()
    u.pathname = `/${DB_NAME}`
    pool = new Pool({ connectionString: u.toString() })
    await pool.query(SCHEMA)
  })

  afterAll(async () => {
    if (pool) await pool.end()
    if (adminDsn) {
      const admin = new Client({ connectionString: adminDsn })
      await admin.connect()
      await admin.query(`DROP DATABASE IF EXISTS ${DB_NAME} WITH (FORCE)`)
      await admin.end()
    }
  })

  beforeEach(async () => {
    mockVerifyOidcToken.mockResolvedValue({ email: 'amjis-scheduler@madhav-astrology.iam.gserviceaccount.com' })
    process.env.PUBSUB_DISABLED = '1'
    await pool!.query(
      `TRUNCATE asset_registry, build_runs, build_run_assets, asset_throughput, build_substep_progress, wd_data`
    )
  })

  it('does NOT reap a ka_gochara_v5 building row 20 min stale (healthy 18-min substep)', async () => {
    const runId = await seedBuilding('ka_gochara_v5', 20)
    const { POST } = await import('../route')
    const body = await (await POST(makeReq())).json()
    expect(body.stuck_assets_failed).toBe(0)
    expect(body.stuck_assets_withheld_incomplete).toBe(0)
    expect(body.orphan_runs_failed).toBe(0) // clause 1 heartbeat test honours the same threshold
    expect(await states('ka_gochara_v5', runId)).toEqual({ throughput: 'building', runAsset: 'building', run: 'running' })
  })

  it('does NOT mark a data-bearing ka_gochara_v5 (has_substeps, rows landed) incomplete/lit at 20 min stale — the production shape', async () => {
    const runId = await seedBuilding('ka_gochara_v5', 20, { dataRows: true })
    const { POST } = await import('../route')
    const body = await (await POST(makeReq())).json()
    expect(body.stuck_assets_withheld_incomplete).toBe(0)
    expect(body.stuck_assets_rescued).toBe(0)
    expect(body.stuck_assets_failed).toBe(0)
    expect(await states('ka_gochara_v5', runId)).toEqual({ throughput: 'building', runAsset: 'building', run: 'running' })
  })

  it('still withholds a data-bearing ka_gochara_v5 as incomplete once stale beyond its threshold', async () => {
    await seedBuilding('ka_gochara_v5', 70, { dataRows: true })
    const { POST } = await import('../route')
    const body = await (await POST(makeReq())).json()
    expect(body.stuck_assets_withheld_incomplete).toBe(1)
  })

  it('still rescues a data-bearing default light asset 20 min stale (default path unchanged)', async () => {
    await seedBuilding('ga_light_default', 20, { dataRows: true, hasSubsteps: false })
    const { POST } = await import('../route')
    expect((await (await POST(makeReq())).json()).stuck_assets_rescued).toBe(1)
  })

  it('DOES reap a default asset 20 min stale (15-min default unchanged)', async () => {
    const runId = await seedBuilding('ga_some_default_asset', 20)
    const { POST } = await import('../route')
    const body = await (await POST(makeReq())).json()
    expect(body.stuck_assets_failed).toBe(1)
    expect(body.orphan_runs_failed).toBe(1) // clause 1: 40-min run, nothing alive inside 15 min
    expect(await states('ga_some_default_asset', runId)).toEqual({ throughput: 'error', runAsset: 'error', run: 'failed' })
  })

  it('DOES reap ka_gochara_v5 once stale beyond its own threshold (a dead writer is not exempt)', async () => {
    const runId = await seedBuilding('ka_gochara_v5', 70)
    const { POST } = await import('../route')
    const body = await (await POST(makeReq())).json()
    expect(body.stuck_assets_failed).toBe(1)
    expect(body.orphan_runs_failed).toBe(1)
    expect(await states('ka_gochara_v5', runId)).toEqual({ throughput: 'error', runAsset: 'error', run: 'failed' })
  })

  it('spares a ka_gochara_v5 row 59 min stale but not 61 min stale (boundary at the 60-min threshold)', async () => {
    const spared = await seedBuilding('ka_gochara_v5', 59)
    const { POST } = await import('../route')
    expect((await (await POST(makeReq())).json()).stuck_assets_failed).toBe(0)
    expect((await states('ka_gochara_v5', spared)).throughput).toBe('building')
    await pool!.query(`UPDATE asset_throughput SET last_built_at = NOW() - INTERVAL '61 minutes'`)
    expect((await (await POST(makeReq())).json()).stuck_assets_failed).toBe(1)
  })
})
