-- step05_reversal.sql — reversal of WP10 runbook step 5 (plan §9: "reverse
-- migration").
--
-- Tranche 1. Restores ka_gochara's and the century's registry fields from the
-- snapshot table written by step05_registry_repin.sql, then drops it.
-- Apply with: psql "$DSN" -f step05_reversal.sql
-- Record the reversal in evidence/step05_evidence.md when used.

BEGIN;

-- clear_tables: the snapshot column is TEXT (1091, applied — not editable)
-- holding the array's text form ('{a, b}'), while production asset_registry.
-- clear_tables is text[]. text -> text[] has no cast, so the literal restore
-- fails against production's real type (verified 2026-09-27 on the disposable
-- rehearsal DB after the ADK-0013 harness fidelity fix); parse the form back.
UPDATE asset_registry r
   SET count_sql = s.count_sql,
       clear_tables = (SELECT array_agg(btrim(e))
                         FROM unnest(string_to_array(btrim(s.clear_tables, '{}'), ',')) AS e),
       integrity_check_sql = s.integrity_check_sql,
       depends_on = s.depends_on
  FROM kala_gochara_cutover_step05_snapshot s
 WHERE r.asset_id = s.asset_id;

DROP TABLE IF EXISTS kala_gochara_cutover_step05_snapshot;

COMMIT;
