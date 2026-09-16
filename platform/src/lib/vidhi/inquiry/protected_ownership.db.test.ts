import { Pool } from 'pg'
import { afterAll, beforeAll, describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))

import {
  __resetInquiryStorePoolForTests,
  probeInquiryStoreReadiness,
} from './store_pool'

const adminDatabaseUrl = process.env.PURNA_PROTECTED_OWNER_ADMIN_DATABASE_URL
const serveDatabaseUrl = process.env.PURNA_PROTECTED_OWNER_SERVE_DATABASE_URL
const describeDisposable = adminDatabaseUrl && serveDatabaseUrl
  ? describe.sequential
  : describe.skip

const principalUid = 'purna-owner-replay-principal'
const principalKeyId = 'purna-owner-replay-key'
const chartId = '00000000-0000-4000-8000-000000001039'

function assertDisposableUrl(value: string): void {
  const parsed = new URL(value)
  if (!['127.0.0.1', 'localhost', '::1'].includes(parsed.hostname)
    || !parsed.pathname.slice(1).startsWith('purna_owner_')) {
    throw new Error('protected-owner replay URLs must target a localhost purna_owner_* database')
  }
}

describeDisposable('Pūrṇa protected-owner production-compatible replay', () => {
  let admin: Pool

  beforeAll(async () => {
    assertDisposableUrl(adminDatabaseUrl!)
    assertDisposableUrl(serveDatabaseUrl!)
    process.env.INQUIRY_STORE_DATABASE_URL = serveDatabaseUrl
    process.env.DB_INQUIRY_USER = 'amjis_inquiry_serve'
    admin = new Pool({ connectionString: adminDatabaseUrl, max: 2 })
    await admin.query(`
      INSERT INTO public.profiles (id, role, status)
      VALUES ($1, 'guest', 'active')
      ON CONFLICT (id) DO NOTHING
    `, [principalUid])
    await admin.query(`
      INSERT INTO public.charts
        (id, client_id, owner_id, name, birth_date, birth_time, birth_place)
      VALUES ($2::uuid, $1, $1, 'Protected owner replay', DATE '2000-01-01',
              TIME '12:00:00', 'Disposable localhost')
      ON CONFLICT (id) DO NOTHING
    `, [principalUid, chartId])
    await admin.query(`
      INSERT INTO public.mcp_api_keys (key_id, key_hash, user_uid, scopes)
      VALUES ($1, 'sha256:disposable-not-a-credential', $2, ARRAY['read'])
      ON CONFLICT (key_id) DO NOTHING
    `, [principalKeyId, principalUid])
  })

  afterAll(async () => {
    await __resetInquiryStorePoolForTests()
    if (admin) {
      await admin.query('DELETE FROM public.mcp_api_keys WHERE key_id=$1', [principalKeyId])
        .catch(() => undefined)
      await admin.query('DELETE FROM public.charts WHERE id=$1::uuid', [chartId])
        .catch(() => undefined)
      await admin.query('DELETE FROM public.profiles WHERE id=$1', [principalUid])
        .catch(() => undefined)
      await admin.end()
    }
    delete process.env.INQUIRY_STORE_DATABASE_URL
    delete process.env.DB_INQUIRY_USER
  })

  it('has an unreachable normalized owner and a disabled bootstrap', async () => {
    const result = await admin.query<{
      owner_ok: boolean
      owner_edges: number
      owner_create: boolean
      bootstrap_disabled: boolean
      bootstrap_edges: number
      serving_ok: boolean
    }>(`
      SELECT
        EXISTS (SELECT 1 FROM pg_roles WHERE rolname='purna_inquiry_owner'
          AND NOT rolcanlogin AND NOT rolinherit AND NOT rolsuper AND NOT rolcreatedb
          AND NOT rolcreaterole AND NOT rolreplication AND NOT rolbypassrls) AS owner_ok,
        (SELECT count(*)::int FROM pg_auth_members m JOIN pg_roles r
          ON r.oid=m.roleid OR r.oid=m.member WHERE r.rolname='purna_inquiry_owner') AS owner_edges,
        has_schema_privilege('purna_inquiry_owner','public','CREATE') AS owner_create,
        EXISTS (SELECT 1 FROM pg_roles WHERE rolname='purna_inquiry_bootstrap'
          AND NOT rolcanlogin AND NOT rolinherit AND NOT rolsuper
          AND NOT rolcreaterole AND NOT rolcreatedb
          AND NOT rolreplication AND NOT rolbypassrls) AS bootstrap_disabled,
        (SELECT count(*)::int FROM pg_auth_members m JOIN pg_roles r
          ON r.oid=m.roleid OR r.oid=m.member WHERE r.rolname='purna_inquiry_bootstrap') AS bootstrap_edges,
        EXISTS (SELECT 1 FROM pg_roles WHERE rolname='amjis_inquiry_serve'
          AND rolcanlogin AND rolinherit AND NOT rolsuper AND NOT rolcreatedb
          AND NOT rolcreaterole AND NOT rolreplication AND NOT rolbypassrls
          AND pg_has_role('amjis_inquiry_serve','role_web_serve','member')
          AND NOT has_schema_privilege('amjis_inquiry_serve','public','CREATE')) AS serving_ok
    `)
    expect(result.rows[0]).toEqual({
      owner_ok: true,
      owner_edges: 0,
      owner_create: false,
      bootstrap_disabled: true,
      bootstrap_edges: 0,
      serving_ok: true,
    })
  })

  it('admits the dedicated login, enforces cross-principal RLS, and rolls back all probe rows', async () => {
    await expect(probeInquiryStoreReadiness({
      principalUid,
      principalKeyId,
      chartId,
    })).resolves.toEqual({
      dedicated_login: true,
      least_privilege_role: true,
      rls_tables: 4,
      same_principal_rows: 4,
      cross_principal_rows: 0,
      security_definer_search_path: true,
      rolled_back: true,
    })

    const persisted = await admin.query<{ total: number }>(`
      SELECT (
        (SELECT count(*) FROM public.planner_inquiry_lifecycles WHERE principal_uid=$1) +
        (SELECT count(*) FROM public.planner_inquiry_evidence_receipts receipt
          JOIN public.planner_inquiry_lifecycles lifecycle USING (inquiry_id)
          WHERE lifecycle.principal_uid=$1) +
        (SELECT count(*) FROM public.planner_inquiry_action_reservations reservation
          JOIN public.planner_inquiry_lifecycles lifecycle USING (inquiry_id)
          WHERE lifecycle.principal_uid=$1) +
        (SELECT count(*) FROM public.planner_managed_prashna_jobs WHERE principal_uid=$1)
      )::int AS total
    `, [principalUid])
    expect(persisted.rows[0]?.total).toBe(0)
  })

  it('rejects an unexpected member that could SET ROLE to the serving login', async () => {
    await admin.query(`
      DO $$ BEGIN
        CREATE ROLE purna_owner_replay_inbound NOLOGIN;
      EXCEPTION WHEN duplicate_object THEN NULL;
      END $$;
      GRANT amjis_inquiry_serve TO purna_owner_replay_inbound;
    `)
    try {
      await expect(probeInquiryStoreReadiness({
        principalUid,
        principalKeyId,
        chartId,
      })).rejects.toThrow('INQUIRY_STORE_READINESS_ROLE_POSTURE_FAILED')
    } finally {
      await admin.query('REVOKE amjis_inquiry_serve FROM purna_owner_replay_inbound')
      await admin.query('DROP ROLE purna_owner_replay_inbound')
    }
  })
})
