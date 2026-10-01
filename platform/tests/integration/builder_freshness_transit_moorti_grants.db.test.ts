// @vitest-environment node
/**
 * Suvarṇa grant v1.4 — migration 1217: data_plane_builder INSERT + UPDATE on
 * public.asset_freshness and public.bg_transit_moorti.
 *
 * The two production failures this migration fixes (verified read-only as
 * suvarna_reader, 2026-10-01):
 *   (a) the pipeline's receipt/freshness path upserts asset_freshness on every
 *       asset completion and every delta-skip (provenance.py _upsert_freshness_row),
 *       but data_plane_builder held SELECT only on it;
 *   (b) the bg_transit_rules / bg_transit_engine L0 seed writer upserts
 *       bg_transit_moorti as its last step (brahmagyan/l0_transit.py), but
 *       data_plane_builder held SELECT only on it.
 *
 * Proof shape (same as the 1211 suite): a role created with EXACTLY the builder's
 * relevant production grants (USAGE on schema public, SELECT on both tables,
 * nothing else) runs the REAL upsert statements — extracted verbatim from the
 * on-disk Python sources, not hand-copied (§N.8: the detector measures the claim
 * it asserts, not a proxy) — and must FAIL before migration 1217 and SUCCEED after
 * the REAL 1217 file is applied, issued by the table OWNER (a non-superuser role
 * with no CREATE on schema public, mirroring the amjis_app runner). Idempotency
 * and no-widening controls follow.
 *
 * Requires a THROWAWAY database. Skipped unless M1217_BUILDER_GRANT_TEST_DATABASE_URL
 * is set, and refuses anything not named `m1217_builder_grant_test` — this suite
 * creates and drops tables and roles and must never touch production.
 *
 *   createdb -h 127.0.0.1 -p 55432 -U postgres m1217_builder_grant_test
 *   M1217_BUILDER_GRANT_TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:55432/m1217_builder_grant_test \
 *     npx vitest run tests/integration/builder_freshness_transit_moorti_grants.db.test.ts
 */
import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { Pool } from 'pg'
import fs from 'fs'
import path from 'path'

const TEST_DB_URL = process.env.M1217_BUILDER_GRANT_TEST_DATABASE_URL

const GRANT_MIGRATION_PATH = path.resolve(
  __dirname,
  '../../migrations/1217_suvarna_builder_freshness_and_transit_moorti_grants.sql'
)
const MOORTI_DDL_MIGRATION_PATH = path.resolve(
  __dirname,
  '../../supabase/migrations/401_bg_transit_moorti.sql'
)
const RECEIPTS_DDL_MIGRATION_PATH = path.resolve(
  __dirname,
  '../../supabase/migrations/596_nirmana_provenance_receipts.sql'
)
const PROVENANCE_PY_PATH = path.resolve(
  __dirname,
  '../../python-sidecar/pipeline/orchestrator/provenance.py'
)
const L0_TRANSIT_PY_PATH = path.resolve(__dirname, '../../python-sidecar/brahmagyan/l0_transit.py')

const BUILDER_ROLE = 'data_plane_builder'
const OWNER_ROLE = 'm1217_table_owner'
const CHART = '00000000-0000-4000-8000-0000000000cd'
const ASSET = '_t_m1217_asset'

/** psycopg `%s` placeholders -> node-postgres `$n`. */
function toPg(sql: string): string {
  let i = 0
  return sql.replace(/%s/g, () => `$${++i}`)
}

/** The exact statement text between `INSERT INTO <table>` and the closing triple quote. */
function extractUpsert(pyPath: string, table: string): string {
  const src = fs.readFileSync(pyPath, 'utf8')
  const m = src.match(new RegExp(`INSERT INTO ${table}\\b[\\s\\S]*?(?="""\\s*,)`))
  if (!m) throw new Error(`could not locate the INSERT INTO ${table} statement in ${pyPath}`)
  return toPg(m[0])
}

/** The real asset_freshness DDL, taken verbatim from migration 596. */
function extractFreshnessDdl(): string {
  const src = fs.readFileSync(RECEIPTS_DDL_MIGRATION_PATH, 'utf8')
  const m = src.match(/CREATE TABLE IF NOT EXISTS asset_freshness \([\s\S]*?\n\);/)
  if (!m) throw new Error('could not locate the asset_freshness DDL in migration 596')
  return m[0]
}

const FRESHNESS_UPSERT = (() => {
  // ON CONFLICT list and params as written in provenance.py (:205-214).
  return extractUpsert(PROVENANCE_PY_PATH, 'asset_freshness')
})()
const MOORTI_UPSERT = extractUpsert(L0_TRANSIT_PY_PATH, 'bg_transit_moorti')

let pool: Pool

/** Run `fn` on a connection AS the builder-mirror role, inside a rolled-back transaction by default. */
type Q = (sql: string, params?: unknown[]) => Promise<{ rows: Record<string, unknown>[]; rowCount: number | null }>

async function asBuilder<T>(fn: (q: Q) => Promise<T>, commit = false): Promise<T> {
  const client = await pool.connect()
  try {
    await client.query('BEGIN')
    await client.query(`SET LOCAL ROLE ${BUILDER_ROLE}`)
    const out = await fn((sql, params) => client.query(sql, params))
    await client.query(commit ? 'COMMIT' : 'ROLLBACK')
    return out
  } catch (error) {
    await client.query('ROLLBACK').catch(() => {})
    throw error
  } finally {
    client.release()
  }
}

const freshnessParams = (chart: string | null, state: string, reasons: string[]) => [
  ASSET, chart, 'whole_asset', state, JSON.stringify(reasons), 'v1',
]
const moortiParams = (offset: number, name: string, tier: number, brief: string) => [
  offset, name, tier, brief, 'Phaladeepika Ch.26 §moorti-nirnaya', null,
]

async function applyMigrationAsOwner() {
  const client = await pool.connect()
  try {
    await client.query('BEGIN')
    await client.query(`SET LOCAL ROLE ${OWNER_ROLE}`)
    await client.query(fs.readFileSync(GRANT_MIGRATION_PATH, 'utf8'))
    await client.query('COMMIT')
  } catch (error) {
    await client.query('ROLLBACK').catch(() => {})
    throw error
  } finally {
    client.release()
  }
}

describe.skipIf(!TEST_DB_URL)('migration 1217 — builder grants on asset_freshness + bg_transit_moorti — live DB', () => {
  beforeAll(async () => {
    if (!/m1217_builder_grant_test/.test(TEST_DB_URL!)) {
      throw new Error(
        'M1217_BUILDER_GRANT_TEST_DATABASE_URL must point at a disposable database named ' +
          '`m1217_builder_grant_test`. This suite creates and drops tables and roles ' +
          'and must never run against production.'
      )
    }
    pool = new Pool({ connectionString: TEST_DB_URL })

    await pool.query(`
      DROP TABLE IF EXISTS asset_freshness, bg_transit_moorti, charts, asset_registry CASCADE;
      DO $cleanup$ BEGIN
        IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '${BUILDER_ROLE}') THEN
          EXECUTE 'REVOKE ALL ON SCHEMA public FROM ${BUILDER_ROLE}';
        END IF;
        IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '${OWNER_ROLE}') THEN
          EXECUTE 'REVOKE ALL ON SCHEMA public FROM ${OWNER_ROLE}';
        END IF;
      END $cleanup$;
      DROP ROLE IF EXISTS ${BUILDER_ROLE};
      DROP ROLE IF EXISTS ${OWNER_ROLE};

      -- Minimal parents for asset_freshness's two real foreign keys.
      CREATE TABLE asset_registry (asset_id text PRIMARY KEY);
      CREATE TABLE charts (id uuid PRIMARY KEY);
      INSERT INTO asset_registry VALUES ('${ASSET}');
      INSERT INTO charts VALUES ('${CHART}');
    `)

    // The REAL table DDL from migrations 596 (asset_freshness) and 401 (bg_transit_moorti,
    // including its 27 seed rows).
    await pool.query(extractFreshnessDdl())
    await pool.query(fs.readFileSync(MOORTI_DDL_MIGRATION_PATH, 'utf8'))

    // Owner mirrors amjis_app: owns both tables, NO CREATE on schema public.
    // Builder mirrors data_plane_builder's production ACL on these two tables
    // (relacl: r = SELECT only) and holds zero role memberships.
    await pool.query(`
      CREATE ROLE ${OWNER_ROLE} NOLOGIN;
      CREATE ROLE ${BUILDER_ROLE} NOLOGIN;
      ALTER TABLE asset_freshness OWNER TO ${OWNER_ROLE};
      ALTER TABLE bg_transit_moorti OWNER TO ${OWNER_ROLE};
      GRANT USAGE ON SCHEMA public TO ${OWNER_ROLE}, ${BUILDER_ROLE};
      GRANT SELECT ON asset_freshness, bg_transit_moorti TO ${BUILDER_ROLE};
    `)
  })

  afterAll(async () => {
    if (!pool) return
    await pool.query(`
      DROP TABLE IF EXISTS asset_freshness, bg_transit_moorti, charts, asset_registry CASCADE;
      REVOKE ALL ON SCHEMA public FROM ${BUILDER_ROLE};
      REVOKE ALL ON SCHEMA public FROM ${OWNER_ROLE};
      DROP ROLE IF EXISTS ${BUILDER_ROLE};
      DROP ROLE IF EXISTS ${OWNER_ROLE};
    `)
    await pool.end()
  })

  it('extracted the real upsert statements from source (drift guard)', () => {
    expect(FRESHNESS_UPSERT).toMatch(/INSERT INTO asset_freshness[\s\S]*ON CONFLICT \(asset_id, scope_key, partition_key\) DO UPDATE SET/)
    expect(FRESHNESS_UPSERT).toMatch(/\$6/)
    expect(MOORTI_UPSERT).toMatch(/INSERT INTO bg_transit_moorti[\s\S]*ON CONFLICT \(nakshatra_offset\) DO UPDATE SET/)
    expect(MOORTI_UPSERT).toMatch(/\$6/)
  })

  it('baseline: the builder-mirror role can read both tables but not write (production state today)', async () => {
    const n = await asBuilder(async (q) => (await q('SELECT count(*)::int AS n FROM bg_transit_moorti')).rows[0]!.n)
    expect(n).toBe(27)
    await asBuilder((q) => q('SELECT count(*) FROM asset_freshness'))
    const privs = await pool.query(
      `SELECT has_table_privilege($1,'public.asset_freshness','INSERT') AS af_i,
              has_table_privilege($1,'public.asset_freshness','UPDATE') AS af_u,
              has_table_privilege($1,'public.bg_transit_moorti','INSERT') AS mo_i,
              has_table_privilege($1,'public.bg_transit_moorti','UPDATE') AS mo_u`,
      [BUILDER_ROLE]
    )
    expect(privs.rows[0]).toEqual({ af_i: false, af_u: false, mo_i: false, mo_u: false })
  })

  it('FAILS BEFORE (a): the real asset_freshness upsert is denied for the builder', async () => {
    await expect(
      asBuilder((q) => q(FRESHNESS_UPSERT, freshnessParams(CHART, 'fresh', [])))
    ).rejects.toThrow(/permission denied for table asset_freshness/)
  })

  it('FAILS BEFORE (b): the real bg_transit_moorti upsert is denied for the builder', async () => {
    await expect(
      asBuilder((q) => q(MOORTI_UPSERT, moortiParams(1, 'swarna', 1, 'x')))
    ).rejects.toThrow(/permission denied for table bg_transit_moorti/)
  })

  it('SUCCEEDS AFTER: applying the REAL 1217 file as the table owner lets both real upserts land', async () => {
    await applyMigrationAsOwner()

    await asBuilder(async (q) => {
      // asset_freshness: global (NULL chart) insert, chart-scoped insert, then both ON CONFLICT updates.
      await q(FRESHNESS_UPSERT, freshnessParams(null, 'unknown', ['receipt_missing']))
      await q(FRESHNESS_UPSERT, freshnessParams(CHART, 'fresh', []))
      await q(FRESHNESS_UPSERT, freshnessParams(CHART, 'stale', ['code_digest_changed']))
      await q(FRESHNESS_UPSERT, freshnessParams(null, 'fresh', []))
      // bg_transit_moorti: update of an existing seed row (the rebuild path) and a re-assert.
      await q(MOORTI_UPSERT, moortiParams(5, 'swarna', 1, 'rebuilt-by-builder'))
    }, true)

    const af = await pool.query(
      `SELECT scope_key, freshness_state, reasons FROM asset_freshness ORDER BY chart_id NULLS LAST`
    )
    expect(af.rows).toEqual([
      { scope_key: CHART, freshness_state: 'stale', reasons: ['code_digest_changed'] },
      { scope_key: '__global__', freshness_state: 'fresh', reasons: [] },
    ])
    const mo = await pool.query(`SELECT phala_brief FROM bg_transit_moorti WHERE nakshatra_offset = 5`)
    expect(mo.rows[0].phala_brief).toBe('rebuilt-by-builder')
  })

  it('the builder can also INSERT a new moorti key (first-seed path) and the row-level CHECKs still bind', async () => {
    await pool.query(`DELETE FROM bg_transit_moorti WHERE nakshatra_offset = 27`) // as superuser, to re-create the insert path
    await asBuilder((q) => q(MOORTI_UPSERT, moortiParams(27, 'tamra', 3, 'reinserted')), true)
    const row = await pool.query(`SELECT moorti_name FROM bg_transit_moorti WHERE nakshatra_offset = 27`)
    expect(row.rows[0].moorti_name).toBe('tamra')
    await expect(
      asBuilder((q) => q(MOORTI_UPSERT, moortiParams(5, 'copper', 1, 'bad name')))
    ).rejects.toThrow(/bg_transit_moorti_moorti_name_check/)
  })

  it('idempotent: applying migration 1217 a second time is a no-op and the builder path still works', async () => {
    await applyMigrationAsOwner()
    await asBuilder((q) => q(FRESHNESS_UPSERT, freshnessParams(CHART, 'fresh', [])), true)
    const r = await pool.query(`SELECT freshness_state FROM asset_freshness WHERE scope_key = $1`, [CHART])
    expect(r.rows[0].freshness_state).toBe('fresh')
  })

  it('scope: grants exactly INSERT + UPDATE — no DELETE/TRUNCATE/TRIGGER/REFERENCES, no CREATE, no grant option', async () => {
    const p = await pool.query(
      `SELECT t.tab,
              has_table_privilege($1, t.tab, 'SELECT')     AS s,
              has_table_privilege($1, t.tab, 'INSERT')     AS i,
              has_table_privilege($1, t.tab, 'UPDATE')     AS u,
              has_table_privilege($1, t.tab, 'DELETE')     AS d,
              has_table_privilege($1, t.tab, 'TRUNCATE')   AS tr,
              has_table_privilege($1, t.tab, 'TRIGGER')    AS tg,
              has_table_privilege($1, t.tab, 'REFERENCES') AS rf,
              has_table_privilege($1, t.tab, 'INSERT WITH GRANT OPTION') AS gi
         FROM (VALUES ('public.asset_freshness'), ('public.bg_transit_moorti')) t(tab) ORDER BY 1`,
      [BUILDER_ROLE]
    )
    for (const row of p.rows) {
      expect(row).toMatchObject({ s: true, i: true, u: true, d: false, tr: false, tg: false, rf: false, gi: false })
    }
    const schema = await pool.query(`SELECT has_schema_privilege($1, 'public', 'CREATE') AS c`, [BUILDER_ROLE])
    expect(schema.rows[0].c).toBe(false)
    const members = await pool.query(
      `SELECT count(*)::int AS n FROM pg_auth_members m JOIN pg_roles r ON r.oid = m.member WHERE r.rolname = $1`,
      [BUILDER_ROLE]
    )
    expect(members.rows[0].n).toBe(0)

    // Behavioural: DELETE and TRUNCATE are still refused.
    await expect(asBuilder((q) => q(`DELETE FROM asset_freshness`))).rejects.toThrow(/permission denied for table asset_freshness/)
    await expect(asBuilder((q) => q(`DELETE FROM bg_transit_moorti`))).rejects.toThrow(/permission denied for table bg_transit_moorti/)
    await expect(asBuilder((q) => q(`TRUNCATE bg_transit_moorti`))).rejects.toThrow(/permission denied for table bg_transit_moorti/)
  })

  it('no sequence is needed: neither table owns one', async () => {
    const r = await pool.query(`
      SELECT count(*)::int AS n FROM pg_depend d
        JOIN pg_class s ON s.oid = d.objid AND s.relkind = 'S'
        JOIN pg_class t ON t.oid = d.refobjid
       WHERE d.deptype IN ('a','i') AND t.relname IN ('asset_freshness','bg_transit_moorti')`)
    expect(r.rows[0].n).toBe(0)
  })
})
