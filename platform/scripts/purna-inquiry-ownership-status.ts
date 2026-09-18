/** Read-only state detector for the one-shot Pūrṇa protected-owner handoff. */
import { Pool } from 'pg'

// 1040 is the current protected-owner release boundary.  A database marked
// through 1039 but missing 1040 must re-enter the explicit one-shot bootstrap
// path; the routine migration runner never receives this authority.
const MARKER = '1040_planner_inquiry_successor_lifecycle.sql'
const TABLES = [
  'planner_inquiry_lifecycles',
  'planner_inquiry_evidence_receipts',
  'planner_inquiry_action_reservations',
  'planner_managed_prashna_jobs',
]
const FUNCTIONS = [
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
  'create_planner_inquiry_successor_lifecycle',
]

export type PurnaOwnershipState = 'armed' | 'rearm_required' | 'interrupted' | 'cleanup_required' | 'marked' | 'invalid'

export async function purnaOwnershipState(databaseUrl = process.env.DATABASE_URL): Promise<PurnaOwnershipState> {
  if (!databaseUrl) throw new Error('DATABASE_URL is required for Pūrṇa ownership status.')
  const pool = new Pool({ connectionString: databaseUrl, max: 1 })
  try {
    const result = await pool.query<{
      marker: boolean
      tables_total: number
      tables_owned: number
      functions_total: number
      functions_owned: number
      owner_normalized: boolean
      owner_memberships: number
      owner_can_create_public: boolean
      serving_normalized: boolean
      bootstrap_disabled: boolean
      bootstrap_armed: boolean
      bootstrap_memberships: number
      bootstrap_acl_dependencies: number
    }>(`
      SELECT
        EXISTS (SELECT 1 FROM public._migrations_applied WHERE filename=$1) AS marker,
        (SELECT count(*)::int FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
          WHERE n.nspname='public' AND c.relname=ANY($2::text[]) AND c.relkind IN ('r','p')) AS tables_total,
        (SELECT count(*)::int FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
          JOIN pg_roles r ON r.oid=c.relowner WHERE n.nspname='public'
          AND c.relname=ANY($2::text[]) AND c.relkind IN ('r','p') AND r.rolname='purna_inquiry_owner') AS tables_owned,
        (SELECT count(*)::int FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
          WHERE n.nspname='public' AND p.proname=ANY($3::text[])) AS functions_total,
        (SELECT count(*)::int FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
          JOIN pg_roles r ON r.oid=p.proowner WHERE n.nspname='public'
          AND p.proname=ANY($3::text[]) AND r.rolname='purna_inquiry_owner') AS functions_owned,
        EXISTS (SELECT 1 FROM pg_roles WHERE rolname='purna_inquiry_owner'
          AND NOT rolcanlogin AND NOT rolinherit AND NOT rolsuper AND NOT rolcreatedb
          AND NOT rolcreaterole AND NOT rolreplication AND NOT rolbypassrls) AS owner_normalized,
        (SELECT count(*)::int FROM pg_auth_members m JOIN pg_roles r
          ON r.oid=m.roleid OR r.oid=m.member WHERE r.rolname='purna_inquiry_owner') AS owner_memberships,
        coalesce((SELECT has_schema_privilege(r.oid,'public','CREATE')
          FROM pg_roles r WHERE r.rolname='purna_inquiry_owner'), false) AS owner_can_create_public,
        EXISTS (SELECT 1 FROM pg_roles r WHERE r.rolname='amjis_inquiry_serve'
          AND r.rolcanlogin AND r.rolinherit AND NOT r.rolsuper AND NOT r.rolcreatedb
          AND NOT r.rolcreaterole AND NOT r.rolreplication AND NOT r.rolbypassrls
          AND pg_has_role(r.oid,'role_web_serve','member')
          AND (SELECT count(*) FROM pg_auth_members membership
                WHERE membership.member=r.oid) = 1
          AND EXISTS (SELECT 1 FROM pg_auth_members membership
                WHERE membership.roleid='role_web_serve'::regrole
                  AND membership.member=r.oid)
          AND NOT EXISTS (SELECT 1 FROM pg_auth_members membership
                WHERE membership.roleid=r.oid)
          AND NOT has_schema_privilege(r.oid,'public','CREATE')) AS serving_normalized,
        NOT EXISTS (SELECT 1 FROM pg_roles r WHERE r.rolname='purna_inquiry_bootstrap'
          AND (r.rolcanlogin OR r.rolinherit OR r.rolsuper OR r.rolcreaterole OR r.rolcreatedb
            OR r.rolreplication OR r.rolbypassrls)) AS bootstrap_disabled,
        EXISTS (SELECT 1 FROM pg_roles r WHERE r.rolname='purna_inquiry_bootstrap'
          AND r.rolcanlogin AND r.rolinherit AND NOT r.rolsuper
          AND NOT r.rolcreaterole AND NOT r.rolcreatedb
          AND NOT r.rolreplication AND NOT r.rolbypassrls
          AND (SELECT count(*) FROM pg_auth_members membership
                WHERE membership.member=r.oid) = 1
          AND EXISTS (SELECT 1 FROM pg_auth_members membership
                WHERE membership.roleid='cloudsqlsuperuser'::regrole
                  AND membership.member=r.oid)
          AND NOT EXISTS (SELECT 1 FROM pg_auth_members membership
                WHERE membership.roleid=r.oid)) AS bootstrap_armed,
        (SELECT count(*)::int FROM pg_auth_members m JOIN pg_roles r
          ON r.oid=m.roleid OR r.oid=m.member WHERE r.rolname='purna_inquiry_bootstrap') AS bootstrap_memberships,
        (SELECT count(*)::int FROM pg_shdepend dependency
          JOIN pg_roles role ON role.oid=dependency.refobjid
          WHERE role.rolname='purna_inquiry_bootstrap'
            AND dependency.deptype='a') AS bootstrap_acl_dependencies
    `, [MARKER, TABLES, FUNCTIONS])
    const row = result.rows[0]
    if (!row) return 'invalid'
    if (!row.marker) {
      const untouched = row.tables_total === 0 && row.functions_total === 0
      const retryableProtected = row.owner_normalized
        && row.tables_total === row.tables_owned
        && row.functions_total === row.functions_owned
      if (!untouched && !retryableProtected) return 'invalid'
      if (row.owner_can_create_public) return 'interrupted'
      if (row.bootstrap_armed) return 'armed'
      return row.bootstrap_disabled && row.bootstrap_memberships === 0
        ? 'rearm_required'
        : 'interrupted'
    }
    const objectsProtected = row.tables_total === TABLES.length && row.tables_owned === TABLES.length
      && row.functions_total === FUNCTIONS.length && row.functions_owned === FUNCTIONS.length
      && row.owner_normalized && row.owner_memberships === 0 && row.serving_normalized
    if (!objectsProtected) return 'invalid'
    // A prior cleanup may have disabled/password-nulled the one-shot login and
    // removed every membership while leaving direct detector ACLs behind. That
    // actor cannot authenticate or SET ROLE, so it must be explicitly rearmed
    // before postflight can remove the residue.
    if (row.bootstrap_disabled && row.bootstrap_memberships === 0
      && !row.owner_can_create_public && row.bootstrap_acl_dependencies !== 0) {
      return 'rearm_required'
    }
    return row.owner_can_create_public || !row.bootstrap_disabled
      || row.bootstrap_memberships !== 0 || row.bootstrap_acl_dependencies !== 0
      ? 'cleanup_required'
      : 'marked'
  } finally {
    await pool.end()
  }
}

if (require.main === module) {
  purnaOwnershipState()
    .then((state) => process.stdout.write(`${state}\n`))
    .catch((error) => { console.error(error); process.exitCode = 1 })
}
