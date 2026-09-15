-- Migration 1039: close the temporary Pūrṇa migration-owner membership.
--
-- A privileged, one-shot preflight creates the NOLOGIN owner and dedicated
-- serving LOGIN, grants the owner CREATE on public, and grants the ordinary
-- migration actor direct owner membership WITH ADMIN OPTION. Migrations
-- 1033/1037/1038 SET LOCAL ROLE to create every Pūrṇa object under that owner.
-- This migration attests the exact object and runtime posture and then makes
-- the owner unreachable by revoking the only temporary membership edge.

BEGIN;
RESET ROLE;

DO $$
DECLARE
  target_table text;
  target_function regprocedure;
BEGIN
  IF current_user <> session_user THEN
    RAISE EXCEPTION 'migration 1039 requires the direct migration actor';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_roles
     WHERE rolname='purna_inquiry_owner'
       AND NOT rolcanlogin AND NOT rolinherit AND NOT rolsuper
       AND NOT rolcreatedb AND NOT rolcreaterole
       AND NOT rolreplication AND NOT rolbypassrls
  ) THEN
    RAISE EXCEPTION 'migration 1039 requires normalized NOLOGIN purna_inquiry_owner';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_auth_members membership
      JOIN pg_roles owner ON owner.oid=membership.roleid
      JOIN pg_roles actor ON actor.oid=membership.member
     WHERE owner.rolname='purna_inquiry_owner'
       AND actor.rolname=session_user
       AND membership.admin_option
  ) THEN
    RAISE EXCEPTION 'migration 1039 requires direct temporary owner membership with admin option';
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_auth_members membership
      JOIN pg_roles parent ON parent.oid=membership.roleid
      JOIN pg_roles member ON member.oid=membership.member
     WHERE (parent.rolname='purna_inquiry_owner' OR member.rolname='purna_inquiry_owner')
       AND NOT (parent.rolname='purna_inquiry_owner' AND member.rolname=session_user)
  ) THEN
    RAISE EXCEPTION 'migration 1039 refuses unreviewed protected-owner membership edges';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_roles
     WHERE rolname='amjis_inquiry_serve'
       AND rolcanlogin AND rolinherit AND NOT rolsuper
       AND NOT rolcreatedb AND NOT rolcreaterole
       AND NOT rolreplication AND NOT rolbypassrls
  ) OR NOT pg_has_role('amjis_inquiry_serve', 'role_web_serve', 'member')
    OR has_schema_privilege('amjis_inquiry_serve', 'public', 'CREATE') THEN
    RAISE EXCEPTION 'migration 1039 requires the normalized least-privilege serving login';
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_roles candidate
     WHERE candidate.rolname NOT IN ('amjis_inquiry_serve', 'role_web_serve')
       AND pg_has_role('amjis_inquiry_serve', candidate.oid, 'member')
  ) THEN
    RAISE EXCEPTION 'migration 1039 refuses serving-login membership outside role_web_serve';
  END IF;
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
    ) THEN
    RAISE EXCEPTION 'migration 1039 requires exact serving-login membership topology';
  END IF;

  IF NOT has_column_privilege('purna_inquiry_owner', 'public.profiles', 'id', 'REFERENCES')
    OR NOT has_column_privilege('purna_inquiry_owner', 'public.charts', 'id', 'REFERENCES')
    OR NOT has_column_privilege('purna_inquiry_owner', 'public.mcp_api_keys', 'key_id', 'REFERENCES')
    OR NOT has_column_privilege('purna_inquiry_owner', 'public.mcp_oauth_tokens', 'access_token_hash', 'REFERENCES')
    OR NOT has_column_privilege('purna_inquiry_owner', 'public.mcp_api_keys', 'key_id', 'SELECT')
    OR NOT has_column_privilege('purna_inquiry_owner', 'public.mcp_api_keys', 'user_uid', 'SELECT')
    OR NOT has_column_privilege('purna_inquiry_owner', 'public.mcp_api_keys', 'revoked_at', 'SELECT')
    OR NOT has_column_privilege('purna_inquiry_owner', 'public.mcp_api_keys', 'revoked_at', 'UPDATE')
    OR NOT has_column_privilege('purna_inquiry_owner', 'public.mcp_oauth_tokens', 'access_token_hash', 'SELECT')
    OR NOT has_column_privilege('purna_inquiry_owner', 'public.mcp_oauth_tokens', 'uid', 'SELECT')
    OR NOT has_column_privilege('purna_inquiry_owner', 'public.mcp_oauth_tokens', 'expires_at', 'SELECT')
    OR NOT has_column_privilege('purna_inquiry_owner', 'public.mcp_oauth_tokens', 'expires_at', 'UPDATE') THEN
    RAISE EXCEPTION 'migration 1039 requires exact protected-owner base-table privileges';
  END IF;

  FOREACH target_table IN ARRAY ARRAY[
    'planner_inquiry_lifecycles',
    'planner_inquiry_evidence_receipts',
    'planner_inquiry_action_reservations',
    'planner_managed_prashna_jobs'
  ] LOOP
    IF NOT EXISTS (
      SELECT 1 FROM pg_class relation
        JOIN pg_namespace namespace ON namespace.oid=relation.relnamespace
        JOIN pg_roles owner ON owner.oid=relation.relowner
       WHERE namespace.nspname='public' AND relation.relname=target_table
         AND relation.relkind IN ('r','p')
         AND owner.rolname='purna_inquiry_owner'
         AND relation.relrowsecurity
    ) THEN
      RAISE EXCEPTION 'migration 1039 requires protected RLS table %', target_table;
    END IF;
  END LOOP;

  FOREACH target_function IN ARRAY ARRAY[
    'public.planner_inquiry_immutable_guard()'::regprocedure,
    'public.create_planner_inquiry_lifecycle(uuid,text,uuid,text,text,text,text,text,text,jsonb,jsonb,text,text,timestamptz)'::regprocedure,
    'public.purge_expired_planner_inquiries_global()'::regprocedure,
    'public.planner_inquiry_action_reservation_guard()'::regprocedure,
    'public.planner_managed_prashna_job_credential_guard()'::regprocedure,
    'public.planner_managed_prashna_job_immutable_guard()'::regprocedure,
    'public.create_planner_managed_prashna_job(uuid,text,text,text,uuid,jsonb)'::regprocedure,
    'public.get_planner_managed_prashna_job(uuid,text,text)'::regprocedure,
    'public.claim_planner_managed_prashna_job(uuid,text,text,text,integer)'::regprocedure,
    'public.update_planner_managed_prashna_job_progress(uuid,text,text,text,jsonb,integer)'::regprocedure,
    'public.complete_planner_managed_prashna_job(uuid,text,text,text,jsonb)'::regprocedure,
    'public.fail_planner_managed_prashna_job(uuid,text,text,text,text)'::regprocedure
  ] LOOP
    IF NOT EXISTS (
      SELECT 1 FROM pg_proc procedure
        JOIN pg_roles owner ON owner.oid=procedure.proowner
       WHERE procedure.oid=target_function AND owner.rolname='purna_inquiry_owner'
    ) THEN
      RAISE EXCEPTION 'migration 1039 requires protected function %', target_function;
    END IF;
  END LOOP;

  IF (
    SELECT count(*) FROM pg_proc procedure
      JOIN pg_namespace namespace ON namespace.oid=procedure.pronamespace
      JOIN pg_roles owner ON owner.oid=procedure.proowner
     WHERE namespace.nspname='public'
       AND procedure.proname = ANY(ARRAY[
         'create_planner_inquiry_lifecycle',
         'purge_expired_planner_inquiries_global',
         'planner_managed_prashna_job_credential_guard',
         'create_planner_managed_prashna_job',
         'get_planner_managed_prashna_job',
         'claim_planner_managed_prashna_job',
         'update_planner_managed_prashna_job_progress',
         'complete_planner_managed_prashna_job',
         'fail_planner_managed_prashna_job'
       ])
       AND procedure.prosecdef
       AND 'search_path=pg_catalog, pg_temp'=ANY(procedure.proconfig)
       AND owner.rolname='purna_inquiry_owner'
  ) <> 9 THEN
    RAISE EXCEPTION 'migration 1039 requires nine fixed-search-path SECURITY DEFINER functions';
  END IF;

  EXECUTE format('REVOKE purna_inquiry_owner FROM %I', session_user);

  IF EXISTS (
    SELECT 1 FROM pg_auth_members membership
      JOIN pg_roles role ON role.oid=membership.roleid OR role.oid=membership.member
     WHERE role.rolname='purna_inquiry_owner'
  ) THEN
    RAISE EXCEPTION 'migration 1039 protected-owner membership cleanup did not converge';
  END IF;
END $$;

COMMIT;

-- No DOWN migration: restoring a runtime-reachable owner is an escalation,
-- not rollback. Reprovision temporary membership only through the reviewed
-- one-shot preflight for a separately numbered ownership migration.
