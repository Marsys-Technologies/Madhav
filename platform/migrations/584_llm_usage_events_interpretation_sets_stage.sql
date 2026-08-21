-- Migration 584: widen llm_usage_events_pipeline_stage_check to allow 'interpretation_sets'.
--
-- PARIPRASHNA-P3-PREFLIGHT Part E (DD-19). interpretation/worker.ts's LLM
-- call site now writes real llm_usage_events rows tagged
-- pipeline_stage='interpretation_sets' (see platform/src/lib/pariprashna/
-- interpretation/worker.ts's callOnce + platform/src/lib/llm/observability/
-- types.ts's PipelineStage union). Without this migration, every one of
-- those writes fails the existing CHECK constraint and is silently
-- swallowed by persistObservation()'s own never-throws-on-observability-
-- failure discipline — the code fix would appear to work while writing
-- zero real rows, the exact §N.8 defect class this campaign keeps finding.
--
-- Idempotent: DROP CONSTRAINT IF EXISTS + unconditional ADD CONSTRAINT,
-- matching the established pattern (328_ka_transit_almanac_retired.sql).
ALTER TABLE llm_usage_events DROP CONSTRAINT IF EXISTS llm_usage_events_pipeline_stage_check;
ALTER TABLE llm_usage_events ADD CONSTRAINT llm_usage_events_pipeline_stage_check
  CHECK (pipeline_stage = ANY (ARRAY[
    'classify'::text,
    'compose'::text,
    'retrieve'::text,
    'synthesize'::text,
    'audit'::text,
    'other'::text,
    'planner'::text,
    'title'::text,
    'history_summary'::text,
    'interpretation_sets'::text
  ]));
