-- 944_nirmana_l2_bo_pratijna_natural_key_partition.sql
--
-- NIRMANA v2.5 -- L2 (Bodha). Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Sibling migration to 943 (bo_pratijna output_digest_spec) -- see that
-- migration's header for the full verified account. bodha_pratijna has
-- exactly ONE writer (bo_pratijna.py; the two sibling module files in the
-- same family are helper libraries with no @register and no INSERT/UPDATE
-- of their own), so this partition description is the writer's own
-- declared ON CONFLICT target, not an inference. Declared anyway per the
-- DEP-ASSERT precedent (880/908/909/910/927/930/939-940/941-942):
-- `natural_key_partition` being NULL reads as `freshness_state='unknown'`
-- (reason `partition_undeclared`) regardless of writer exclusivity or
-- build success.

UPDATE asset_registry
   SET natural_key_partition = 'bodha_pratijna (chart_id, ayanamsha_id, event_class_id) -- sole writer, ON CONFLICT (chart_id, ayanamsha_id, event_class_id) DO UPDATE declared directly in the writer''s own INSERT statement'
 WHERE asset_id = 'bo_pratijna'
   AND natural_key_partition IS NULL;
