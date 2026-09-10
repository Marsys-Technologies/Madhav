-- 930_nirmana_l2_bo_laksana_natural_key_partition.sql
--
-- NIRMANA v2.5 -- L2 (Bodha) W4 post-dispatch. Transaction ownership belongs
-- to platform/scripts/migrate.ts.
--
-- Sibling migration to 908/909/910/927 -- see 908 for the full
-- partition_undeclared rationale (migrations 868-874, adjudication #2180;
-- bo_sudarshana's own fix, migration 880). Authored alongside bo_laksana's
-- output-digest spec (migration 929), fixing the same asset_provenance_receipts
-- receipt_state='unknown' block ("partition_undeclared" reason) surfaced by
-- build_run 7c8f2195-5953-4008-8347-e4c99b515a15's completed rebuild.
--
-- bo_laksana owns 15 signal_type_class values (see migration 929's header for
-- the full verified list and cross-check against
-- BO_LAKSANA_OWNED_SIGNAL_TYPE_CLASSES, pipeline/orchestrator/writers/
-- bo_laksana.py:145-160). natural_key_partition is consumed as an opaque
-- descriptive partition_key label (asset_runner.py: `partition_key =
-- natural_key_partition or WHOLE_ASSET_PARTITION`), not machine-parsed --
-- the multi-class "IN (...)" free-text format matches the precedent already
-- live for bo_vargottama_dhana's own two-class partition declaration.

UPDATE asset_registry
   SET natural_key_partition = 'bodha_msr_signals.signal_type_class IN (yoga, dosha, sade_sati, panchanga, karaka_alignment, tradition_specific, parivartana, configuration, varga_pattern, annual, medical, vastu, composite_state, varga_ratification_divergence, bhavat_bhavam_amplifier)'
 WHERE asset_id = 'bo_laksana'
   AND natural_key_partition IS NULL;
