-- step03_reversal.sql — reversal of WP10 runbook step 3 (plan §9: "DROP
-- trigger + restore is_active (both recorded)").
--
-- Tranche 1. Apply with: psql "$DSN" -f step03_reversal.sql
-- Record the reversal in evidence/step03_evidence.md when used.

BEGIN;

DROP TRIGGER IF EXISTS trg_kgw_generation_guard_row ON kala_gochara_windows;
DROP TRIGGER IF EXISTS trg_kgw_generation_guard_truncate ON kala_gochara_windows;
DROP FUNCTION IF EXISTS kala_gochara_generation_guard();

-- The build_protected_assets re-seed rows are left in place deliberately:
-- migration 540's asset-keyed layer pre-dates step 3 and its removal is a
-- separate, older decision (588 removed one such row set under its own
-- authority). Step 3's reversal restores the trigger/lifecycle state, not a
-- reduction of protection.

UPDATE asset_registry
   SET is_active = true
 WHERE asset_id = 'ka_gochara_v3_century_materialize';

COMMIT;
