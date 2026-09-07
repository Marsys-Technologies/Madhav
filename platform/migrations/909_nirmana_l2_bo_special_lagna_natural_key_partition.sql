-- 909_nirmana_l2_bo_special_lagna_natural_key_partition.sql
--
-- NIRMANA v2.5 -- L2 (Bodha) W4 pre-dispatch. Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Sibling migration to 908 (bo_nakshatra_semantic) -- see that file for the
-- full #1770 EXTENSION RULING / D-CND-27-adjacent partition_undeclared
-- rationale (migrations 868-874, adjudication #2180; bo_sudarshana's own fix,
-- migration 880).
--
-- bo_special_lagna's own ownership, verified directly against
-- pipeline/orchestrator/writers/bo_special_lagna.py's own declared allowlist
-- (BO_SPECIAL_LAGNA_OWNED_SIGNAL_TYPE_CLASSES = ["special_lagna"], line 39)
-- and bodha_writers/special_lagna_emitter.py's row-construction site -- a
-- single signal_type_class, `special_lagna`. Confirmed no overlap: live
-- production (canonical chart) shows exactly 20 rows at
-- signal_type_class='special_lagna' and no other co-writer's class collides
-- with it.

UPDATE asset_registry
   SET natural_key_partition = 'bodha_msr_signals.signal_type_class = special_lagna'
 WHERE asset_id = 'bo_special_lagna'
   AND natural_key_partition IS NULL;
