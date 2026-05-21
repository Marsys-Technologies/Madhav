-- platform/supabase/migrations/069_performance_wiring_fixes.sql
-- Migration: PERF-S1 — three column additions to performance_queries.
-- Brief: PERF-S1_BRIEF_v1_0.md (§H.1 of CAPABILITY_COVERAGE_AND_PERFORMANCE_AUDIT_v1_0.md)
-- Created: 2026-05-21.
--
-- Adds:
--   (b) retrieval_scores jsonb        — per-tool top-1 score map (tool_name → score)
--   (c) compose_bundle_latency_ms int — bundle-assembly stage latency
--   (d) latency_complete boolean      — false when synthesis timestamps are non-finite

BEGIN;

-- (b) Per-tool top-score map. Null when no tools ran or scores were not captured.
ALTER TABLE performance_queries
  ADD COLUMN IF NOT EXISTS retrieval_scores jsonb;

COMMENT ON COLUMN performance_queries.retrieval_scores IS
  'Map of tool_name → top-1 retrieval score for every tool that ran on this query. '
  'Null when no tools produced a scoreable result. Introduced PERF-S1.';

-- (c) Bundle-assembly stage latency. Null for rows ingested before PERF-S1.
ALTER TABLE performance_queries
  ADD COLUMN IF NOT EXISTS compose_bundle_latency_ms integer;

COMMENT ON COLUMN performance_queries.compose_bundle_latency_ms IS
  'Latency of the compose_bundle pipeline stage in milliseconds. '
  'Null for rows ingested before the PERF-S1 ingestion update, or when the stage '
  'timing was not threaded through to the audit consumer. Introduced PERF-S1.';

-- (d) Latency completeness flag. Defaults to true so pre-existing rows (which were
--     inserted with a computed total, even if that total was 0 for bad timestamps)
--     are not retroactively marked incomplete.
ALTER TABLE performance_queries
  ADD COLUMN IF NOT EXISTS latency_complete boolean NOT NULL DEFAULT true;

COMMENT ON COLUMN performance_queries.latency_complete IS
  'False when the latency_total_ms computation could not be completed because '
  'synthesis timestamps were missing or produced a non-finite difference. '
  'Introduced PERF-S1 to replace the silent null→0 coercion.';

COMMIT;
