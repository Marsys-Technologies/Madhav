-- step01_select_grant.sql — WP10 runbook step 1 (plan §9): Phase 1.2 grant.
--
-- SELECT on both v1 archives for `data_plane_builder`. Tranche 1
-- (PRODUCTION_TRANCHE_1_AUTHORIZED). Sheet A-2.
--
-- Apply with:  psql "$DSN" -f step01_select_grant.sql
-- The applying wrapper (any step runner) must have refused the production
-- instance unless PRODUCTION_TRANCHE_1_AUTHORIZED=true — see common.py.
--
-- Gate: privilege listed —
--   SELECT has_table_privilege('data_plane_builder',
--          'public.kala_gochara_windows', 'SELECT')                      -- expect t
--   SELECT has_table_privilege('data_plane_builder',
--          'public.kala_gochara_windows_archive_20260805', 'SELECT')     -- expect t
-- (If the archive relation does not exist in the target, the GRANT
--  fails loudly — that is the gate doing its job; verify the archive name
--  against the live catalog before re-issuing.)
--
-- Reversal:
--   REVOKE SELECT ON kala_gochara_windows FROM data_plane_builder;
--   REVOKE SELECT ON kala_gochara_windows_archive_20260805 FROM data_plane_builder;

BEGIN;

GRANT SELECT ON kala_gochara_windows TO data_plane_builder;
GRANT SELECT ON kala_gochara_windows_archive_20260805 TO data_plane_builder;

-- Gate probe inside the same transaction: fail the apply if the privilege did
-- not land (never trust a silent no-op, §N.8).
DO $$
BEGIN
  IF NOT has_table_privilege('data_plane_builder', 'public.kala_gochara_windows', 'SELECT') THEN
    RAISE EXCEPTION 'step 1 gate failed: data_plane_builder lacks SELECT on kala_gochara_windows';
  END IF;
  IF NOT has_table_privilege('data_plane_builder', 'public.kala_gochara_windows_archive_20260805', 'SELECT') THEN
    RAISE EXCEPTION 'step 1 gate failed: data_plane_builder lacks SELECT on kala_gochara_windows_archive_20260805';
  END IF;
END $$;

COMMIT;
