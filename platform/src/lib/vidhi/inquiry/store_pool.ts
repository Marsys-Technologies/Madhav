import 'server-only'

import { randomUUID } from 'node:crypto'
import { Connector } from '@google-cloud/cloud-sql-connector'
import { Pool, type PoolClient } from 'pg'

import { assertChartContextValue, CHART_CONTEXT_GUC, PRINCIPAL_ID_GUC } from '@/lib/db/roles'

const g = globalThis as typeof globalThis & {
  __pgInquiryStorePool?: Pool
  __pgInquiryStoreConnector?: Connector
}

export class InquiryStoreRoleNotConfiguredError extends Error {
  constructor() {
    super(
      'INQUIRY_STORE_ROLE_NOT_CONFIGURED: configure INQUIRY_STORE_DATABASE_URL or ' +
      'DB_INQUIRY_USER and DB_INQUIRY_PASSWORD; refusing to use the broad application pool',
    )
    this.name = 'InquiryStoreRoleNotConfiguredError'
  }
}

/**
 * Dedicated least-privilege pool for Pūrṇa lifecycle and managed-job state.
 * It never falls back to DB_USER/DB_PASSWORD: doing so would silently bypass
 * the role_web_serve grant and RLS boundary these stores are designed around.
 */
export async function getInquiryStorePool(): Promise<Pool> {
  if (g.__pgInquiryStorePool) return g.__pgInquiryStorePool

  const keepalive = {
    keepAlive: true,
    keepAliveInitialDelayMillis: 10_000,
    idleTimeoutMillis: 15_000,
    connectionTimeoutMillis: 5_000,
    options: '-c statement_timeout=25000',
    max: 10,
  }
  if (process.env.INQUIRY_STORE_DATABASE_URL) {
    g.__pgInquiryStorePool = new Pool({
      connectionString: process.env.INQUIRY_STORE_DATABASE_URL,
      ...keepalive,
    })
  } else if (process.env.DB_INQUIRY_USER && process.env.DB_INQUIRY_PASSWORD) {
    const instanceConnectionName = process.env.INSTANCE_CONNECTION_NAME
    const database = process.env.DB_NAME
    if (!instanceConnectionName || !database) throw new InquiryStoreRoleNotConfiguredError()
    const connector = new Connector()
    const clientOpts = await connector.getOptions({ instanceConnectionName })
    g.__pgInquiryStoreConnector = connector
    g.__pgInquiryStorePool = new Pool({
      ...clientOpts,
      user: process.env.DB_INQUIRY_USER,
      password: process.env.DB_INQUIRY_PASSWORD,
      database,
      ...keepalive,
    })
  } else {
    throw new InquiryStoreRoleNotConfiguredError()
  }

  g.__pgInquiryStorePool.on('error', (error) => {
    console.error('[pg inquiry store] idle client error (evicted)', error)
  })
  return g.__pgInquiryStorePool
}

/** Pin tenant context for every query made through the dedicated RLS role. */
export async function withInquiryStoreContext<T>(
  principalUid: string,
  chartId: string | null,
  action: (client: PoolClient) => Promise<T>,
): Promise<T> {
  const pinnedChart = chartId === null ? null : assertChartContextValue(chartId)
  const pool = await getInquiryStorePool()
  const client = await pool.connect()
  try {
    await client.query('BEGIN')
    await client.query('SELECT set_config($1, $2, true)', [PRINCIPAL_ID_GUC, principalUid])
    if (pinnedChart !== null) {
      await client.query('SELECT set_config($1, $2, true)', [CHART_CONTEXT_GUC, pinnedChart])
    }
    const result = await action(client)
    await client.query('COMMIT')
    return result
  } catch (error) {
    await client.query('ROLLBACK').catch(() => undefined)
    throw error
  } finally {
    client.release()
  }
}

export interface InquiryStoreReadinessResult {
  dedicated_login: true
  least_privilege_role: true
  rls_tables: 4
  same_principal_rows: 4
  cross_principal_rows: 0
  security_definer_search_path: true
  rolled_back: true
}

/**
 * Non-vacuous deployment canary. It creates one row in every Pūrṇa store through
 * the reviewed serving-role surface, proves those rows disappear after changing
 * the transaction principal, and always rolls the entire probe back.
 */
export async function probeInquiryStoreReadiness(args: {
  principalUid: string
  principalKeyId: string
  chartId: string
}): Promise<InquiryStoreReadinessResult> {
  const chartId = assertChartContextValue(args.chartId)
  const pool = await getInquiryStorePool()
  const client = await pool.connect()
  const inquiryId = randomUUID()
  const managedJobId = randomUUID()

  try {
    await client.query('BEGIN')
    await client.query('SELECT set_config($1, $2, true)', [PRINCIPAL_ID_GUC, args.principalUid])
    await client.query('SELECT set_config($1, $2, true)', [CHART_CONTEXT_GUC, chartId])

    const role = await client.query<{
      login: boolean
      superuser: boolean
      create_role: boolean
      create_database: boolean
      bypass_rls: boolean
      serves_web: boolean
      other_memberships: number
      direct_memberships: number
      inbound_memberships: number
      can_create_public: boolean
    }>(`
      SELECT r.rolcanlogin AS login, r.rolsuper AS superuser,
             r.rolcreaterole AS create_role, r.rolcreatedb AS create_database,
             r.rolbypassrls AS bypass_rls,
             pg_has_role(current_user, 'role_web_serve', 'member') AS serves_web,
             has_schema_privilege(current_user, 'public', 'CREATE') AS can_create_public,
             (SELECT count(*)::int FROM pg_auth_members membership
               WHERE membership.member=r.oid) AS direct_memberships,
             (SELECT count(*)::int FROM pg_auth_members membership
               WHERE membership.roleid=r.oid) AS inbound_memberships,
             (SELECT count(*)::int
                FROM pg_roles candidate
               WHERE candidate.rolname NOT IN (current_user, 'role_web_serve')
                 AND pg_has_role(current_user, candidate.oid, 'member')) AS other_memberships
        FROM pg_roles r WHERE r.rolname=current_user
    `)
    const roleRow = role.rows[0]
    const expectedLogin = process.env.DB_INQUIRY_USER ?? 'amjis_inquiry_serve'
    if (!roleRow || !roleRow.login || roleRow.superuser || roleRow.create_role
        || roleRow.create_database || roleRow.bypass_rls || !roleRow.serves_web
        || roleRow.other_memberships !== 0 || roleRow.direct_memberships !== 1
        || roleRow.inbound_memberships !== 0 || roleRow.can_create_public) {
      throw new Error('INQUIRY_STORE_READINESS_ROLE_POSTURE_FAILED')
    }
    const currentUser = await client.query<{ current_user: string }>('SELECT current_user')
    if (currentUser.rows[0]?.current_user !== expectedLogin) {
      throw new Error('INQUIRY_STORE_READINESS_WRONG_LOGIN')
    }

    const posture = await client.query<{
      rls_tables: number
      protected_owner_tables: number
      protected_owner_functions: number
      owner_membership_edges: number
      owner_can_create_public: boolean
      owner_can_use_public: boolean
      scoped_policies: number
      safe_definers: number
    }>(`
      SELECT
        (SELECT count(*)::int FROM pg_class c
          JOIN pg_namespace n ON n.oid=c.relnamespace
          WHERE n.nspname='public' AND c.relname = ANY($1::text[])
            AND c.relrowsecurity) AS rls_tables,
        (SELECT count(*)::int FROM pg_class c
          JOIN pg_namespace n ON n.oid=c.relnamespace
          JOIN pg_roles owner ON owner.oid=c.relowner
          WHERE n.nspname='public' AND c.relname = ANY($1::text[])
            AND owner.rolname=$4::text
            AND NOT owner.rolcanlogin AND NOT owner.rolinherit AND NOT owner.rolsuper
            AND NOT owner.rolcreatedb AND NOT owner.rolcreaterole
            AND NOT owner.rolreplication AND NOT owner.rolbypassrls
            AND NOT pg_has_role(current_user, owner.oid, 'member')
            AND NOT pg_has_role('role_web_serve', owner.oid, 'member')) AS protected_owner_tables,
        (SELECT count(*)::int FROM pg_proc p
          JOIN pg_namespace n ON n.oid=p.pronamespace
          JOIN pg_roles owner ON owner.oid=p.proowner
          WHERE n.nspname='public' AND p.proname = ANY($2::text[])
            AND owner.rolname=$4::text
            AND NOT owner.rolcanlogin AND NOT owner.rolinherit AND NOT owner.rolsuper
            AND NOT owner.rolcreatedb AND NOT owner.rolcreaterole
            AND NOT owner.rolreplication AND NOT owner.rolbypassrls
            AND NOT pg_has_role(current_user, owner.oid, 'member')
            AND NOT pg_has_role('role_web_serve', owner.oid, 'member')) AS protected_owner_functions,
        (SELECT count(*)::int FROM pg_auth_members membership
          JOIN pg_roles owner
            ON owner.oid=membership.roleid OR owner.oid=membership.member
          WHERE owner.rolname=$4::text) AS owner_membership_edges,
        coalesce((SELECT has_schema_privilege(owner.oid, 'public', 'CREATE')
          FROM pg_roles owner WHERE owner.rolname=$4::text), false) AS owner_can_create_public,
        coalesce((SELECT has_schema_privilege(owner.oid, 'public', 'USAGE')
          FROM pg_roles owner WHERE owner.rolname=$4::text), false) AS owner_can_use_public,
        (SELECT count(*)::int FROM pg_policies p
          WHERE p.schemaname='public' AND p.tablename = ANY($1::text[])
            AND 'role_web_serve'=ANY(p.roles)) AS scoped_policies,
        (SELECT count(*)::int FROM pg_proc p
          JOIN pg_namespace n ON n.oid=p.pronamespace
          JOIN pg_roles owner ON owner.oid=p.proowner
          WHERE n.nspname='public' AND p.proname = ANY($3::text[]) AND p.prosecdef
            AND 'search_path=pg_catalog, pg_temp'=ANY(p.proconfig)
            AND owner.rolname=$4::text
            AND NOT owner.rolcanlogin AND NOT owner.rolinherit AND NOT owner.rolsuper
            AND NOT owner.rolcreatedb AND NOT owner.rolcreaterole
            AND NOT owner.rolreplication AND NOT owner.rolbypassrls
            AND NOT pg_has_role(current_user, owner.oid, 'member')
            AND NOT pg_has_role('role_web_serve', owner.oid, 'member')) AS safe_definers
    `, [
      [
        'planner_inquiry_lifecycles',
        'planner_inquiry_evidence_receipts',
        'planner_inquiry_action_reservations',
        'planner_managed_prashna_jobs',
      ],
      [
        'planner_inquiry_immutable_guard',
        'create_planner_inquiry_lifecycle',
        'purge_expired_planner_inquiries_global',
        'planner_inquiry_action_reservation_guard',
        'planner_managed_prashna_job_credential_guard',
        'planner_managed_prashna_job_immutable_guard',
        'create_planner_managed_prashna_job',
        'get_planner_managed_prashna_job',
        'claim_planner_managed_prashna_job',
        'update_planner_managed_prashna_job_progress',
        'complete_planner_managed_prashna_job',
        'fail_planner_managed_prashna_job',
      ],
      [
        'create_planner_inquiry_lifecycle',
        'purge_expired_planner_inquiries_global',
        'planner_managed_prashna_job_credential_guard',
        'create_planner_managed_prashna_job',
        'get_planner_managed_prashna_job',
        'claim_planner_managed_prashna_job',
        'update_planner_managed_prashna_job_progress',
        'complete_planner_managed_prashna_job',
        'fail_planner_managed_prashna_job',
      ],
      process.env.PURNA_INQUIRY_OBJECT_OWNER ?? 'purna_inquiry_owner',
    ])
    const postureRow = posture.rows[0]
    if (!postureRow || postureRow.rls_tables !== 4 || postureRow.protected_owner_tables !== 4
        || postureRow.protected_owner_functions !== 12 || postureRow.scoped_policies !== 4
        || postureRow.owner_membership_edges !== 0 || postureRow.owner_can_create_public
        || !postureRow.owner_can_use_public
        || postureRow.safe_definers !== 9) {
      throw new Error('INQUIRY_STORE_READINESS_DATABASE_POSTURE_FAILED')
    }

    await client.query(`
      SELECT inquiry_id FROM create_planner_inquiry_lifecycle(
        $1::uuid, $2::text, $3::uuid,
        'sha256:readiness-contract', 'sha256:readiness-plan',
        'sha256:readiness-catalog', 'readiness-v1',
        'sha256:readiness-overlay', 'readiness-build',
        '{}'::jsonb, '{}'::jsonb, 'INCOMPLETE',
        'sha256:readiness-jti', now() + interval '5 minutes'
      )
    `, [inquiryId, args.principalUid, chartId])
    await client.query(`
      INSERT INTO planner_inquiry_evidence_receipts
        (inquiry_id, revision, obligation_ids, plan_item_id, scu_id, binding_id,
         canonical_args_hash, raw_result_hash, disposition, evidence_jsonb)
      VALUES ($1::uuid, 1, ARRAY['readiness'], 'item-000', 'scu.readiness',
              'registry:readiness', 'sha256:args', 'sha256:result', 'served', '{}'::jsonb)
    `, [inquiryId])
    await client.query(`
      INSERT INTO planner_inquiry_action_reservations
        (inquiry_id, revision, plan_item_id, source_jti_hash, reservation_hash, lease_expires_at)
      VALUES ($1::uuid, 0, 'item-000', 'sha256:readiness-jti', $2, now() + interval '1 minute')
    `, [inquiryId, `sha256:${randomUUID()}`])
    await client.query(`
      SELECT job_id FROM create_planner_managed_prashna_job(
        $1::uuid, $2::text, $3::text, 'api_key', $4::uuid,
        '{"question":"readiness","response_format":"digest"}'::jsonb
      )
    `, [managedJobId, args.principalUid, args.principalKeyId, chartId])

    const samePrincipal = await client.query<{ row_count: number }>(`
      SELECT (
        (SELECT count(*) FROM planner_inquiry_lifecycles WHERE inquiry_id=$1::uuid) +
        (SELECT count(*) FROM planner_inquiry_evidence_receipts WHERE inquiry_id=$1::uuid) +
        (SELECT count(*) FROM planner_inquiry_action_reservations WHERE inquiry_id=$1::uuid) +
        (SELECT count(*) FROM get_planner_managed_prashna_job($2::uuid, $3::text, $4::text))
      )::int AS row_count
    `, [inquiryId, managedJobId, args.principalUid, args.principalKeyId])
    if (samePrincipal.rows[0]?.row_count !== 4) {
      throw new Error('INQUIRY_STORE_READINESS_SAME_PRINCIPAL_FAILED')
    }

    const crossPrincipalUid = `${args.principalUid}:readiness-cross-principal`
    await client.query('SELECT set_config($1, $2, true)', [
      PRINCIPAL_ID_GUC,
      crossPrincipalUid,
    ])
    const crossPrincipal = await client.query<{ row_count: number }>(`
      SELECT (
        (SELECT count(*) FROM planner_inquiry_lifecycles WHERE inquiry_id=$1::uuid) +
        (SELECT count(*) FROM planner_inquiry_evidence_receipts WHERE inquiry_id=$1::uuid) +
        (SELECT count(*) FROM planner_inquiry_action_reservations WHERE inquiry_id=$1::uuid) +
        (SELECT count(*) FROM get_planner_managed_prashna_job($2::uuid, $3::text, $4::text))
      )::int AS row_count
    `, [inquiryId, managedJobId, crossPrincipalUid, args.principalKeyId])
    if (crossPrincipal.rows[0]?.row_count !== 0) {
      throw new Error('INQUIRY_STORE_READINESS_CROSS_PRINCIPAL_FAILED')
    }

    await client.query('ROLLBACK')
    return {
      dedicated_login: true,
      least_privilege_role: true,
      rls_tables: 4,
      same_principal_rows: 4,
      cross_principal_rows: 0,
      security_definer_search_path: true,
      rolled_back: true,
    }
  } catch (error) {
    await client.query('ROLLBACK').catch(() => undefined)
    throw error
  } finally {
    client.release()
  }
}

export async function __resetInquiryStorePoolForTests(): Promise<void> {
  if (g.__pgInquiryStorePool) await g.__pgInquiryStorePool.end()
  if (g.__pgInquiryStoreConnector) await g.__pgInquiryStoreConnector.close()
  delete g.__pgInquiryStorePool
  delete g.__pgInquiryStoreConnector
}
