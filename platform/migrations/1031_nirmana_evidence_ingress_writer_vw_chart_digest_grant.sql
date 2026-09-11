-- Migration 1031: grant verifier read access to vw_chart_digest
-- Created: 2026-09-11
--
-- bo_samvada's integrity_check_sql (migration 1029) re-evaluates the live
-- read-side digest as nirmana_evidence_ingress_writer. Production verification
-- proved every referenced relation readable except vw_chart_digest, causing
-- the fail-closed integrity event to return SQLSTATE 42501. This grants only
-- the missing SELECT capability to the existing verifier role.

BEGIN;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_evidence_ingress_writer') THEN
    RAISE EXCEPTION 'migration 1031 requires nirmana_evidence_ingress_writer (migration 632) to already exist';
  END IF;

  IF to_regclass(format('%I.%I', current_schema(), 'vw_chart_digest')) IS NULL THEN
    RAISE EXCEPTION 'migration 1031 requires vw_chart_digest to already exist';
  END IF;

  IF NOT has_table_privilege(
    'nirmana_evidence_ingress_writer',
    format('%I.%I', current_schema(), 'vw_chart_digest'),
    'SELECT'
  ) THEN
    EXECUTE format(
      'GRANT SELECT ON TABLE %I.%I TO nirmana_evidence_ingress_writer',
      current_schema(),
      'vw_chart_digest'
    );
  END IF;
END $$;

COMMIT;
