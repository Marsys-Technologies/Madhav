-- Migration 194: bg_compendium_index target_floor correction
-- Sets target_floor from the PROVISIONAL placeholder (1,755) to the actual
-- emergent build count (7,025) produced by the bg_compendium_index writer.
--
-- Build: 2026-06-09, build_id=b9b1543d-f908-4daf-90cc-5032c651b263
-- Pass A (per-text-per-chapter): 5,795 rows inserted, 0 skipped
-- Pass B (per-text-per-topic): 1,230 rows inserted, 0 skipped, 0 invalid_topic
-- Total in brahma_compendium_index: 7,025
-- Duration: 728.4s
-- Upstream: 8,193 classical_text_chunks (13 texts), 5,442 with topic_tag, 481 reference_topic_tags
--
-- Per CLAUDECODE_BRIEF_BG_COMPENDIUM_INDEX_v1_0.md §3a:
-- "The writer's migration MUST include: UPDATE asset_registry SET target_floor = <actual_produced_count>
--  WHERE asset_id = 'bg_compendium_index'; — replacing 1,755 with the real emergent count."

UPDATE asset_registry
   SET target_floor = 7025
 WHERE asset_id = 'bg_compendium_index';

-- Update asset_throughput to reflect completed build state
-- NOTE: asset_throughput row has chart_id set (not NULL) for this asset;
-- do not filter by chart_id IS NULL.
UPDATE asset_throughput
   SET state       = 'lit',
       rows_written = 7025,
       expected_rows = 7025,
       last_built_at = NOW()
 WHERE asset_id = 'bg_compendium_index';
