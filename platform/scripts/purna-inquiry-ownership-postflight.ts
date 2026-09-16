/** Always-run cleanup and final attestation for the Pūrṇa ownership bootstrap. */
import { Pool } from 'pg'

const ADMIN_URL = 'PURNA_INQUIRY_ADMIN_DATABASE_URL'

export async function runPurnaInquiryOwnershipPostflight(
  databaseUrl = process.env[ADMIN_URL],
): Promise<void> {
  if (!databaseUrl) throw new Error(`${ADMIN_URL} is required for Pūrṇa owner cleanup.`)
  const pool = new Pool({ connectionString: databaseUrl, max: 1 })
  const client = await pool.connect()
  try {
    const actor = await client.query<{ session_user: string; current_user: string; provider_admin: boolean }>(`
      SELECT session_user, current_user,
             pg_has_role(session_user, 'cloudsqlsuperuser', 'member') AS provider_admin
    `)
    if (actor.rows[0]?.session_user !== 'purna_inquiry_bootstrap'
      || actor.rows[0]?.current_user !== 'purna_inquiry_bootstrap'
      || !actor.rows[0]?.provider_admin) {
      throw new Error('Pūrṇa ownership postflight requires the dedicated temporary Cloud SQL bootstrap login.')
    }
    await client.query('BEGIN')
    // A recovery run may begin after an older postflight already removed the
    // app membership but left detector-only ACLs. Re-establish the exact role
    // only inside this transaction, use it to revoke app-owned grants, and
    // remove it again below before COMMIT.
    await client.query('SET LOCAL ROLE cloudsqlsuperuser')
    await client.query('GRANT amjis_app TO purna_inquiry_bootstrap')
    await client.query('RESET ROLE')
    await client.query('SET LOCAL ROLE amjis_app')
    await client.query(`
      DO $$
      DECLARE role_name text;
      BEGIN
        FOREACH role_name IN ARRAY ARRAY[
          'purna_inquiry_owner', 'amjis_inquiry_serve', 'role_web_serve'
        ] LOOP
          IF to_regrole(role_name) IS NOT NULL THEN
            EXECUTE format('REVOKE CREATE ON SCHEMA public FROM %I', role_name);
          END IF;
        END LOOP;
      END $$;
      -- The one-shot login receives these two direct read prerequisites so
      -- the ownership state detector can run before temporary memberships
      -- are armed. Revoke them here so the disabled Cloud SQL user has no
      -- ACL dependencies and can be deleted after marked attestation.
      REVOKE SELECT ON TABLE public._migrations_applied FROM purna_inquiry_bootstrap;
      REVOKE USAGE ON SCHEMA public FROM purna_inquiry_bootstrap;
    `)
    await client.query('RESET ROLE')
    await client.query('SET LOCAL ROLE cloudsqlsuperuser')
    await client.query(`
      DO $$
      DECLARE parent_name text;
      BEGIN
        FOREACH parent_name IN ARRAY ARRAY['purna_inquiry_owner', 'amjis_app'] LOOP
          IF to_regrole(parent_name) IS NOT NULL AND EXISTS (
            SELECT 1 FROM pg_auth_members membership
             WHERE membership.roleid=to_regrole(parent_name)
               AND membership.member='purna_inquiry_bootstrap'::regrole
          ) THEN
            EXECUTE format('REVOKE %I FROM purna_inquiry_bootstrap', parent_name);
          END IF;
        END LOOP;
      END $$;
      REVOKE cloudsqlsuperuser FROM purna_inquiry_bootstrap;
      -- Cloud SQL's provider-admin role is deliberately not a PostgreSQL
      -- superuser, so it cannot restate NOSUPERUSER/NOREPLICATION/NOBYPASSRLS.
      -- Preflight already fails closed unless all three are false; postflight
      -- asserts they remain false after removing every membership.
      ALTER ROLE purna_inquiry_bootstrap NOLOGIN NOINHERIT NOCREATEROLE
        NOCREATEDB PASSWORD NULL;
    `)
    await client.query('RESET ROLE')
    const finalState = await client.query<{
      owner_can_create: boolean
      serving_can_create: boolean
      bootstrap_disabled: boolean
      bootstrap_memberships: number
      bootstrap_acl_dependencies: number
    }>(`
      SELECT
        coalesce((SELECT has_schema_privilege(oid,'public','CREATE')
          FROM pg_roles WHERE rolname='purna_inquiry_owner'), false) AS owner_can_create,
        coalesce((SELECT has_schema_privilege(oid,'public','CREATE')
          FROM pg_roles WHERE rolname='amjis_inquiry_serve'), false) AS serving_can_create,
        EXISTS (SELECT 1 FROM pg_roles WHERE rolname='purna_inquiry_bootstrap'
          AND NOT rolcanlogin AND NOT rolinherit AND NOT rolsuper
          AND NOT rolcreaterole AND NOT rolcreatedb
          AND NOT rolreplication AND NOT rolbypassrls) AS bootstrap_disabled,
        (SELECT count(*)::int FROM pg_auth_members membership
          JOIN pg_roles role ON role.oid=membership.roleid OR role.oid=membership.member
          WHERE role.rolname='purna_inquiry_bootstrap') AS bootstrap_memberships,
        (SELECT count(*)::int FROM pg_shdepend dependency
          JOIN pg_roles role ON role.oid=dependency.refobjid
          WHERE role.rolname='purna_inquiry_bootstrap'
            AND dependency.deptype='a') AS bootstrap_acl_dependencies
    `)
    const final = finalState.rows[0]
    if (!final || final.owner_can_create || final.serving_can_create
      || !final.bootstrap_disabled || final.bootstrap_memberships !== 0
      || final.bootstrap_acl_dependencies !== 0) {
      throw new Error('Pūrṇa ownership postflight did not remove all temporary authority.')
    }
    await client.query('COMMIT')
  } catch (error) {
    await client.query('ROLLBACK').catch(() => undefined)
    throw error
  } finally {
    client.release()
    await pool.end()
  }

}

if (require.main === module) {
  runPurnaInquiryOwnershipPostflight()
    .then(() => process.stdout.write('Pūrṇa protected-owner postflight complete.\n'))
    .catch((error) => { console.error(error); process.exitCode = 1 })
}
