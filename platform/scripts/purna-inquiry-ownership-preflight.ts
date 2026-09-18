/** Privileged, one-shot bootstrap for Pūrṇa protected ownership. */
import { Pool } from 'pg'

const ADMIN_URL = 'PURNA_INQUIRY_ADMIN_DATABASE_URL'
const SERVE_PASSWORD = 'PURNA_INQUIRY_SERVE_PASSWORD'

export async function runPurnaInquiryOwnershipPreflight(
  databaseUrl = process.env[ADMIN_URL],
  servingPassword = process.env[SERVE_PASSWORD],
): Promise<void> {
  if (!databaseUrl) throw new Error(`${ADMIN_URL} is required for the one-shot Pūrṇa owner bootstrap.`)
  if (!servingPassword || servingPassword.length < 32) {
    throw new Error(`${SERVE_PASSWORD} must contain at least 32 characters.`)
  }
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
      throw new Error('Pūrṇa ownership preflight requires the dedicated temporary Cloud SQL bootstrap login.')
    }
    await client.query('BEGIN')
    await client.query("SELECT set_config('purna.bootstrap_password', $1, true)", [servingPassword])
    await client.query('SET LOCAL ROLE cloudsqlsuperuser')
    await client.query(`
      DO $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='purna_inquiry_owner') THEN
          CREATE ROLE purna_inquiry_owner NOLOGIN NOINHERIT;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='amjis_inquiry_serve') THEN
          CREATE ROLE amjis_inquiry_serve LOGIN INHERIT;
        END IF;
      END $$;
      DO $$ BEGIN
        IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname IN ('purna_inquiry_owner','amjis_inquiry_serve')
          AND (rolsuper OR rolreplication OR rolbypassrls))
        THEN RAISE EXCEPTION 'refusing elevated Pūrṇa owner or serving role'; END IF;
        IF EXISTS (
          SELECT 1 FROM pg_namespace namespace
          CROSS JOIN LATERAL aclexplode(
            coalesce(namespace.nspacl, acldefault('n', namespace.nspowner))
          ) privilege
          WHERE namespace.nspname='public' AND privilege.grantee=0
            AND privilege.privilege_type='CREATE'
        ) THEN RAISE EXCEPTION 'refusing protected-owner migration while PUBLIC can CREATE in public'; END IF;
      END $$;
      ALTER ROLE purna_inquiry_owner NOLOGIN NOINHERIT NOCREATEDB NOCREATEROLE;
      ALTER ROLE amjis_inquiry_serve LOGIN INHERIT NOCREATEDB NOCREATEROLE;
      ALTER ROLE purna_inquiry_bootstrap LOGIN INHERIT NOCREATEDB NOCREATEROLE;
      DO $$ BEGIN
        EXECUTE format(
          'ALTER ROLE amjis_inquiry_serve PASSWORD %L',
          current_setting('purna.bootstrap_password', true)
        );
      END $$;

      DO $$ BEGIN
        IF EXISTS (
          SELECT 1 FROM pg_auth_members membership
            JOIN pg_roles parent ON parent.oid=membership.roleid
            JOIN pg_roles member ON member.oid=membership.member
           WHERE (parent.rolname='purna_inquiry_owner' OR member.rolname='purna_inquiry_owner')
             AND NOT (parent.rolname='purna_inquiry_owner' AND member.rolname='purna_inquiry_bootstrap')
        ) THEN RAISE EXCEPTION 'refusing unreviewed Pūrṇa owner membership topology'; END IF;
        IF EXISTS (
          SELECT 1 FROM pg_roles candidate
           WHERE candidate.rolname NOT IN ('amjis_inquiry_serve','role_web_serve')
             AND pg_has_role('amjis_inquiry_serve',candidate.oid,'member')
        ) THEN RAISE EXCEPTION 'refusing serving-login membership outside role_web_serve'; END IF;
        IF EXISTS (
          SELECT 1 FROM pg_auth_members membership
           WHERE membership.roleid='amjis_inquiry_serve'::regrole
        ) THEN RAISE EXCEPTION 'refusing members of the Pūrṇa serving login'; END IF;
      END $$;

      GRANT role_web_serve TO amjis_inquiry_serve;
      GRANT amjis_app TO purna_inquiry_bootstrap;
      GRANT purna_inquiry_owner TO purna_inquiry_bootstrap WITH ADMIN OPTION;
      RESET ROLE;
      SET LOCAL ROLE amjis_app;
      REVOKE CREATE ON SCHEMA public FROM amjis_inquiry_serve, role_web_serve;
      GRANT USAGE, CREATE ON SCHEMA public TO purna_inquiry_owner;
      GRANT REFERENCES (id) ON TABLE public.profiles, public.charts TO purna_inquiry_owner;
      GRANT REFERENCES (key_id) ON TABLE public.mcp_api_keys TO purna_inquiry_owner;
      GRANT REFERENCES (access_token_hash) ON TABLE public.mcp_oauth_tokens TO purna_inquiry_owner;
      GRANT SELECT (key_id, user_uid, revoked_at), UPDATE (revoked_at)
        ON TABLE public.mcp_api_keys TO purna_inquiry_owner;
      GRANT SELECT (access_token_hash, uid, expires_at), UPDATE (expires_at)
        ON TABLE public.mcp_oauth_tokens TO purna_inquiry_owner;

      -- ADMIN OPTION on the owner exists only so the terminal protected
      -- ownership migration (1039 or its successor) can revoke its exact edge
      -- transactionally. amjis_app membership is in the safe
      -- direction (deployment login is the member, runtime role is the parent)
      -- and supplies migration 1034's existing-table write privileges.
      RESET ROLE;

      DO $$ BEGIN
        IF NOT EXISTS (
          SELECT 1 FROM pg_roles
           WHERE rolname='purna_inquiry_bootstrap'
             AND rolcanlogin AND rolinherit AND NOT rolsuper
             AND NOT rolcreatedb AND NOT rolcreaterole
             AND NOT rolreplication AND NOT rolbypassrls
        ) THEN RAISE EXCEPTION 'Pūrṇa bootstrap role attributes did not normalize'; END IF;
        IF NOT pg_has_role('purna_inquiry_bootstrap','amjis_app','member')
          OR NOT pg_has_role('purna_inquiry_bootstrap','purna_inquiry_owner','member')
        THEN RAISE EXCEPTION 'Pūrṇa bootstrap temporary memberships did not converge'; END IF;
        IF (SELECT count(*) FROM pg_auth_members membership
              WHERE membership.member='amjis_inquiry_serve'::regrole) <> 1
          OR NOT EXISTS (
            SELECT 1 FROM pg_auth_members membership
             WHERE membership.roleid='role_web_serve'::regrole
               AND membership.member='amjis_inquiry_serve'::regrole
          )
          OR EXISTS (
            SELECT 1 FROM pg_auth_members membership
             WHERE membership.roleid='amjis_inquiry_serve'::regrole
          )
        THEN RAISE EXCEPTION 'Pūrṇa serving-login membership topology did not converge'; END IF;
        IF NOT has_table_privilege(
          'purna_inquiry_bootstrap', 'public.asset_output_digest_specs', 'INSERT'
        ) THEN RAISE EXCEPTION 'Pūrṇa bootstrap cannot apply migration 1034'; END IF;
        IF NOT has_table_privilege(
          'purna_inquiry_bootstrap', 'public._migrations_applied', 'INSERT'
        ) THEN RAISE EXCEPTION 'Pūrṇa bootstrap cannot write the migration ledger'; END IF;
        IF NOT has_sequence_privilege(
          'purna_inquiry_bootstrap', 'public._migrations_applied_id_seq', 'USAGE'
        ) THEN RAISE EXCEPTION 'Pūrṇa bootstrap cannot advance the migration ledger'; END IF;
      END $$;
    `)
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
  runPurnaInquiryOwnershipPreflight()
    .then(() => process.stdout.write('Pūrṇa protected-owner preflight complete.\n'))
    .catch((error) => { console.error(error); process.exitCode = 1 })
}
