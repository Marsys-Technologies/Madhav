// @vitest-environment node
/**
 * Detector for the race-safe `data_plane_builder` fixture helpers
 * (builder_role_fixture.ts) — the merge_group failure of #3615/#3711 was
 * SQLSTATE 42710 "role data_plane_builder already exists" from two suites
 * creating the cluster-global role on one Postgres.
 *
 * Claims measured against a real cluster:
 *  1. ensureRole is idempotent and survives N concurrent callers (no 42710 /
 *     23505), leaving exactly one role.
 *  2. acquireClusterRoleLock is mutually exclusive across connections: a second
 *     holder is not admitted until the first releases.
 *
 * Requires a THROWAWAY database; shares the 1216 suite's variable so it rides
 * the same CI step (it only reads host/credentials from it and creates one
 * probe role, dropped afterwards):
 *   M1216_GOCHARA_GRANT_TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:55433/m1216_gochara_grant_test
 */
import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { Pool } from 'pg'
import { acquireClusterRoleLock, ensureRole } from './builder_role_fixture'

const TEST_DB_URL = process.env.M1216_GOCHARA_GRANT_TEST_DATABASE_URL
const PROBE_ROLE = 'zz_builder_role_fixture_probe'

describe.skipIf(!TEST_DB_URL)('builder_role_fixture — race-safe cluster-global role helpers — live DB', () => {
  let pool: Pool

  beforeAll(async () => {
    if (!/m1216_gochara_grant_test/.test(TEST_DB_URL!)) {
      throw new Error('M1216_GOCHARA_GRANT_TEST_DATABASE_URL must point at a disposable database named `m1216_gochara_grant_test*`.')
    }
    pool = new Pool({ connectionString: TEST_DB_URL, max: 12 })
    await pool.query(`DROP ROLE IF EXISTS ${PROBE_ROLE}`)
  })

  afterAll(async () => {
    if (!pool) return
    await pool.query(`DROP ROLE IF EXISTS ${PROBE_ROLE}`).catch(() => {})
    await pool.end()
  })

  it('ensureRole tolerates 12 concurrent creators and an already-present role', async () => {
    await Promise.all(Array.from({ length: 12 }, () => ensureRole(pool, PROBE_ROLE)))
    await ensureRole(pool, PROBE_ROLE)
    const { rows } = await pool.query(`SELECT count(*)::int AS n FROM pg_roles WHERE rolname = $1`, [PROBE_ROLE])
    expect(rows[0].n).toBe(1)
  })

  it('acquireClusterRoleLock admits one holder at a time', async () => {
    const releaseFirst = await acquireClusterRoleLock(TEST_DB_URL!)
    let secondAdmitted = false
    const second = acquireClusterRoleLock(TEST_DB_URL!).then(release => {
      secondAdmitted = true
      return release
    })
    await new Promise(r => setTimeout(r, 750))
    expect(secondAdmitted).toBe(false)
    await releaseFirst()
    const releaseSecond = await second
    expect(secondAdmitted).toBe(true)
    await releaseSecond()
  })
})
