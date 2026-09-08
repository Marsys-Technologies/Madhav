-- 923_nirmana_evidence_ingress_writer_ga_vichara_grant.sql
--
-- NIRMĀṆA — same class of gap as migrations 645/646/885/890/898/903/921/922: the server-side
-- `integrity_verified` re-evaluation runs each asset's `integrity_check_sql` as
-- `nirmana_evidence_ingress_writer`, which never had `SELECT` on `ga_vichara`'s own target
-- table `chart_vichara`. Discovered pre-emptively this cycle (before dispatching `ga_vichara`'s
-- rebuild, per the migration-921/922 precedent): direct DB query confirmed
-- `has_table_privilege('nirmana_evidence_ingress_writer', 'chart_vichara', 'SELECT')` = false.
--
-- The GRANT was applied live ad-hoc this cycle (verified: `has_table_privilege` = true) ahead
-- of dispatching the rebuild, to avoid the wasted HTTP 500 + log-dig prior cycles hit — this
-- file is the durable, tracked record; re-apply is idempotent.
--
-- Same additive, existence-checked, SELECT-only pattern as migrations 898/903/921/922.

BEGIN;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_evidence_ingress_writer') THEN
    RAISE EXCEPTION 'migration 923 requires nirmana_evidence_ingress_writer (migration 632) to already exist';
  END IF;

  IF to_regclass(format('%I.%I', current_schema(), 'chart_vichara')) IS NULL THEN
    RAISE EXCEPTION 'migration 923 requires chart_vichara to already exist';
  END IF;

  EXECUTE format('GRANT SELECT ON TABLE %I.%I TO nirmana_evidence_ingress_writer', current_schema(), 'chart_vichara');
END $$;

COMMIT;
