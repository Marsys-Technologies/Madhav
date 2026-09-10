-- 921_nirmana_evidence_ingress_writer_ga_medical_grant.sql
--
-- NIRMĀṆA — same class of gap as migrations 645/646/885/890/898/903: the server-side
-- `integrity_verified` re-evaluation runs each asset's `integrity_check_sql` as
-- `nirmana_evidence_ingress_writer`, which never had `SELECT` on `ga_medical` (its own
-- target table). Discovered live this cycle: `ga_medical`'s first `integrity_verified`
-- submission (build_run 9eb07d35-d42b-4c94-9043-ec8a8411c0a9) failed HTTP 500;
-- `has_table_privilege('nirmana_evidence_ingress_writer', 'ga_medical', 'SELECT')` = false
-- (confirmed via direct DB query before the fix, 42501/aclcheck_error in Cloud Run logs —
-- the exact migration-898/903 signature). `ga_condition_composite` (the other table
-- `ga_medical`'s integrity_check_sql reads via its cross-table join) was already granted by
-- migration 903.
--
-- The GRANT was already applied live ad-hoc this cycle (verified:
-- `has_table_privilege` = true; `ga_medical`'s `integrity_verified` went through
-- immediately afterward, and `asset_frozen` followed, landing L1 at 15/19) — this file is
-- the durable, tracked record; re-apply is idempotent.
--
-- Same additive, existence-checked, SELECT-only pattern as migrations 898/903.

BEGIN;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_evidence_ingress_writer') THEN
    RAISE EXCEPTION 'migration 921 requires nirmana_evidence_ingress_writer (migration 632) to already exist';
  END IF;

  IF to_regclass(format('%I.%I', current_schema(), 'ga_medical')) IS NULL THEN
    RAISE EXCEPTION 'migration 921 requires ga_medical to already exist';
  END IF;

  EXECUTE format('GRANT SELECT ON TABLE %I.%I TO nirmana_evidence_ingress_writer', current_schema(), 'ga_medical');
END $$;

COMMIT;
