-- 942_nirmana_l2_bo_drishti_natural_key_partition.sql
--
-- NIRMANA v2.5 -- L2 (Bodha). Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Sibling migration to 941 (bo_drishti output_digest_spec) -- see that
-- migration's header for the full verified account. Unlike every
-- bodha_msr_signals co-writer migrated so far, bodha_question_lenses has
-- exactly ONE writer (bo_drishti), so this partition description is
-- simpler: the whole table is this asset's own slice, no co-writer
-- scoping needed. Declared anyway per the DEP-ASSERT precedent (880/908/
-- 909/910/927/930/939-940): `natural_key_partition` being NULL reads as
-- `freshness_state='unknown'` (reason `partition_undeclared`) regardless
-- of writer exclusivity or build success.

UPDATE asset_registry
   SET natural_key_partition = 'bodha_question_lenses (chart_id, ayanamsha_id, question_type) -- sole writer, chart-wide delete-then-insert, one row per (question_type x ayanamsha)'
 WHERE asset_id = 'bo_drishti'
   AND natural_key_partition IS NULL;
