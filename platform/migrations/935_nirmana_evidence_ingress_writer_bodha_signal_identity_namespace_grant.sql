-- 935_nirmana_evidence_ingress_writer_bodha_signal_identity_namespace_grant.sql
--
-- NIRMĀṆA — follow-up to migration 934, same defect class as 645/646/885/890/898/903/
-- 921/922/923/934. Migration 934 granted `nirmana_evidence_ingress_writer` EXECUTE on
-- `bodha_signal_identity(uuid,text,text,text,jsonb)` (the identity function bo_laksana's
-- migration-931 `integrity_check_sql` calls), but `integrity_verified` for `bo_laksana` still
-- failed with HTTP 500 afterward.
--
-- Root cause, confirmed live via the actual Postgres error surfaced through Cloud Run logs
-- (`permission denied for function bodha_signal_identity_namespace`, code 42501, `where: 'SQL
-- function "bodha_signal_identity" during startup'`): `bodha_signal_identity(...)` is
-- `LANGUAGE sql` and SECURITY INVOKER (not SECURITY DEFINER), and its body calls a second,
-- separate zero-arg helper function `bodha_signal_identity_namespace()` (returns a fixed UUID
-- constant). Because the outer function runs with the CALLER's privileges, Postgres separately
-- checks the caller's own EXECUTE grant on the inner function too -- granting only the outer
-- function (migration 934) was not sufficient. Confirmed directly:
-- `has_function_privilege('nirmana_evidence_ingress_writer', 'bodha_signal_identity_namespace()',
-- 'EXECUTE')` = false before this migration (outer function's grant from 934 reads true).
--
-- Same additive, existence-checked FUNCTION-grant pattern as migration 934.

BEGIN;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_evidence_ingress_writer') THEN
    RAISE EXCEPTION 'migration 935 requires nirmana_evidence_ingress_writer (migration 632) to already exist';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = current_schema()
      AND p.proname = 'bodha_signal_identity_namespace'
      AND pg_get_function_identity_arguments(p.oid) = ''
  ) THEN
    RAISE EXCEPTION 'migration 935 requires bodha_signal_identity_namespace() to already exist';
  END IF;

  EXECUTE format(
    'GRANT EXECUTE ON FUNCTION %I.bodha_signal_identity_namespace() TO nirmana_evidence_ingress_writer',
    current_schema()
  );
END $$;

COMMIT;
