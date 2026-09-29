// @vitest-environment node
/**
 * KĀLA (L3) pre-elevation Phase 1.1 / B1 — migration 1071's generation guard,
 * LIVE-DB test.
 *
 * Executes the REAL migration file against a REAL throwaway Postgres, so the
 * trigger pair is proven end-to-end against its own on-disk SQL rather than a
 * hand-copied re-implementation that could silently drift from what ships
 * (CLAUDE.md §N.8 — a detector must measure the claim it asserts).
 *
 * Sibling of `build_protected_assets_sweep_guard.db.test.ts`, which covers the
 * migration-540/556 guards. Those guards were DROPPED from production by
 * migration 588 (2026-08-23); this suite covers their generation-keyed
 * replacement, which is keyed on the ROW's `generation` rather than on an
 * `asset_id`, per migration 588's own closing instruction.
 *
 * WHAT MUST HOLD, and what must NOT:
 *   - generation='v1'  DELETE/UPDATE → REFUSED, for every chart, with no
 *     `build_protected_assets` row required (migration 540's guard was
 *     registry-keyed and therefore fail-OPEN for any chart absent from it —
 *     not hypothetical: chart cb73cd3d… holds 2,667 v1 rows and was never
 *     seeded by 540 or 566).
 *   - generation='3.0' DELETE/UPDATE → ALLOWED. `ka_gochara_v3_century_materialize`
 *     legitimately DELETE-then-INSERTs those rows; blocking it is Defect D-02,
 *     the reason 588 removed the old protection. A guard that refused
 *     everything would not be a guard, it would be an outage.
 *   - a GENERATION-BLIND per-chart DELETE → REFUSED, because it sweeps v1 rows
 *     too and the v1 rule aborts the whole statement before any row is removed.
 *   - TRUNCATE → REFUSED unconditionally (always generation-blind).
 *   - INSERT → never gated.
 *
 * Requires a THROWAWAY database. Skipped unless KGW_GUARD_TEST_DATABASE_URL is
 * set, and it refuses to run against anything not obviously disposable.
 *
 *   initdb -D /tmp/kb1/pgdata -U postgres --auth=trust
 *   pg_ctl -D /tmp/kb1/pgdata -o "-p 59530 -k /tmp/kb1 -c listen_addresses=127.0.0.1" start
 *   createdb -h 127.0.0.1 -p 59530 -U postgres sweep_guard_test
 *   KGW_GUARD_TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:59530/sweep_guard_test \
 *     npx vitest run tests/integration/kala_gochara_windows_generation_guard.db.test.ts
 */
import { describe, it, expect, beforeAll, afterAll, beforeEach } from 'vitest'
import { Pool, type PoolClient } from 'pg'
import fs from 'fs'
import path from 'path'

const TEST_DB_URL = process.env.KGW_GUARD_TEST_DATABASE_URL

// Fixture chart_ids — the `0000…00aa` idiom used by the sibling suite, so they
// can never collide with a real chart_id.
const CHART_A = '00000000-0000-4000-8000-0000000000aa'
const CHART_B = '00000000-0000-4000-8000-0000000000bb'
// A chart that no protection registry ever listed — the cb73cd3d… case.
const CHART_UNREGISTERED = '00000000-0000-4000-8000-0000000000cc'

const GEN_V1 = 'v1'
const GEN_PROD = '3.0'

const MIGRATION_1071_PATH = path.resolve(
  __dirname, '../../migrations/1071_kala_gochara_windows_generation_guard.sql'
)

let pool: Pool

async function insertWindowRow(chartId: string, n: number, generation: string): Promise<number> {
  const day = String((n % 27) + 1).padStart(2, '0')
  const res = await pool.query<{ id: string }>(
    `INSERT INTO kala_gochara_windows
       (chart_id, event_class, temporal_shape, window_start, window_end,
        peak_date, signed_intensity, raw_intensity, valence, is_adverse, generation)
     VALUES ($1, 'test_event', 'point', $2, $2, $2, 1.0, 1.0, 'neutral', false, $3)
     RETURNING id`,
    [chartId, `2020-01-${day}`, generation]
  )
  return parseInt(res.rows[0]!.id, 10)
}

async function countRows(chartId: string, generation?: string): Promise<number> {
  const res = generation
    ? await pool.query<{ count: string }>(
        'SELECT COUNT(*)::text AS count FROM kala_gochara_windows WHERE chart_id=$1 AND generation=$2',
        [chartId, generation])
    : await pool.query<{ count: string }>(
        'SELECT COUNT(*)::text AS count FROM kala_gochara_windows WHERE chart_id=$1', [chartId])
  return parseInt(res.rows[0]!.count, 10)
}

/** Run `fn` with the override GUC SET LOCAL — the production opt-in exactly:
 *  transaction-scoped, auto-resetting, never a standing session setting. */
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

describe.skipIf(!TEST_DB_URL)('migration 1071 — kala_gochara_windows generation guard (live DB)', () => {
  beforeAll(async () => {
    if (!/sweep_guard_test|kala_guard_test/.test(TEST_DB_URL!)) {
      throw new Error(
        'KGW_GUARD_TEST_DATABASE_URL must point at a disposable database named ' +
        '`sweep_guard_test` or `kala_guard_test`. This suite creates and drops ' +
        'schema objects and must never run against production.'
      )
    }

    pool = new Pool({ connectionString: TEST_DB_URL })

    // Faithful-enough kala_gochara_windows: every NOT-NULL-without-DEFAULT column
    // production declares, plus `generation TEXT NOT NULL DEFAULT 'v1'` exactly as
    // migration 556 left it. The default matters — a row inserted without a
    // generation lands as v1 and is therefore protected.
    await pool.query(`
      DROP TABLE IF EXISTS kala_gochara_windows CASCADE;
      DROP FUNCTION IF EXISTS kala_gochara_windows_generation_guard_row() CASCADE;
      DROP FUNCTION IF EXISTS kala_gochara_windows_generation_guard_truncate() CASCADE;

      CREATE TABLE kala_gochara_windows (
        id BIGSERIAL PRIMARY KEY,
        chart_id UUID NOT NULL,
        event_class TEXT NOT NULL,
        temporal_shape TEXT NOT NULL CHECK (temporal_shape IN ('point','interval','chain')),
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
        generation TEXT NOT NULL DEFAULT 'v1',
        era_slice_key TEXT
      );
    `)

    // A v1 row must exist BEFORE the migration runs, so the migration's own
    // behavioural self-test genuinely executes rather than taking its honest skip.
    await insertWindowRow(CHART_A, 90, GEN_V1)

    // Execute the REAL migration file — what ships is what is under test.
    await pool.query(fs.readFileSync(MIGRATION_1071_PATH, 'utf8'))
  })

  afterAll(async () => {
    if (!pool) return
    await pool.query(`
      DROP TABLE IF EXISTS kala_gochara_windows CASCADE;
      DROP FUNCTION IF EXISTS kala_gochara_windows_generation_guard_row() CASCADE;
      DROP FUNCTION IF EXISTS kala_gochara_windows_generation_guard_truncate() CASCADE;
    `)
    await pool.end()
  })

  beforeEach(async () => {
    await withOverride(c => c.query('TRUNCATE kala_gochara_windows RESTART IDENTITY'))
    await insertWindowRow(CHART_A, 1, GEN_V1)
    await insertWindowRow(CHART_A, 2, GEN_V1)
    await insertWindowRow(CHART_A, 3, GEN_PROD)
    await insertWindowRow(CHART_B, 4, GEN_V1)
    await insertWindowRow(CHART_UNREGISTERED, 5, GEN_V1)
  })

  it('(0) both triggers are installed on kala_gochara_windows', async () => {
    const res = await pool.query<{ tgname: string }>(
      `SELECT t.tgname FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid
        WHERE c.relname = 'kala_gochara_windows' AND NOT t.tgisinternal
        ORDER BY t.tgname`
    )
    expect(res.rows.map(r => r.tgname)).toEqual([
      'trg_kala_gochara_windows_generation_guard_row',
      'trg_kala_gochara_windows_generation_guard_truncate',
    ])
  })

  it('(a) the exact DELETE the Clear route derives from the retired sweep count_sql is REFUSED', async () => {
    // Verbatim from production asset_registry.ka_gochara_sweep.count_sql, passed
    // through deriveDeleteSqlFromCountSql — this is the live vector, not a proxy.
    await expect(
      pool.query(
        "DELETE FROM kala_gochara_windows WHERE chart_id=$1 AND generation='v1'", [CHART_A])
    ).rejects.toThrow(/BUILD-PROTECTED/)
    expect(await countRows(CHART_A, GEN_V1)).toBe(2)
  })

  it('(b) a v1 DELETE is refused for a chart NO protection registry ever listed', async () => {
    // The fail-open hole in migration 540's registry-keyed guard. Production
    // holds 2,667 v1 rows for exactly such a chart.
    const before = await countRows(CHART_UNREGISTERED, GEN_V1)
    await expect(
      pool.query('DELETE FROM kala_gochara_windows WHERE chart_id=$1', [CHART_UNREGISTERED])
    ).rejects.toThrow(/BUILD-PROTECTED/)
    expect(await countRows(CHART_UNREGISTERED, GEN_V1)).toBe(before)
  })

  it('(c) a v1 UPDATE is refused too — not just DELETE', async () => {
    await expect(
      pool.query(
        "UPDATE kala_gochara_windows SET valence='gain' WHERE chart_id=$1 AND generation='v1'",
        [CHART_A])
    ).rejects.toThrow(/BUILD-PROTECTED/)
  })

  it('(d) a GENERATION-BLIND per-chart DELETE is refused and removes NOTHING, gen-3.0 included', async () => {
    // The fence the W0 field-contract register names: v1 and century v3 coexist
    // in this table, so a generation-blind statement is forbidden. The v1 rule
    // aborts the whole statement, so the 3.0 row survives as a side effect.
    await expect(
      pool.query('DELETE FROM kala_gochara_windows WHERE chart_id=$1', [CHART_A])
    ).rejects.toThrow(/BUILD-PROTECTED/)
    expect(await countRows(CHART_A, GEN_V1)).toBe(2)
    expect(await countRows(CHART_A, GEN_PROD)).toBe(1)
  })

  it('(e) the century materializer\'s generation-pinned gen-3.0 DELETE is ALLOWED — no Defect D-02', async () => {
    // `writers/ka_gochara_v3_century_materialize.py:2257` shape. If this test
    // ever goes red, the guard has become the outage migration 588 removed.
    await pool.query(
      "DELETE FROM kala_gochara_windows WHERE chart_id=$1 AND generation='3.0'", [CHART_A])
    expect(await countRows(CHART_A, GEN_PROD)).toBe(0)
    expect(await countRows(CHART_A, GEN_V1)).toBe(2)   // untouched
  })

  it('(f) a gen-3.0 UPDATE is allowed', async () => {
    await pool.query(
      "UPDATE kala_gochara_windows SET valence='gain' WHERE chart_id=$1 AND generation='3.0'",
      [CHART_A])
    expect(await countRows(CHART_A, GEN_PROD)).toBe(1)
  })

  it('(g) TRUNCATE is refused unconditionally — it is always generation-blind', async () => {
    await expect(pool.query('TRUNCATE kala_gochara_windows'))
      .rejects.toThrow(/BUILD-PROTECTED/)
    expect(await countRows(CHART_A)).toBe(3)
  })

  it('(h) INSERT is never gated, v1 included', async () => {
    await insertWindowRow(CHART_A, 6, GEN_V1)
    expect(await countRows(CHART_A, GEN_V1)).toBe(3)
  })

  it('(i) the override releases the guard for one transaction only', async () => {
    await withOverride(c =>
      c.query("DELETE FROM kala_gochara_windows WHERE chart_id=$1 AND generation='v1'", [CHART_A]))
    expect(await countRows(CHART_A, GEN_V1)).toBe(0)
    // ...and the very next ordinary statement is guarded again.
    await expect(
      pool.query("DELETE FROM kala_gochara_windows WHERE chart_id=$1 AND generation='v1'", [CHART_B])
    ).rejects.toThrow(/BUILD-PROTECTED/)
  })

  it('(j) an unrelated chart\'s gen-3.0-only rows are wholly unaffected by the guard', async () => {
    await insertWindowRow(CHART_B, 7, GEN_PROD)
    await pool.query(
      "DELETE FROM kala_gochara_windows WHERE chart_id=$1 AND generation='3.0'", [CHART_B])
    expect(await countRows(CHART_B, GEN_PROD)).toBe(0)
  })

  it('(k) re-applying migration 1071 is a clean no-op — idempotency, against the real file', async () => {
    await pool.query(fs.readFileSync(MIGRATION_1071_PATH, 'utf8'))
    const res = await pool.query<{ n: string }>(
      `SELECT COUNT(*)::text AS n FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid
        WHERE c.relname='kala_gochara_windows' AND NOT t.tgisinternal`)
    expect(res.rows[0]!.n).toBe('2')
    // Still refusing after the re-run — a re-apply that silently disarmed the
    // guard would be exactly the no-op-completion defect §N.8 names.
    await expect(
      pool.query("DELETE FROM kala_gochara_windows WHERE chart_id=$1 AND generation='v1'", [CHART_A])
    ).rejects.toThrow(/BUILD-PROTECTED/)
  })
})
