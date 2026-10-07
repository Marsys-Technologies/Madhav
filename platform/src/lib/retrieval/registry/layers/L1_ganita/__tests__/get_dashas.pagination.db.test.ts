import { randomUUID } from 'node:crypto'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import { afterAll, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import { Pool } from 'pg'

const { queryMock } = vi.hoisted(() => ({ queryMock: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: queryMock }))

import { getDashasCapability } from '../get_dashas'

// This is an isolated, localhost-only disposable schema. It validates the real
// PostgreSQL CTE rather than reproducing fence outcomes in an adapter mock.
const DATABASE_URL = process.env.PURNA_ANVESANA_OVERLAY_TEST_DATABASE_URL
const run = DATABASE_URL ? describe : describe.skip
const schema = `purna_dasha_pagination_${randomUUID().replaceAll('-', '')}`
const chartId = '482012f1-710e-4a25-994a-93821f5871aa'
const runA = '11111111-1111-4111-8111-111111111111'
const runB = '22222222-2222-4222-8222-222222222222'
const dashaRowB = '33333333-3333-4333-8333-333333333333'
const specSha = '573e8aa1a0298d6626784b5ff540c004fd4d2298b6b47d2980a447acdc193d14'
const receiptObservedAt = '2026-09-17T10:00:00Z'

function assertDisposableDatabase(url: string): void {
  const parsed = new URL(url)
  if (!['localhost', '127.0.0.1', '::1'].includes(parsed.hostname)) {
    throw new Error('PURNA_ANVESANA_OVERLAY_TEST_DATABASE_URL must target localhost')
  }
  if (!parsed.pathname.endsWith('/purna_overlay_test')) {
    throw new Error('PURNA_ANVESANA_OVERLAY_TEST_DATABASE_URL must target database purna_overlay_test')
  }
}

function migration(relativePath: string): string {
  return readFileSync(path.join(process.cwd(), relativePath), 'utf8')
}

const signingEnvironment = {
  INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID: 'inquiry-v1',
  INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT: Buffer.alloc(32, 3).toString('base64url'),
}
const originalSigningEnvironment = {
  kid: process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID,
  key: process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT,
}

run('get_dashas disposable PostgreSQL overlapping terminal replacement fence', () => {
  let admin: Pool
  let scoped: Pool

  beforeAll(async () => {
    assertDisposableDatabase(DATABASE_URL!)
    admin = new Pool({ connectionString: DATABASE_URL!, max: 1 })
    await admin.query(`CREATE SCHEMA ${schema}`)
    scoped = new Pool({ connectionString: DATABASE_URL!, max: 1, options: `-c search_path=${schema}` })
    queryMock.mockImplementation(async (sql: string, params: unknown[] = []) => scoped.query(sql, params))
    process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID = signingEnvironment.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID
    process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT = signingEnvironment.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT

    await scoped.query(`
      CREATE TABLE charts (
        id uuid PRIMARY KEY, birth_date date, birth_time time, birth_lat numeric, birth_lng numeric,
        birth_place text, timezone_id text, name text, subject_name text, preferred_name text
      );
      CREATE TABLE asset_registry (
        asset_id text PRIMARY KEY, depends_on jsonb, natural_key_partition text, health_probe text,
        integrity_check_sql text, target_floor integer, asset_kind text, asset_type text, scope text,
        has_writer boolean, is_active boolean, target_table text
      );
      CREATE TABLE asset_throughput (asset_id text PRIMARY KEY);
      CREATE TABLE chart_dashas (
        dasha_row_id uuid PRIMARY KEY, chart_id uuid NOT NULL, build_id uuid NOT NULL,
        system_id text NOT NULL, ayanamsha_id text NOT NULL, level_n integer NOT NULL,
        start_date date NOT NULL, end_date date NOT NULL, start_iso timestamptz NOT NULL
      );
    `)
    const digestSql = migration('supabase/migrations/598_nirmana_output_digest_specs.sql')
      + migration('migrations/881_nirmana_l1_ga_dashas_output_digest_spec.sql')
    const assetIds = [...digestSql.matchAll(/'([a-z0-9_]+)'\s*,\s*'[a-f0-9]{64}'/g)].map((match) => match[1]!)
    await scoped.query(
      'INSERT INTO asset_registry(asset_id) SELECT unnest($1::text[]) ON CONFLICT DO NOTHING',
      [[...new Set(assetIds)]],
    )
    await scoped.query(migration('supabase/migrations/171_build_runs.sql'))
    await scoped.query(migration('supabase/migrations/596_nirmana_provenance_receipts.sql'))
    await scoped.query(migration('supabase/migrations/598_nirmana_output_digest_specs.sql'))
    await scoped.query(migration('migrations/881_nirmana_l1_ga_dashas_output_digest_spec.sql'))
    await scoped.query(migration('migrations/640_nirmana_owave_wp1_output_changed.sql'))
    await scoped.query(migration('migrations/641_nirmana_owave_wp2_disposition.sql'))
    await scoped.query(migration('supabase/migrations/499_orchestrator_event_register.sql'))

    await scoped.query('INSERT INTO charts(id, name) VALUES ($1, $2)', [chartId, 'Disposable Dasha'])
    await scoped.query(`
      INSERT INTO build_runs(id, chart_id, scope, action, state, plan, triggered_by, started_at, ended_at)
      VALUES
        ($1, $3, 'asset', 'build', 'failed', '{}'::jsonb, 'test', '2026-09-17T08:00:00Z', '2026-09-17T12:00:00Z'),
        ($2, $3, 'asset', 'build', 'completed', '{}'::jsonb, 'test', '2026-09-17T09:00:00Z', '2026-09-17T11:00:00Z')
    `, [runA, runB, chartId])
    await scoped.query(`
      INSERT INTO build_run_assets(run_id, asset_id, position, state, started_at, ended_at)
      VALUES
        ($1, 'ga_dashas', 0, 'error', '2026-09-17T08:00:00Z', '2026-09-17T09:00:00Z'),
        ($2, 'ga_dashas', 0, 'complete', '2026-09-17T09:00:00Z', '2026-09-17T11:00:00Z')
    `, [runA, runB])
    await scoped.query(`
      INSERT INTO asset_provenance_receipts
        (asset_id, chart_id, partition_key, receipt_version, receipt_state, build_id, output_digest_spec_sha256, unknown_reasons, observed_at)
      VALUES ('ga_dashas', $1, '__whole_asset__', 'v1', 'proven', $2, $3, '[]', $4)
    `, [chartId, runB, specSha, receiptObservedAt])
    await scoped.query(`
      INSERT INTO asset_freshness(asset_id, chart_id, partition_key, freshness_state, reasons, receipt_version, observed_at)
      VALUES ('ga_dashas', $1, '__whole_asset__', 'fresh', '[]', 'v1', $2)
    `, [chartId, receiptObservedAt])
    await scoped.query(`
      INSERT INTO chart_dashas
        (dasha_row_id, chart_id, build_id, system_id, ayanamsha_id, level_n, start_date, end_date, start_iso)
      VALUES ($1, $2, $3, 'vimshottari', 'lahiri_chitrapaksha', 1, '2000-01-01', '2030-01-01', '2000-01-01T00:00:00Z')
    `, [dashaRowB, chartId, runB])
  }, 30_000)

  beforeEach(async () => {
    await scoped.query("UPDATE build_run_assets SET ended_at = '2026-09-17T09:00:00Z' WHERE run_id = $1", [runA])
  })

  afterAll(async () => {
    if (originalSigningEnvironment.kid === undefined) delete process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID
    else process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID = originalSigningEnvironment.kid
    if (originalSigningEnvironment.key === undefined) delete process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT
    else process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT = originalSigningEnvironment.key
    await scoped?.end()
    if (admin) {
      await admin.query(`DROP SCHEMA IF EXISTS ${schema} CASCADE`)
      await admin.end()
    }
  })

  it('serves B when A asset ended before B receipt even though A run ended afterwards', async () => {
    const result = await getDashasCapability.handler({
      chart_id: chartId, fields: 'all', limit: 10,
      window_start: '2000-01-01', window_end: '2100-01-01',
    }, undefined)

    expect(result).toMatchObject({
      is_error: false,
      content: { build_id: runB, rows: [expect.objectContaining({ dasha_row_id: dashaRowB })] },
    })
  })

  it('requires restart when A asset ended after B receipt', async () => {
    await scoped.query("UPDATE build_run_assets SET ended_at = '2026-09-17T12:00:00Z' WHERE run_id = $1", [runA])

    const result = await getDashasCapability.handler({
      chart_id: chartId, fields: 'all', limit: 10,
      window_start: '2000-01-01', window_end: '2100-01-01',
    }, undefined)

    expect(result).toMatchObject({
      is_error: true,
      content: { code: 'ga_dashas_replacement_in_progress', restart_required: true },
    })
  })

  // Replacement-fence state matrix (RC-2). A fence must represent a producer that
  // can still mutate — or may already have mutated — the served asset. A queued
  // asset row that was never dispatched inside a terminal run is an orphan needing
  // hygiene; it cannot mutate rows and must not block serving forever.
  const runC = '44444444-4444-4444-8444-444444444444'

  async function withFencedRun(
    run: { state: string; ended_at: string | null },
    asset: { state: string; started_at: string | null; ended_at: string | null },
    assertion: () => Promise<void>,
  ): Promise<void> {
    await scoped.query(`
      INSERT INTO build_runs(id, chart_id, scope, action, state, plan, triggered_by, started_at, ended_at)
      VALUES ($1, $2, 'asset', 'build', $3, '{}'::jsonb, 'test', '2026-09-18T08:00:00Z', $4)
    `, [runC, chartId, run.state, run.ended_at])
    await scoped.query(`
      INSERT INTO build_run_assets(run_id, asset_id, position, state, started_at, ended_at)
      VALUES ($1, 'ga_dashas', 0, $2, $3, $4)
    `, [runC, asset.state, asset.started_at, asset.ended_at])
    try {
      await assertion()
    } finally {
      await scoped.query('DELETE FROM build_runs WHERE id = $1', [runC])
    }
  }

  async function readDashas() {
    return getDashasCapability.handler({
      chart_id: chartId, fields: 'all', limit: 10,
      window_start: '2000-01-01', window_end: '2100-01-01',
    }, undefined)
  }

  const served = { is_error: false, content: { build_id: runB, rows: [expect.objectContaining({ dasha_row_id: dashaRowB })] } }
  const fenced = { is_error: true, content: { code: 'ga_dashas_replacement_in_progress', restart_required: true } }

  it('serves B when a never-dispatched queued asset belongs to a failed run that ended before the receipt', async () => {
    await withFencedRun(
      { state: 'failed', ended_at: '2026-08-06T10:00:00Z' },
      { state: 'queued', started_at: null, ended_at: null },
      async () => expect(await readDashas()).toMatchObject(served),
    )
  })

  it('serves B when a never-dispatched queued asset belongs to a terminal run that ended after the receipt', async () => {
    for (const state of ['failed', 'stopped', 'completed']) {
      await withFencedRun(
        { state, ended_at: '2026-09-18T12:00:00Z' },
        { state: 'queued', started_at: null, ended_at: null },
        async () => expect(await readDashas()).toMatchObject(served),
      )
    }
  })

  it('fences while any run that holds the asset is still active', async () => {
    for (const state of ['planned', 'running', 'paused']) {
      await withFencedRun(
        { state, ended_at: null },
        { state: 'queued', started_at: null, ended_at: null },
        async () => expect(await readDashas()).toMatchObject(fenced),
      )
    }
  })

  it('fences a dispatched asset left building by a terminal run that ended after the receipt without a proven receipt', async () => {
    await withFencedRun(
      { state: 'failed', ended_at: '2026-09-18T12:00:00Z' },
      { state: 'building', started_at: '2026-09-18T09:00:00Z', ended_at: null },
      async () => expect(await readDashas()).toMatchObject(fenced),
    )
  })

  it('serves the rows B wrote after a skip_no_delta run re-attributes the receipt (RC-1 twin)', async () => {
    const runSkip = '55555555-5555-4555-8555-555555555555'
    await scoped.query(`
      INSERT INTO build_runs(id, chart_id, scope, action, state, plan, triggered_by, started_at, ended_at)
      VALUES ($1, $2, 'asset', 'build', 'completed', '{}'::jsonb, 'test', '2026-09-18T08:00:00Z', '2026-09-18T08:05:00Z')
    `, [runSkip, chartId])
    await scoped.query(`
      INSERT INTO build_run_assets(run_id, asset_id, position, state, disposition, started_at, ended_at)
      VALUES ($1, 'ga_dashas', 0, 'complete', 'skip_no_delta', '2026-09-18T08:00:00Z', '2026-09-18T08:01:00Z')
    `, [runSkip])
    await scoped.query("UPDATE asset_provenance_receipts SET build_id = $1, observed_at = '2026-09-18T08:01:00Z' WHERE asset_id = 'ga_dashas'", [runSkip])
    try {
      expect(await readDashas()).toMatchObject(served)
    } finally {
      await scoped.query('UPDATE asset_provenance_receipts SET build_id = $1, observed_at = $2 WHERE asset_id = \'ga_dashas\'', [runB, receiptObservedAt])
      await scoped.query('DELETE FROM build_runs WHERE id = $1', [runSkip])
    }
  })

  it('refuses rows when a skip_no_delta receipt has no provable writing run', async () => {
    await scoped.query("UPDATE build_run_assets SET disposition = 'skip_no_delta' WHERE run_id = $1", [runB])
    try {
      expect(await readDashas()).toMatchObject({ is_error: true, content: { code: 'ga_dashas_receipt_unavailable' } })
    } finally {
      await scoped.query('UPDATE build_run_assets SET disposition = NULL WHERE run_id = $1', [runB])
    }
  })

  it('serves B when a building orphan belongs to a terminal run that ended before the receipt', async () => {
    await withFencedRun(
      { state: 'failed', ended_at: '2026-08-06T10:00:00Z' },
      { state: 'building', started_at: '2026-08-06T09:00:00Z', ended_at: null },
      async () => expect(await readDashas()).toMatchObject(served),
    )
  })
  // Per-asset served fence (N-208): a failed run serves an asset that itself finished in it, unless
  // the run that wrote the rows was held back (asset.noop_completion_rejected). This is the inline
  // reader's own SQL predicate (the resolver uses the TS twin), so it needs its own behavioural case.
  describe('failed-run admission in the inline reader', () => {
    const runF = '66666666-6666-4666-8666-666666666666'
    const dashaRowF = '77777777-7777-4777-8777-777777777777'
    const servedF = { is_error: false, content: { build_id: runF, rows: [expect.objectContaining({ dasha_row_id: dashaRowF })] } }

    async function withFailedRunReceipt(
      asset: { state: string }, outcome: string | null, heldBack: boolean, assertion: () => Promise<void>,
    ): Promise<void> {
      await scoped.query(`
        INSERT INTO build_runs(id, chart_id, scope, action, state, plan, triggered_by, started_at, ended_at)
        VALUES ($1, $2, 'asset', 'build', 'failed', '{}'::jsonb, 'test', '2026-09-19T08:00:00Z', '2026-09-19T10:00:00Z')`, [runF, chartId])
      await scoped.query(`
        INSERT INTO build_run_assets(run_id, asset_id, position, state, disposition, started_at, ended_at)
        VALUES ($1, 'ga_dashas', 0, $2, 'build', '2026-09-19T08:00:00Z', '2026-09-19T09:00:00Z')`, [runF, asset.state])
      await scoped.query(`
        INSERT INTO chart_dashas (dasha_row_id, chart_id, build_id, system_id, ayanamsha_id, level_n, start_date, end_date, start_iso)
        VALUES ($1, $2, $3, 'vimshottari', 'lahiri_chitrapaksha', 1, '2000-01-01', '2030-01-01', '2000-01-01T00:00:00Z')`, [dashaRowF, chartId, runF])
      await scoped.query("UPDATE asset_provenance_receipts SET build_id = $1, observed_at = '2026-09-19T09:00:00Z' WHERE asset_id = 'ga_dashas'", [runF])
      if (outcome) await scoped.query('INSERT INTO asset_throughput(chart_id, asset_id, state) VALUES ($1, \'ga_dashas\', $2)', [chartId, outcome])
      if (heldBack) {
        await scoped.query(`INSERT INTO orchestrator_event_register(event_type, chart_id, asset_id, run_id)
                            VALUES ('asset.noop_completion_rejected', $1, 'ga_dashas', $2)`, [chartId, runF])
      }
      try {
        await assertion()
      } finally {
        await scoped.query('UPDATE asset_provenance_receipts SET build_id = $1, observed_at = $2 WHERE asset_id = \'ga_dashas\'', [runB, receiptObservedAt])
        await scoped.query('DELETE FROM orchestrator_event_register WHERE run_id = $1', [runF])
        await scoped.query('DELETE FROM asset_throughput WHERE asset_id = \'ga_dashas\'')
        await scoped.query('DELETE FROM chart_dashas WHERE dasha_row_id = $1', [dashaRowF])
        await scoped.query('DELETE FROM build_runs WHERE id = $1', [runF])
      }
    }
    const refused = { is_error: true, content: { code: 'ga_dashas_receipt_unavailable' } }

    it('serves the rows of an asset that finished in a failed run', async () => {
      await withFailedRunReceipt({ state: 'complete' }, 'lit', false, async () => expect(await readDashas()).toMatchObject(servedF))
    })

    it('refuses the rows of a failed run whose writer was held back (asset.noop_completion_rejected)', async () => {
      await withFailedRunReceipt({ state: 'complete' }, 'lit', true, async () => expect(await readDashas()).toMatchObject(refused))
    })

    it('refuses a failed-run receipt whose asset errored, is stale, or has no recorded outcome', async () => {
      await withFailedRunReceipt({ state: 'error' }, 'lit', false, async () => expect(await readDashas()).toMatchObject(refused))
      await withFailedRunReceipt({ state: 'complete' }, 'stale', false, async () => expect(await readDashas()).toMatchObject(refused))
      await withFailedRunReceipt({ state: 'complete' }, null, false, async () => expect(await readDashas()).toMatchObject(refused))
    })
  })
})
