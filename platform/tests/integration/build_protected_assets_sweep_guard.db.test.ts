// @vitest-environment node
/**
 * SHAD-DARSHANA sweep-protection Phase 1a, Layers 3+4 — LIVE-DB test.
 * Extended by GOCHARA-UTKARSA W0.3 (migration 556) with generation-aware
 * guard tests.
 *
 * Executes the REAL migration files (540 + 556) against a REAL throwaway
 * Postgres, so the trigger pair is proven end-to-end against its own on-disk
 * SQL rather than a hand-copied re-implementation that could silently drift
 * from what actually ships (CLAUDE.md §N.8 — a detector must measure the
 * claim it asserts, not a proxy for it).
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

const MIGRATION_540_PATH = path.resolve(
  __dirname,
  '../../supabase/migrations/540_build_protected_assets.sql'
)
const MIGRATION_556_PATH = path.resolve(
  __dirname,
  '../../supabase/migrations/556_gochara_generation_schema.sql'
)

// Backward compat alias — existing tests reference MIGRATION_PATH
const MIGRATION_PATH = MIGRATION_540_PATH

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

// =============================================================================
// GOCHARA-UTKARSA W0.3 — generation-aware guard tests (migration 556)
// =============================================================================
// A SECOND describe block that applies migration 556 ON TOP of 540, against a
// table that includes the `generation` column (migration 527). Tests the five
// behaviors the generation-inclusive schema must satisfy.

let pool556: Pool

/** Insert a window row with an explicit generation value. */
async function insertWindowRowGen(
  p: Pool,
  chartId: string,
  n: number,
  generation: string = 'v1'
): Promise<number> {
  const r = windowRow(chartId, n)
  const res = await p.query<{ id: number }>(
    `INSERT INTO kala_gochara_windows
       (chart_id, event_class, temporal_shape, window_start, window_end,
        peak_date, signed_intensity, raw_intensity, valence, is_adverse,
        generation)
     VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
     RETURNING id`,
    [
      r.chart_id, r.event_class, r.temporal_shape, r.window_start, r.window_end,
      r.peak_date, r.signed_intensity, r.raw_intensity, r.valence, r.is_adverse,
      generation,
    ]
  )
  return res.rows[0]!.id
}

async function countRows556(p: Pool, chartId: string, generation?: string): Promise<number> {
  if (generation) {
    const res = await p.query<{ count: string }>(
      'SELECT COUNT(*)::text AS count FROM kala_gochara_windows WHERE chart_id = $1 AND generation = $2',
      [chartId, generation]
    )
    return parseInt(res.rows[0]!.count, 10)
  }
  const res = await p.query<{ count: string }>(
    'SELECT COUNT(*)::text AS count FROM kala_gochara_windows WHERE chart_id = $1',
    [chartId]
  )
  return parseInt(res.rows[0]!.count, 10)
}

async function withOverride556<T>(p: Pool, fn: (client: PoolClient) => Promise<T>): Promise<T> {
  const client = await p.connect()
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

describe.skipIf(!TEST_DB_URL)('migration-556 generation-aware guard — live DB', () => {
  beforeAll(async () => {
    if (!/sweep_guard_test/.test(TEST_DB_URL!)) {
      throw new Error(
        'SWEEP_GUARD_TEST_DATABASE_URL must point at a disposable database named ' +
          '`sweep_guard_test`.'
      )
    }

    pool556 = new Pool({ connectionString: TEST_DB_URL })

    // Fresh schema: table WITH `generation` column (migration 527 added it).
    // The unique index is the OLD generation-blind one from migration 460 —
    // migration 556 will replace it.
    await pool556.query(`
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
        computed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        generation TEXT NOT NULL DEFAULT 'v1'
      );

      CREATE UNIQUE INDEX uq_kala_gochara_windows_natural_key
        ON kala_gochara_windows (chart_id, event_class, window_start, peak_date, COALESCE(milestone_id, ''));
    `)

    // Apply migration 540 (guard functions + triggers + build_protected_assets table)
    const migration540 = fs.readFileSync(MIGRATION_540_PATH, 'utf8')
    await pool556.query(migration540)

    // Apply migration 556 (generation-inclusive index + amended guard + new columns)
    const migration556 = fs.readFileSync(MIGRATION_556_PATH, 'utf8')
    await pool556.query(migration556)

    // Register test fixture chart as protected
    await pool556.query(
      `INSERT INTO build_protected_assets (asset_id, chart_id, reason)
       VALUES ($1, $2, 'test fixture protection')
       ON CONFLICT (asset_id, chart_id) DO NOTHING`,
      [ASSET_ID, PROTECTED_CHART]
    )
  })

  afterAll(async () => {
    if (!pool556) return
    await pool556.query(`
      DROP TABLE IF EXISTS kala_gochara_windows, build_protected_assets CASCADE;
      DROP FUNCTION IF EXISTS build_protected_assets_guard_row() CASCADE;
      DROP FUNCTION IF EXISTS build_protected_assets_guard_truncate() CASCADE;
    `)
    await pool556.end()
  })

  beforeEach(async () => {
    await withOverride556(pool556, client =>
      client.query('TRUNCATE kala_gochara_windows RESTART IDENTITY')
    )
    // Seed: 2 v1 rows + 1 v1 row on other chart
    await insertWindowRowGen(pool556, PROTECTED_CHART, 1, 'v1')
    await insertWindowRowGen(pool556, PROTECTED_CHART, 2, 'v1')
    await insertWindowRowGen(pool556, OTHER_CHART, 3, 'v1')
  })

  // ── Test 1: v1 DELETE on protected chart raises ──────────────────────────
  it('v1-DELETE on protected chart raises', async () => {
    await expect(
      pool556.query(
        "DELETE FROM kala_gochara_windows WHERE chart_id = $1 AND generation = 'v1'",
        [PROTECTED_CHART]
      )
    ).rejects.toThrow(/BUILD-PROTECTED/)
    // Nothing removed
    expect(await countRows556(pool556, PROTECTED_CHART, 'v1')).toBe(2)
  })

  // ── Test 2: 3.0-DELETE on protected chart succeeds ───────────────────────
  it('3.0-DELETE on protected chart succeeds (generation 3.0 not in protected_generations)', async () => {
    // Insert a 3.0 row first (different natural key to avoid unique index collision)
    await insertWindowRowGen(pool556, PROTECTED_CHART, 10, '3.0')
    expect(await countRows556(pool556, PROTECTED_CHART, '3.0')).toBe(1)

    // DELETE of 3.0 rows should succeed — '3.0' is NOT in protected_generations '{v1}'
    await expect(
      pool556.query(
        "DELETE FROM kala_gochara_windows WHERE chart_id = $1 AND generation = '3.0'",
        [PROTECTED_CHART]
      )
    ).resolves.toBeDefined()
    expect(await countRows556(pool556, PROTECTED_CHART, '3.0')).toBe(0)
    // v1 rows untouched
    expect(await countRows556(pool556, PROTECTED_CHART, 'v1')).toBe(2)
  })

  // ── Test 3: UPDATE on v1 row of protected chart raises ───────────────────
  it('UPDATE on v1 row of protected chart raises', async () => {
    await expect(
      pool556.query(
        "UPDATE kala_gochara_windows SET valence = 'gain' WHERE chart_id = $1 AND generation = 'v1'",
        [PROTECTED_CHART]
      )
    ).rejects.toThrow(/BUILD-PROTECTED/)
  })

  // ── Test 4: TRUNCATE raises (unchanged behavior) ─────────────────────────
  it('TRUNCATE raises while any protected pair exists', async () => {
    await expect(
      pool556.query('TRUNCATE kala_gochara_windows')
    ).rejects.toThrow(/BUILD-PROTECTED/)
    expect(await countRows556(pool556, PROTECTED_CHART)).toBe(2)
    expect(await countRows556(pool556, OTHER_CHART)).toBe(1)
  })

  // ── Test 5: cross-generation INSERT succeeds (generation-inclusive index) ─
  it('cross-generation INSERT succeeds (v1 and 3.0 coexist with same natural key)', async () => {
    // Get the natural key of an existing v1 row
    const v1Res = await pool556.query<{
      event_class: string
      window_start: string
      window_end: string
      peak_date: string
      milestone_id: string | null
    }>(
      "SELECT event_class, window_start, window_end, peak_date, milestone_id FROM kala_gochara_windows WHERE chart_id = $1 AND generation = 'v1' LIMIT 1",
      [PROTECTED_CHART]
    )
    expect(v1Res.rows.length).toBe(1)
    const v1 = v1Res.rows[0]!

    // Insert a 3.0 row with the SAME natural key — should succeed under the
    // generation-inclusive unique index (migration 556). Under the old
    // generation-blind index this would have raised a unique violation.
    await expect(
      pool556.query(
        `INSERT INTO kala_gochara_windows
           (chart_id, event_class, temporal_shape, window_start, window_end,
            peak_date, milestone_id, signed_intensity, raw_intensity, valence,
            is_adverse, generation)
         VALUES ($1, $2, 'point', $3, $4, $5, $6, 0, 0, 'neutral', false, '3.0')`,
        [
          PROTECTED_CHART,
          v1.event_class,
          v1.window_start,
          v1.window_end,
          v1.peak_date,
          v1.milestone_id,
        ]
      )
    ).resolves.toBeDefined()

    // Both rows coexist
    expect(await countRows556(pool556, PROTECTED_CHART, 'v1')).toBe(2)
    expect(await countRows556(pool556, PROTECTED_CHART, '3.0')).toBe(1)

    // Clean up the test-inserted 3.0 row (no trigger issue — 3.0 is not protected)
    await pool556.query(
      "DELETE FROM kala_gochara_windows WHERE chart_id = $1 AND generation = '3.0'",
      [PROTECTED_CHART]
    )
  })

  // ── Bonus: UPDATE on 3.0 row of protected chart succeeds ────────────────
  it('UPDATE on 3.0 row of protected chart succeeds (not a protected generation)', async () => {
    await insertWindowRowGen(pool556, PROTECTED_CHART, 10, '3.0')
    await expect(
      pool556.query(
        "UPDATE kala_gochara_windows SET valence = 'gain' WHERE chart_id = $1 AND generation = '3.0'",
        [PROTECTED_CHART]
      )
    ).resolves.toBeDefined()
    const res = await pool556.query<{ valence: string }>(
      "SELECT valence FROM kala_gochara_windows WHERE chart_id = $1 AND generation = '3.0' LIMIT 1",
      [PROTECTED_CHART]
    )
    expect(res.rows[0]!.valence).toBe('gain')
    // Clean up
    await pool556.query(
      "DELETE FROM kala_gochara_windows WHERE chart_id = $1 AND generation = '3.0'",
      [PROTECTED_CHART]
    )
  })

  // ── Verify the unique index has 6 key columns ───────────────────────────
  it('unique index uq_kala_gochara_windows_natural_key has 6 key columns (generation-inclusive)', async () => {
    const res = await pool556.query<{ indnatts: number }>(
      `SELECT indnatts FROM pg_index
         JOIN pg_class ON pg_class.oid = pg_index.indexrelid
        WHERE pg_class.relname = 'uq_kala_gochara_windows_natural_key'`
    )
    expect(res.rows.length).toBe(1)
    expect(res.rows[0]!.indnatts).toBe(6)
  })

  // ── Verify protected_generations column exists ──────────────────────────
  it('build_protected_assets has protected_generations column', async () => {
    const res = await pool556.query<{ column_name: string }>(
      `SELECT column_name FROM information_schema.columns
        WHERE table_name = 'build_protected_assets'
          AND column_name = 'protected_generations'`
    )
    expect(res.rows.length).toBe(1)
  })

  // ── Verify era_slice_key column exists ──────────────────────────────────
  it('kala_gochara_windows has era_slice_key column', async () => {
    const res = await pool556.query<{ column_name: string }>(
      `SELECT column_name FROM information_schema.columns
        WHERE table_name = 'kala_gochara_windows'
          AND column_name = 'era_slice_key'`
    )
    expect(res.rows.length).toBe(1)
  })
})
