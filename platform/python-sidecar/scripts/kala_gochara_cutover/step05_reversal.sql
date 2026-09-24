-- step05_reversal.sql — reversal of WP10 runbook step 5 (plan §9: "reverse
-- migration").
--
-- Tranche 1. Restores ka_gochara's and the century's registry fields from the
-- snapshot table written by step05_registry_repin.sql, then drops it.
-- Apply with: psql "$DSN" -f step05_reversal.sql
-- Record the reversal in evidence/step05_evidence.md when used.

BEGIN;

UPDATE asset_registry r
   SET count_sql = s.count_sql,
       clear_tables = s.clear_tables,
       integrity_check_sql = s.integrity_check_sql,
       depends_on = s.depends_on
  FROM kala_gochara_cutover_step05_snapshot s
 WHERE r.asset_id = s.asset_id;

DROP TABLE IF EXISTS kala_gochara_cutover_step05_snapshot;

COMMIT;
