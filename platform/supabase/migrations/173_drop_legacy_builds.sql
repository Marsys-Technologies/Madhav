-- Migration 173: Drop legacy build orchestration tables
--
-- builds, build_steps, and build_events are superseded by the new
-- build_runs / asset_throughput orchestrator (migration 171 + 169).
-- All API routes that wrote to these tables are now 410 Gone stubs.
-- brahma_pipeline.py no longer writes to these tables.

DROP TABLE IF EXISTS public.build_events  CASCADE;
DROP TABLE IF EXISTS public.build_steps   CASCADE;
DROP TABLE IF EXISTS public.builds        CASCADE;
