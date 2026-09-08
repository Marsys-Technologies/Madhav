-- 922_nirmana_evidence_ingress_writer_ga_vastu_grant.sql
--
-- NIRMĀṆA — same class of gap as migrations 645/646/885/890/898/903/921: the server-side
-- `integrity_verified` re-evaluation runs each asset's `integrity_check_sql` as
-- `nirmana_evidence_ingress_writer`, which never had `SELECT` on `ga_vastu`'s own target
-- table `ga_vastu_planet_direction_map`. Discovered pre-emptively this cycle (before
-- dispatching `ga_vastu`'s rebuild, per the migration-921/`ga_medical` precedent): direct
-- DB query confirmed `has_table_privilege('nirmana_evidence_ingress_writer',
-- 'ga_vastu_planet_direction_map', 'SELECT')` = false, while the OTHER table
-- `ga_vastu`'s `integrity_check_sql` cross-table-joins against
-- (`ga_condition_composite`) was already granted by migration 903.
--
-- The GRANT was applied live ad-hoc this cycle (verified: `has_table_privilege` = true)
-- ahead of dispatching the `integrity_verified` submission, to avoid the wasted HTTP 500 +
-- log-dig the `ga_medical` cycle hit — this file is the durable, tracked record; re-apply
-- is idempotent.
--
-- Same additive, existence-checked, SELECT-only pattern as migrations 898/903/921.

BEGIN;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_evidence_ingress_writer') THEN
    RAISE EXCEPTION 'migration 922 requires nirmana_evidence_ingress_writer (migration 632) to already exist';
  END IF;

  IF to_regclass(format('%I.%I', current_schema(), 'ga_vastu_planet_direction_map')) IS NULL THEN
    RAISE EXCEPTION 'migration 922 requires ga_vastu_planet_direction_map to already exist';
  END IF;

  EXECUTE format('GRANT SELECT ON TABLE %I.%I TO nirmana_evidence_ingress_writer', current_schema(), 'ga_vastu_planet_direction_map');
END $$;

COMMIT;
