-- Migration 156: drop incorrect build_manifests FK from chart_facts
-- chart_facts.build_id is a free-form build tag shared with the per-chart
-- build pipeline (builds table), not the RAG corpus build_manifests table.
-- The FK was incorrectly pointing to build_manifests, blocking all chart
-- builds from inserting fact rows. Applied directly 2026-05-31; migration
-- recorded for audit trail only.
ALTER TABLE chart_facts DROP CONSTRAINT IF EXISTS chart_facts_build_id_fkey;
