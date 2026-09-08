-- 947_nirmana_l2_bo_grounding_natural_key_partition.sql
--
-- NIRMANA v2.5 -- L2 (Bodha). Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Sibling migration to 946 (bo_grounding output_digest_spec) -- see that
-- migration's header for the full verified account. bodha_grounding_matches
-- has exactly ONE writer (bo_grounding.py; confirmed via grep, no other
-- file INSERTs/UPDATEs the table). Declared per the DEP-ASSERT precedent
-- (880/908/909/910/927/930/939-940/941-942/943-944): natural_key_partition
-- being NULL reads as freshness_state='unknown' (reason
-- 'partition_undeclared') regardless of writer exclusivity or build
-- success -- true here even though the asset has 0 rows fleet-wide as of
-- this cycle (see 946's header), since the partition declaration itself
-- doesn't depend on the table currently being populated.

UPDATE asset_registry
   SET natural_key_partition = 'bodha_grounding_matches (chart_id, ayanamsha_id, target_kind, target_id) -- sole writer; live table unique constraint is (chart_id, ayanamsha_id, target_kind, target_id, build_id), build_id excluded here as the orchestrator''s per-run identifier (fresh every rebuild); delete-then-insert (replace_prior_grounding_matches) is scoped to (chart_id, ayanamsha_id) only, so only one build''s rows exist at a time per that slice'
 WHERE asset_id = 'bo_grounding'
   AND natural_key_partition IS NULL;
