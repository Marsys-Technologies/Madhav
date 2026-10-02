// @vitest-environment node
/**
 * Pravāha B6.0 — migration 1236: kala_gochara_authority refuses a governed ('5.x'+) generation — live disposable DB.
 * The table is created from the REAL migration 527 DDL (read from supabase/migrations), the guard from the real 1236 file. Requires
 * the throwaway database (GOCHARA_A51_TEST_DATABASE_URL, named gochara_a51_test).
 */
import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { Pool } from 'pg'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import { resolveDisposableA51Config } from './gochara_a5_1_disposable_url'

const TEST_DB_URL = process.env.GOCHARA_A51_TEST_DATABASE_URL
const MIG = path.resolve(process.cwd(), 'migrations/1236_gochara_authority_refuses_governed_generation.sql')
const DDL_527 = readFileSync(path.resolve(process.cwd(), 'supabase/migrations/527_kala_gochara_generation_authority.sql'), 'utf8')
const CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const CHART2 = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'
let pool: Pool
const refused = async (p: Promise<unknown>, re: RegExp): Promise<void> => { await expect(p).rejects.toThrow(re) }

describe.skipIf(!TEST_DB_URL)('B6.0 migration 1236 — authority refuses governed generations (live disposable DB)', () => {
  beforeAll(async () => {
    pool = new Pool({ ...resolveDisposableA51Config(TEST_DB_URL), max: 3 })
    await pool.query(`DROP TABLE IF EXISTS kala_gochara_authority CASCADE`)
    // only the authority table from 527 (the rest of 527 alters the windows table, absent here)
    const m = DDL_527.match(/CREATE TABLE IF NOT EXISTS kala_gochara_authority \([\s\S]*?\);/)
    expect(m).toBeTruthy()
    await pool.query(m![0])
    await pool.query(`INSERT INTO kala_gochara_authority (chart_id, authoritative_generation, flipped_by, evidence_ref) VALUES ($1,'3.0','t','e'),($2,'3.0','t','e')`, [CHART, CHART2])
  })
  afterAll(async () => { if (!pool) return; await pool.query(`DROP TABLE IF EXISTS kala_gochara_authority CASCADE`); await pool.end() })

  it('BEFORE 1236 nothing stops a governed generation becoming authoritative (the gap)', async () => {
    await pool.query(`UPDATE kala_gochara_authority SET authoritative_generation='5.0' WHERE chart_id=$1`, [CHART2])
    await refused(pool.query(readFileSync(MIG, 'utf8')), /already authoritative/)        // the gate refuses to apply over it
    await pool.query(`UPDATE kala_gochara_authority SET authoritative_generation='3.0' WHERE chart_id=$1`, [CHART2])
  })

  it('applies; a replay is refused', async () => {
    await pool.query(readFileSync(MIG, 'utf8'))
    await refused(pool.query(readFileSync(MIG, 'utf8')), /migration_1236_already_applied/)
  })

  it('legacy generations are unaffected: v1, 2.0, 3.0, 4.0, 4.1', async () => {
    for (const g of ['v1', '2.0', '3.0', '4.0', '4.1', '4.9']) {
      await pool.query(`UPDATE kala_gochara_authority SET authoritative_generation=$2 WHERE chart_id=$1`, [CHART, g])
    }
    await pool.query(`UPDATE kala_gochara_authority SET authoritative_generation='3.0' WHERE chart_id=$1`, [CHART])
  })

  it('every governed generation is refused, on UPDATE and INSERT, naming the constraint', async () => {
    for (const g of ['5.0', '5.1', '5.9', '6.0', '9.9', '10.0', '12.3'])
      await refused(pool.query(`UPDATE kala_gochara_authority SET authoritative_generation=$2 WHERE chart_id=$1`, [CHART, g]), /kga_governed_generation_refused_ck/)
    await pool.query(`DELETE FROM kala_gochara_authority WHERE chart_id=$1`, [CHART2])
    for (const g of ['5.0', '7.2', '10.0'])
      await refused(pool.query(`INSERT INTO kala_gochara_authority (chart_id, authoritative_generation) VALUES ($1,$2)`, [CHART2, g]), /kga_governed_generation_refused_ck/)
    expect((await pool.query(`SELECT authoritative_generation FROM kala_gochara_authority WHERE chart_id=$1`, [CHART])).rows[0].authoritative_generation).toBe('3.0')
  })

  it('no role and no session setting bypasses it (a CHECK, not a trigger)', async () => {
    const c = await pool.connect()
    try {
      await c.query(`SET session_replication_role = replica`)                                   // disables TRIGGERS; a CHECK still applies
      await refused(c.query(`UPDATE kala_gochara_authority SET authoritative_generation='5.0' WHERE chart_id=$1`, [CHART]), /kga_governed_generation_refused_ck/)
    } finally { await c.query(`SET session_replication_role = origin`).catch(() => undefined); c.release() }
  })

  it('the guard is a validated CHECK on the table (not NOT VALID)', async () => {
    const r = await pool.query<{ convalidated: boolean; contype: string }>(
      `SELECT convalidated, contype FROM pg_constraint WHERE conrelid='kala_gochara_authority'::regclass AND conname='kga_governed_generation_refused_ck'`)
    expect(r.rows).toEqual([{ convalidated: true, contype: 'c' }])
  })
})
