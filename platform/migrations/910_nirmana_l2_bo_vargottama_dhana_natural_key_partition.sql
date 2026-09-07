-- 910_nirmana_l2_bo_vargottama_dhana_natural_key_partition.sql
--
-- NIRMANA v2.5 -- L2 (Bodha) W4 pre-dispatch. Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Sibling migration to 908/909 -- see 908 for the full #1770 EXTENSION
-- RULING / partition_undeclared rationale (migrations 868-874, adjudication
-- #2180; bo_sudarshana's own fix, migration 880).
--
-- bo_vargottama_dhana's own ownership, verified directly against
-- pipeline/orchestrator/writers/bo_vargottama_dhana.py's own declared
-- allowlist (BO_VARGOTTAMA_DHANA_OWNED_SIGNAL_TYPE_CLASSES =
-- ["vargottama_amplification", "dhana_axis"], line 42) and bodha_writers/
-- vargottama_dhana_emitter.py's two row-construction functions
-- (build_vargottama_rows, build_dhana_axis_rows) -- TWO signal_type_classes,
-- unlike its five siblings' single class each. Confirmed no overlap: live
-- production (canonical chart) shows exactly 4 rows at
-- signal_type_class='vargottama_amplification' and 10 rows at
-- signal_type_class='dhana_axis' (14 total, matching the #1770 extension
-- ruling's own disclosed estimate), neither colliding with any other
-- co-writer's class.

UPDATE asset_registry
   SET natural_key_partition = 'bodha_msr_signals.signal_type_class IN (vargottama_amplification, dhana_axis)'
 WHERE asset_id = 'bo_vargottama_dhana'
   AND natural_key_partition IS NULL;
