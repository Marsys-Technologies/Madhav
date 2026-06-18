-- Migration 313: Backfill last_built_at on L0 global asset_throughput records
-- Created: 2026-06-18
-- ─────────────────────────────────────────────────────────────────────────────
-- Root cause:
--
-- Migration 312 fixed stale state for L1 per-chart assets and the stats route
-- was updated to include `OR chart_id IS NULL` so global L0 (bg_*) records are
-- now correctly visible. However, 20 bg_* global throughput records have
-- last_built_at = NULL (never written by the build process at the time they
-- were created), which causes `build_state_stale = true` for every one of them.
--
-- All 20 records have state = 'lit' and correct rows_written > 0 — they are
-- fully built; the timestamp was simply never stamped.
--
-- Fix: set last_built_at = NOW() for all global (chart_id IS NULL) throughput
-- records that are lit with rows > 0 but have a null timestamp.
-- This is a backfill stamp — the data is current; the timestamp gap is the bug.
-- ─────────────────────────────────────────────────────────────────────────────

BEGIN;

UPDATE asset_throughput
SET    last_built_at = NOW()
WHERE  chart_id IS NULL          -- global L0 records only
  AND  state = 'lit'
  AND  rows_written > 0
  AND  last_built_at IS NULL;

COMMIT;
