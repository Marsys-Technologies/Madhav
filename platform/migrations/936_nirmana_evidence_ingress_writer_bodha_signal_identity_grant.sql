-- 936_nirmana_evidence_ingress_writer_bodha_signal_identity_grant.sql
--
-- NIRMĀṆA — same class of gap as migrations 645/646/885/890/898/903/921/922/923: the
-- server-side `integrity_verified` re-evaluation runs each asset's `integrity_check_sql` as
-- `nirmana_evidence_ingress_writer`. Migration 931 gave `bo_laksana` a real chart-agnostic
-- `integrity_check_sql` that calls `bodha_signal_identity(chart_id, ayanamsha_id,
-- signal_type_id, varga_id, configuration_jsonb)` (the migration-661 identity function) to
-- assert ratcheting identity conformance. That function's EXECUTE privilege was never granted
-- to `nirmana_evidence_ingress_writer` (only the owner `amjis_app` has it; PUBLIC revoked).
--
-- Discovered live this cycle by an independent verifier subagent attempting to freeze
-- `bo_laksana`: `integrity_verified` returned a generic HTTP 500 (uncaught exception, not a
-- validation rejection) because `collectIntegrityObservation`'s detector-SQL query raised
-- Postgres `permission denied for function bodha_signal_identity` under that role. Confirmed
-- directly: `has_function_privilege('nirmana_evidence_ingress_writer',
-- 'bodha_signal_identity(uuid,text,text,text,jsonb)', 'EXECUTE')` = false before this migration.
--
-- Same additive, existence-checked pattern as migrations 898/903/921/922/923, adapted for a
-- FUNCTION grant (EXECUTE) instead of a TABLE grant (SELECT) since the check calls a function,
-- not a bare SELECT on a table this role lacked.

BEGIN;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_evidence_ingress_writer') THEN
    RAISE EXCEPTION 'migration 936 requires nirmana_evidence_ingress_writer (migration 632) to already exist';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = current_schema()
      AND p.proname = 'bodha_signal_identity'
      AND pg_get_function_identity_arguments(p.oid) = 'p_chart_id uuid, p_ayanamsha_id text, p_signal_type_id text, p_varga_id text, p_configuration jsonb'
  ) THEN
    RAISE EXCEPTION 'migration 936 requires bodha_signal_identity(uuid,text,text,text,jsonb) (migration 661) to already exist';
  END IF;

  EXECUTE format(
    'GRANT EXECUTE ON FUNCTION %I.bodha_signal_identity(uuid,text,text,text,jsonb) TO nirmana_evidence_ingress_writer',
    current_schema()
  );
END $$;

COMMIT;
