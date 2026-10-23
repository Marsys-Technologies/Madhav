// @vitest-environment node
/**
 * Owner step 1 fix (2026-10-21, SR-STEP1-MIGRATOR-SETROLE): the data-plane deploy gate (platform/scripts/data-plane-ownership-status.ts) must TOLERATE — and only
 * tolerate — what `gochara-provision-roles.sh` stage `grant-l1-reads` leaves behind, otherwise the first deploy after step 1 stops on "Protected table ACL allowlist
 * drift" / "Public schema ACL allowlist drift" (STEP1_DIAG §3 F2; the precedents are #2756 suvarna_reader and #3366 verifier_principal).
 *
 * The allowlist, exactly: gochara_verifier and gochara_sealer, SELECT (never grantable) on public.chart_facts and public.chart_dashas, and USAGE (never CREATE, never
 * grantable) on schema public. Nothing else. A THIRD grantee, a grantable SELECT, a write privilege, a third L1 table, or CREATE on public must still FAIL the gate.
 *
 * Proof shape (same as builder_freshness_transit_moorti_grants.db.test.ts): the two ACL statements are extracted VERBATIM from the on-disk gate source (§N.8: the detector
 * measures the claim it asserts, not a hand-copied proxy) and run against a throwaway database whose public schema and L1 tables carry the post-cutover ACL
 * (data-plane-ownership-preflight.ts:215-322): the baseline reads SAFE, then each planted drift reads UNSAFE.
 *
 * Needs a DISPOSABLE cluster. Skipped unless GOCHARA_ACL_GATE_TEST_ADMIN_URL is set — a superuser, loopback-only URL naming the maintenance database `postgres`. The suite
 * creates its OWN database (gochara_acl_gate_test_<pid>), refuses to reuse one, and drops it (and the roles it created) afterwards; it never touches any other database.
 *
 *   GOCHARA_ACL_GATE_TEST_ADMIN_URL=postgresql://postgres@127.0.0.1:55433/postgres \
 *     node_modules/.bin/vitest run tests/integration/data_plane_gochara_acl_gate.db.test.ts
 */
import fs from 'node:fs'
import path from 'node:path'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'
import { Pool } from 'pg'
import { L1_ACTIVE_TABLES, L2_ACTIVE_TABLES } from '../../scripts/data-plane-ownership-preflight'
import { acquireClusterRoleLock, ensureRole } from './builder_role_fixture'

const ADMIN_URL = process.env.GOCHARA_ACL_GATE_TEST_ADMIN_URL
const DB_NAME = `gochara_acl_gate_test_${process.pid}`
if (ADMIN_URL) {
  const u = new URL(ADMIN_URL)
  if (!['127.0.0.1', 'localhost', '[::1]'].includes(u.hostname) || u.pathname !== '/postgres' || u.search) {
    throw new Error('GOCHARA_ACL_GATE_TEST_ADMIN_URL must be a plain loopback URL naming the maintenance database postgres.')
  }
}
const dbUrl = (): string => { const u = new URL(ADMIN_URL!); u.pathname = `/${DB_NAME}`; return u.toString() }

const STATUS_SRC = fs.readFileSync(path.resolve(__dirname, '../../scripts/data-plane-ownership-status.ts'), 'utf8')

/** The statement text and parameter expression of `const <name> = await pool.query<...>(`...`, [params])` in the gate source. */
function extractGateQuery(name: string): { sql: string; params: string } {
  const m = STATUS_SRC.match(new RegExp(`const ${name} = await pool\\.query<[^>]*>\\(\`([\\s\\S]*?)\`(?:,\\s*(\\[[\\s\\S]*?\\]))?\\)\\n`))
  if (!m) throw new Error(`could not locate the ${name} query in data-plane-ownership-status.ts`)
  return { sql: m[1], params: (m[2] ?? '').replace(/\s+/g, ' ') }
}

const TABLE_GATE = extractGateQuery('aclSurface')
const SCHEMA_GATE = extractGateQuery('schemaAcl')
const TABLE_PARAMS = [[...L1_ACTIVE_TABLES], [...L1_ACTIVE_TABLES, ...L2_ACTIVE_TABLES]]

const SHARED_ROLES = [
  'data_plane_builder', 'data_plane_verifier', 'data_plane_migrator', 'amjis_app', 'role_web_serve',
  'data_plane_schema_owner', 'data_plane_l1_owner', 'data_plane_l2_owner',
] as const
const GOCHARA = ['gochara_verifier', 'gochara_sealer'] as const
const THIRD = 'gochara_acl_gate_third_grantee'
const LAYER_VERIFIER = 'verifier_principal'      // O-W56-C: the Kāla role gochara-provision-roles.sh stage layer-verifier-credential makes able to log in
const TABLES = ['chart_facts', 'chart_dashas'] as const

describe.skipIf(!ADMIN_URL)('data-plane deploy gate — Gochara verifier/sealer L1-read tolerance is exact', () => {
  let admin: Pool
  let pool: Pool
  let release: (() => Promise<void>) | undefined
  const createdByThisRun: string[] = []

  /** true = the gate would STOP the deploy (the statement's `unsafe` column). */
  const tableGateUnsafe = async () => (await pool.query<{ unsafe: boolean }>(TABLE_GATE.sql, TABLE_PARAMS)).rows[0].unsafe
  const schemaGateUnsafe = async () => (await pool.query<{ unsafe: boolean }>(SCHEMA_GATE.sql)).rows[0].unsafe

  async function reset(): Promise<void> {
    for (const r of [...GOCHARA, THIRD]) {
      await pool.query(`REVOKE ALL ON public.chart_facts, public.chart_dashas, public.chart_divisionals FROM ${r}`)
      await pool.query(`REVOKE ALL ON SCHEMA public FROM ${r}`)
    }
  }

  beforeAll(async () => {
    admin = new Pool({ connectionString: ADMIN_URL })
    release = await acquireClusterRoleLock(ADMIN_URL!)
    if ((await admin.query('SELECT 1 FROM pg_database WHERE datname=$1', [DB_NAME])).rowCount) throw new Error(`${DB_NAME} already exists: refusing to reuse a database this run did not create`)
    await admin.query(`CREATE DATABASE ${DB_NAME}`)
    pool = new Pool({ connectionString: dbUrl() })
    for (const r of [...SHARED_ROLES, ...GOCHARA, THIRD, LAYER_VERIFIER]) {
      const existed = (await admin.query('SELECT 1 FROM pg_roles WHERE rolname=$1', [r])).rowCount
      if (!existed && !(SHARED_ROLES as readonly string[]).includes(r)) createdByThisRun.push(r)
      await ensureRole(admin, r)
    }
    // the post-cutover surface (preflight.ts:215-322): schema public owned by the schema owner, PUBLIC revoked, the fixed USAGE list, L1/L2 owners also CREATE
    await pool.query(`
      ALTER SCHEMA public OWNER TO data_plane_schema_owner;
      REVOKE ALL ON SCHEMA public FROM PUBLIC;
      GRANT USAGE, CREATE ON SCHEMA public TO data_plane_l1_owner, data_plane_l2_owner;
      GRANT USAGE ON SCHEMA public TO data_plane_migrator, data_plane_builder, data_plane_verifier, amjis_app, role_web_serve;
      DO $$ DECLARE r text; BEGIN
        FOREACH r IN ARRAY ARRAY['purna_inquiry_owner','suvarna_reader','verifier_principal'] LOOP
          IF to_regrole(r) IS NOT NULL THEN EXECUTE format('GRANT USAGE ON SCHEMA public TO %I', r); END IF;   -- the gate REQUIRES these once they exist (shared cluster)
        END LOOP;
      END $$;
    `)
    for (const t of [...TABLES, 'chart_divisionals']) {
      await pool.query(`
        DROP TABLE IF EXISTS public.${t};
        CREATE TABLE public.${t} (id int);
        ALTER TABLE public.${t} OWNER TO data_plane_l1_owner;
        GRANT SELECT, INSERT, UPDATE, DELETE ON public.${t} TO data_plane_builder;
        GRANT SELECT ON public.${t} TO amjis_app, data_plane_verifier, data_plane_migrator, data_plane_l2_owner;
      `)
    }
    for (const r of [...GOCHARA, THIRD]) {
      await pool.query(`REVOKE ALL ON public.chart_facts, public.chart_dashas, public.chart_divisionals FROM ${r}; REVOKE ALL ON SCHEMA public FROM ${r}`)
    }
  })

  afterAll(async () => {
    try {
      await pool?.end()
      if (admin) {
        await admin.query(`DROP DATABASE IF EXISTS ${DB_NAME} WITH (FORCE)`)       // only the database this run created
        for (const r of [...createdByThisRun].reverse()) {
          await admin.query(`DROP ROLE IF EXISTS ${r}`).catch(() => {})            // best effort: a role another database still depends on stays (the cluster is disposable)
        }
      }
    } finally {
      await admin?.end()
      await release?.()
    }
  })

  it('extracts the gate statements verbatim and with the parameters this test assumes', () => {
    expect(TABLE_GATE.sql).toContain("a.grantee IN ('gochara_verifier','gochara_sealer')")
    expect(TABLE_GATE.params).toBe('[[...L1_ACTIVE_TABLES], [...L1_ACTIVE_TABLES, ...L2_ACTIVE_TABLES]]')
    expect(SCHEMA_GATE.sql).toContain("to_regrole(a.grantee) IS NOT NULL")
  })

  it('baseline: the post-cutover ACL with no Gochara grant reads SAFE (the tolerance is not a requirement)', async () => {
    await reset()
    expect(await tableGateUnsafe()).toBe(false)
    expect(await schemaGateUnsafe()).toBe(false)
  })

  it('TOLERATES exactly what grant-l1-reads grants: SELECT on chart_facts + chart_dashas and USAGE on public, for the verifier and the sealer, none grantable', async () => {
    await reset()
    await pool.query('GRANT SELECT ON public.chart_facts, public.chart_dashas TO gochara_verifier, gochara_sealer')
    await pool.query('GRANT USAGE ON SCHEMA public TO gochara_verifier, gochara_sealer')
    expect(await tableGateUnsafe()).toBe(false)
    expect(await schemaGateUnsafe()).toBe(false)
  })

  it('TOLERATES a partial application too (only the sealer, only the tables): tolerance is per grantee, never a requirement', async () => {
    await reset()
    await pool.query('GRANT SELECT ON public.chart_facts TO gochara_sealer')
    expect(await tableGateUnsafe()).toBe(false)
    expect(await schemaGateUnsafe()).toBe(false)
  })

  it('still FAILS the table gate for a THIRD grantee holding the same SELECT', async () => {
    await reset()
    await pool.query('GRANT SELECT ON public.chart_facts, public.chart_dashas TO gochara_verifier, gochara_sealer')
    await pool.query(`GRANT SELECT ON public.chart_facts TO ${THIRD}`)
    expect(await tableGateUnsafe()).toBe(true)
  })

  it('still FAILS the schema gate for a THIRD grantee holding USAGE on public', async () => {
    await reset()
    await pool.query('GRANT USAGE ON SCHEMA public TO gochara_verifier, gochara_sealer')
    await pool.query(`GRANT USAGE ON SCHEMA public TO ${THIRD}`)
    expect(await schemaGateUnsafe()).toBe(true)
  })

  it('still FAILS the table gate for a GRANTABLE SELECT (WITH GRANT OPTION)', async () => {
    await reset()
    await pool.query('GRANT SELECT ON public.chart_facts TO gochara_verifier WITH GRANT OPTION')
    expect(await tableGateUnsafe()).toBe(true)
  })

  it('still FAILS the schema gate for a GRANTABLE USAGE on public', async () => {
    await reset()
    await pool.query('GRANT USAGE ON SCHEMA public TO gochara_sealer WITH GRANT OPTION')
    expect(await schemaGateUnsafe()).toBe(true)
  })

  it('still FAILS the schema gate for CREATE on public (USAGE is tolerated, CREATE is not)', async () => {
    await reset()
    await pool.query('GRANT USAGE ON SCHEMA public TO gochara_verifier, gochara_sealer')
    await pool.query('GRANT CREATE ON SCHEMA public TO gochara_verifier')
    expect(await schemaGateUnsafe()).toBe(true)
  })

  it('still FAILS the table gate for any write privilege, and for SELECT on a third L1 table', async () => {
    await reset()
    await pool.query('GRANT SELECT, INSERT ON public.chart_facts TO gochara_verifier')
    expect(await tableGateUnsafe()).toBe(true)
    await reset()
    await pool.query('GRANT SELECT ON public.chart_divisionals TO gochara_sealer')
    expect(await tableGateUnsafe()).toBe(true)
  })

  // O-W56-C (M-W56-4): the post-stage state of gochara-provision-roles.sh stage `layer-verifier-credential`. The stage grants NOTHING — it only lets the Kāla role
  // verifier_principal log in (LOGIN, a password, CONNECTION LIMIT 4) — so the deploy gate needs no new allowance: the role's existing allowlist entry (USAGE on schema public, the
  // `verifier_principal` row of the schema gate) is all it holds on the protected surface, its receipt INSERT / column reads are on non-protected kala_* tables, and NOTHING
  // widened for it. Both claims are measured with the gate statements extracted verbatim from the on-disk source.
  describe('O-W56-C: verifier_principal after the layer-verifier-credential stage', () => {
    async function resetLv(): Promise<void> {
      await reset()                                                                     // the preceding tests above leave their last planted drift behind
      await pool.query(`REVOKE ALL ON public.chart_facts, public.chart_dashas, public.chart_divisionals FROM ${LAYER_VERIFIER}`)
      await pool.query(`REVOKE CREATE ON SCHEMA public FROM ${LAYER_VERIFIER}`)
      await pool.query(`GRANT USAGE ON SCHEMA public TO ${LAYER_VERIFIER}`)          // the schema gate REQUIRES this once the role exists
    }
    async function postStage(): Promise<void> {
      await resetLv()
      await pool.query('DROP TABLE IF EXISTS public.kala_layer_verification; CREATE TABLE public.kala_layer_verification (chart_id uuid, generation text, result text)')
      await pool.query(`GRANT INSERT ON public.kala_layer_verification TO ${LAYER_VERIFIER}; GRANT SELECT (chart_id, generation) ON public.kala_layer_verification TO ${LAYER_VERIFIER}`)
      if (createdByThisRun.includes(LAYER_VERIFIER)) {                                  // never alter a shared cluster's pre-existing role: the ACL gates do not read the login attributes
        await admin.query(`ALTER ROLE ${LAYER_VERIFIER} LOGIN PASSWORD 'lv-fixture-only' CONNECTION LIMIT 4`)
      }
    }
    afterAll(async () => { await pool.query('DROP TABLE IF EXISTS public.kala_layer_verification') })

    it('claim A1: the role as the stage leaves it (LOGIN, USAGE on public, the receipt INSERT and column reads on its kala table) reads SAFE on both ACL gates — nothing to allowlist', async () => {
      await postStage()
      expect(await tableGateUnsafe()).toBe(false)
      expect(await schemaGateUnsafe()).toBe(false)
      if (createdByThisRun.includes(LAYER_VERIFIER)) {
        const attrs = (await admin.query('SELECT rolcanlogin, rolconnlimit FROM pg_roles WHERE rolname=$1', [LAYER_VERIFIER])).rows[0]
        expect(attrs).toEqual({ rolcanlogin: true, rolconnlimit: 4 })
      }
    })
    it('claim A2: the allowlist did NOT widen for it — SELECT on an L1 table is still drift for verifier_principal (the Gochara tolerance names only gochara_verifier and gochara_sealer)', async () => {
      await postStage()
      await pool.query(`GRANT SELECT ON public.chart_facts TO ${LAYER_VERIFIER}`)
      expect(await tableGateUnsafe()).toBe(true)
      await resetLv()
      expect(await tableGateUnsafe()).toBe(false)
    })
    it('claim A3: CREATE on schema public is still drift for it (USAGE only), and losing USAGE is drift too (the schema gate requires it once the role exists)', async () => {
      await postStage()
      await pool.query(`GRANT CREATE ON SCHEMA public TO ${LAYER_VERIFIER}`)
      expect(await schemaGateUnsafe()).toBe(true)
      await resetLv()
      await pool.query(`REVOKE USAGE ON SCHEMA public FROM ${LAYER_VERIFIER}`)
      expect(await schemaGateUnsafe()).toBe(true)
      await resetLv()
      expect(await schemaGateUnsafe()).toBe(false)
    })
  })
})
