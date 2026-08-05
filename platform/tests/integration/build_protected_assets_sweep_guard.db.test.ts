// @vitest-environment node
/**
 * SHAD-DARSHANA sweep-protection Phase 1a, Layers 3+4 — LIVE-DB test.
 *
 * Executes the REAL migration file (539_build_protected_assets.sql) against a
 * REAL throwaway Postgres, so the trigger pair is proven end-to-end against
 * its own on-disk SQL rather than a hand-copied re-implementation that could
 * silently drift from what actually ships (CLAUDE.md §N.8 — a detector must
 * measure the claim it asserts, not a proxy for it).
 *
 * Requires a THROWAWAY database. It is skipped unless
 * SWEEP_GUARD_TEST_DATABASE_URL is set, and it refuses to run against
 * anything that is not obviously disposable (see the guard in beforeAll) —
 * this suite CREATEs and DROPs schema objects and must never touch
 * production. Mirrors tests/integration/watchdog_substep_lit_guard.db.test.ts's
 * pattern exactly.
 *
 *   initdb -D /tmp/pgdata -U postgres --auth=trust
 *   pg_ctl -D /tmp/pgdata -o "-p 55432 -k '' -c listen_addresses=127.0.0.1" start
 *   createdb -h 127.0.0.1 -p 55432 -U postgres sweep_guard_test
 *   SWEEP_GUARD_TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:55432/sweep_guard_test \
 *     npx vitest run tests/integration/build_protected_assets_sweep_guard.db.test.ts
 */
import { describe, it, expect, beforeAll, afterAll, beforeEach } from 'vitest'
import { Pool, type PoolClient } from 'pg'
import fs from 'fs'
import path from 'path'

const TEST_DB_URL = process.env.SWEEP_GUARD_TEST_DATABASE_URL

// Fixture chart_ids. Prefixed with a distinct `00000000-...-00aa`/`00bb` block
// (same fixture-UUID idiom as watchdog_substep_lit_guard.db.test.ts) so they
// can never collide with a real chart_id.
const PROTECTED_CHART = '00000000-0000-4000-8000-0000000000aa'
const OTHER_CHART = '00000000-0000-4000-8000-0000000000bb'
const ASSET_ID = 'ka_gochara_sweep'

const MIGRATION_PATH = path.resolve(
  __dirname,
  '../../supabase/migrations/539_build_protected_assets.sql'
)

let pool: Pool

function windowRow(chartId: string, n: number) {
  // Minimal legal row shape for kala_gochara_windows (all NOT NULL-without-
  // DEFAULT columns supplied); n keeps window_start distinct so the unique
  // natural-key index never collides across seeded rows.
  return {
    chart_id: chartId,
    event_class: 'test_event',
    temporal_shape: 'point',
    window_start: `2020-01-${String((n % 27) + 1).padStart(2, '0')}`,
    window_end: `2020-01-${String((n % 27) + 1).padStart(2, '0')}`,
    peak_date: `2020-01-${String((n % 27) + 1).padStart(2, '0')}`,
    signed_intensity: 1.0,
    raw_intensity: 1.0,
    valence: 'neutral',
    is_adverse: false,
  }
}

async function insertWindowRow(chartId: string, n: number): Promise<number> {
  const r = windowRow(chartId, n)
  const res = await pool.query<{ id: number }>(
    `INSERT INTO kala_gochara_windows
       (chart_id, event_class, temporal_shape, window_start, window_end,
        peak_date, signed_intensity, raw_intensity, valence, is_adverse)
     VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
     RETURNING id`,
    [
      r.chart_id, r.event_class, r.temporal_shape, r.window_start, r.window_end,
      r.peak_date, r.signed_intensity, r.raw_intensity, r.valence, r.is_adverse,
    ]
  )
  return res.rows[0]!.id
}

async function countRows(chartId: string): Promise<number> {
  const res = await pool.query<{ count: string }>(
    'SELECT COUNT(*)::text AS count FROM kala_gochara_windows WHERE chart_id = $1',
    [chartId]
  )
  return parseInt(res.rows[0]!.count, 10)
}

/** Run `fn` inside a transaction with the override GUC set SET LOCAL — exactly
 *  the production opt-in mechanism (a session-scoped, per-transaction flag
 *  that auto-resets on COMMIT/ROLLBACK, never a standing session setting). */
async function withOverride<T>(fn: (client: PoolClient) => Promise<T>): Promise<T> {
  const client = await pool.connect()
  try {
    await client.query('BEGIN')
    await client.query("SET LOCAL app.allow_protected_sweep_rewrite = 'on'")
    const result = await fn(client)
    await client.query('COMMIT')
    return result
  } catch (err) {
    await client.query('ROLLBACK')
    throw err
  } finally {
    client.release()
  }
}

describe.skipIf(!TEST_DB_URL)('build_protected_assets sweep-protection triggers — live DB', () => {
  beforeAll(async () => {
    // Refuse to run anywhere that is not plainly a throwaway.
    if (!/sweep_guard_test/.test(TEST_DB_URL!)) {
      throw new Error(
        'SWEEP_GUARD_TEST_DATABASE_URL must point at a disposable database named ' +
          '`sweep_guard_test`. This suite creates and drops schema objects and ' +
          'must never run against production.'
      )
    }

    pool = new Pool({ connectionString: TEST_DB_URL })

    // Minimal faithful kala_gochara_windows — exactly the NOT-NULL-without-
    // DEFAULT columns migration 460 declares, enough for the trigger under
    // test (which only ever reads OLD.chart_id) to attach and fire for real.
    await pool.query(`
      DROP TABLE IF EXISTS kala_gochara_windows, build_protected_assets CASCADE;
      DROP FUNCTION IF EXISTS build_protected_assets_guard_row() CASCADE;
      DROP FUNCTION IF EXISTS build_protected_assets_guard_truncate() CASCADE;

      CREATE TABLE kala_gochara_windows (
        id BIGSERIAL PRIMARY KEY,
        chart_id UUID NOT NULL,
        event_class TEXT NOT NULL,
        temporal_shape TEXT NOT NULL CHECK (temporal_shape IN ('point', 'interval', 'chain')),
        window_start DATE NOT NULL,
        window_end DATE NOT NULL,
        peak_date DATE NOT NULL,
        milestone_id TEXT,
        is_irreversibility_milestone BOOLEAN NOT NULL DEFAULT FALSE,
        signed_intensity NUMERIC NOT NULL,
        raw_intensity NUMERIC NOT NULL,
        valence TEXT NOT NULL,
        is_adverse BOOLEAN NOT NULL,
        active_sentences JSONB NOT NULL DEFAULT '[]'::jsonb,
        contributing_systems JSONB NOT NULL DEFAULT '[]'::jsonb,
        suppression_state JSONB NOT NULL DEFAULT '{}'::jsonb,
        peak_basis TEXT NOT NULL DEFAULT 'gochara_lambda_e_v1',
        calibration_state TEXT NOT NULL DEFAULT 'structural_prior',
        source TEXT NOT NULL DEFAULT 'live',
        computed_at TIMESTAMPTZ NOT NULL DEFAULT now()
      );
    `)

    // Execute the REAL migration file — the trigger functions/triggers/table
    // under test are the exact ones that will ship, not a re-implementation.
    const migrationSql = fs.readFileSync(MIGRATION_PATH, 'utf8')
    await pool.query(migrationSql)

    // The migration itself only seeds the two CANONICAL chart_ids. This
    // suite's fixture PROTECTED_CHART is a distinct test UUID (never a real
    // chart_id — see the fixture-UUID note above) and must be registered as
    // protected explicitly, exactly as a native designating a new protected
    // pair would via a real INSERT into build_protected_assets.
    await pool.query(
      `INSERT INTO build_protected_assets (asset_id, chart_id, reason)
       VALUES ($1, $2, 'test fixture protection')
       ON CONFLICT (asset_id, chart_id) DO NOTHING`,
      [ASSET_ID, PROTECTED_CHART]
    )
  })

  afterAll(async () => {
    if (!pool) return
    await pool.query(`
      DROP TABLE IF EXISTS kala_gochara_windows, build_protected_assets CASCADE;
      DROP FUNCTION IF EXISTS build_protected_assets_guard_row() CASCADE;
      DROP FUNCTION IF EXISTS build_protected_assets_guard_truncate() CASCADE;
    `)
    await pool.end()
  })

  beforeEach(async () => {
    await withOverride(client => client.query('TRUNCATE kala_gochara_windows RESTART IDENTITY'))
    await insertWindowRow(PROTECTED_CHART, 1)
    await insertWindowRow(PROTECTED_CHART, 2)
    await insertWindowRow(OTHER_CHART, 3)
  })

  it('migration seeded the two canonical protected pairs', async () => {
    const res = await pool.query<{ chart_id: string }>(
      'SELECT chart_id FROM build_protected_assets WHERE asset_id = $1 ORDER BY chart_id',
      [ASSET_ID]
    )
    const chartIds = res.rows.map(r => r.chart_id)
    expect(chartIds).toContain('482012f1-710e-4a25-994a-93821f5871aa')
    expect(chartIds).toContain('1c826d5a-41cb-4450-b4dc-59d440e5f75a')
  })

  it('(a) DELETE on a protected chart raises without the override', async () => {
    await expect(
      pool.query('DELETE FROM kala_gochara_windows WHERE chart_id = $1', [PROTECTED_CHART])
    ).rejects.toThrow(/BUILD-PROTECTED/)
    // Nothing was removed — the raised exception aborts the whole statement.
    expect(await countRows(PROTECTED_CHART)).toBe(2)
  })

  it('(b) DELETE on a protected chart succeeds WITH the override set', async () => {
    await withOverride(async client => {
      await client.query('DELETE FROM kala_gochara_windows WHERE chart_id = $1', [PROTECTED_CHART])
    })
    expect(await countRows(PROTECTED_CHART)).toBe(0)
  })

  it('(c) a non-protected chart is completely unaffected — no override needed', async () => {
    await pool.query('DELETE FROM kala_gochara_windows WHERE chart_id = $1', [OTHER_CHART])
    expect(await countRows(OTHER_CHART)).toBe(0)
    // The protected chart's rows were never touched by this statement.
    expect(await countRows(PROTECTED_CHART)).toBe(2)
  })

  it('(d) INSERT is always allowed, protected chart or not, no override needed', async () => {
    await insertWindowRow(PROTECTED_CHART, 4)
    expect(await countRows(PROTECTED_CHART)).toBe(3)
  })

  it('UPDATE on a protected chart raises without the override', async () => {
    await expect(
      pool.query(
        "UPDATE kala_gochara_windows SET valence = 'gain' WHERE chart_id = $1",
        [PROTECTED_CHART]
      )
    ).rejects.toThrow(/BUILD-PROTECTED/)
  })

  it('UPDATE on a protected chart succeeds WITH the override set', async () => {
    await withOverride(async client => {
      await client.query(
        "UPDATE kala_gochara_windows SET valence = 'gain' WHERE chart_id = $1",
        [PROTECTED_CHART]
      )
    })
    const res = await pool.query<{ valence: string }>(
      'SELECT valence FROM kala_gochara_windows WHERE chart_id = $1 LIMIT 1',
      [PROTECTED_CHART]
    )
    expect(res.rows[0]!.valence).toBe('gain')
  })

  it('UPDATE on a non-protected chart proceeds normally', async () => {
    await pool.query(
      "UPDATE kala_gochara_windows SET valence = 'gain' WHERE chart_id = $1",
      [OTHER_CHART]
    )
    const res = await pool.query<{ valence: string }>(
      'SELECT valence FROM kala_gochara_windows WHERE chart_id = $1 LIMIT 1',
      [OTHER_CHART]
    )
    expect(res.rows[0]!.valence).toBe('gain')
  })

  it('TRUNCATE raises while any protected pair exists, without the override', async () => {
    await expect(pool.query('TRUNCATE kala_gochara_windows')).rejects.toThrow(/BUILD-PROTECTED/)
    expect(await countRows(PROTECTED_CHART)).toBe(2)
    expect(await countRows(OTHER_CHART)).toBe(1)
  })

  it('TRUNCATE succeeds WITH the override set', async () => {
    await withOverride(async client => {
      await client.query('TRUNCATE kala_gochara_windows')
    })
    expect(await countRows(PROTECTED_CHART)).toBe(0)
    expect(await countRows(OTHER_CHART)).toBe(0)
  })

  it('the override GUC does not leak across transactions (SET LOCAL, not SET)', async () => {
    await withOverride(async client => {
      await client.query('DELETE FROM kala_gochara_windows WHERE chart_id = $1', [PROTECTED_CHART])
    })
    // A fresh statement outside that transaction must be guarded again.
    await insertWindowRow(PROTECTED_CHART, 5)
    await expect(
      pool.query('DELETE FROM kala_gochara_windows WHERE chart_id = $1', [PROTECTED_CHART])
    ).rejects.toThrow(/BUILD-PROTECTED/)
  })
})
