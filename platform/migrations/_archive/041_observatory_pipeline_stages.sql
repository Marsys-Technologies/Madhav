-- platform/migrations/041_observatory_pipeline_stages.sql
-- Expand the pipeline_stage CHECK constraint on llm_usage_events to include
-- the 'planner', 'title', and 'history_summary' stages that are already
-- present in the PipelineStage TypeScript union but were missing from the DB
-- constraint. The original constraint (migration 038) only allowed:
--   'classify','compose','retrieve','synthesize','audit','other'
-- The manifest_planner OBS-S1 block uses 'planner' — every insert was failing
-- silently against the constraint, which is why only 'synthesize' appeared in
-- the pipeline stage breakdown. This migration fixes that gap and adds headroom
-- for the title and history_summary stages.
--
-- Idempotent: DROP CONSTRAINT IF EXISTS + ADD CONSTRAINT.

BEGIN;

ALTER TABLE llm_usage_events
  DROP CONSTRAINT IF EXISTS llm_usage_events_pipeline_stage_check;

ALTER TABLE llm_usage_events
  ADD CONSTRAINT llm_usage_events_pipeline_stage_check
    CHECK (pipeline_stage IN (
      'classify',
      'compose',
      'retrieve',
      'synthesize',
      'audit',
      'other',
      'planner',
      'title',
      'history_summary'
    ));

COMMIT;
