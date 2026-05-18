-- Migration 065: Add domains_affected to l25_msr_signals
-- Rationale: multi_school_signal_lookup tool queries msr.domains_affected for
-- domain-level filtering and topic-text matching. The column was omitted from
-- the initial l25_msr_signals schema. Populated post-migration by Phase 2A
-- seeding script from 06_LEARNING_LAYER/OBSERVATIONS/msr_domain_buckets.json.
-- 2026-05-18 (Phase 2A M9 fix, analysis/backend-data-pipeline-perf-audit).

ALTER TABLE l25_msr_signals
  ADD COLUMN IF NOT EXISTS domains_affected text[] DEFAULT ARRAY[]::text[];

CREATE INDEX IF NOT EXISTS idx_l25_msr_domains
  ON l25_msr_signals USING gin(domains_affected);
