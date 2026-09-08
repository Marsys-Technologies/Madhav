-- Migration 934: rename bg_sky_events → bg_sky_calendar
-- ==========================================================
-- Root cause: migration 473 (473_bg_sky_calendar.sql) created the table as
-- `bg_sky_events` instead of `bg_sky_calendar`. All subsequent references
-- (migrations 485/494/538/544 comments, migration 557 GRANT, the
-- bg_sky_calendar.py writer, and asset_registry.count_sql) use the name
-- `bg_sky_calendar`. Migration 557 fails at deploy time because the GRANT
-- targets a table that does not exist under that name.
--
-- Fix: rename the physical table and update asset_registry.count_sql.
-- Indexes keep their original names (bg_sky_events_*) — this is fine;
-- Postgres index names are decorative for correctness purposes.
--
-- Originally authored as migration 561 (PR #1180, 2026-08-10); renumbered to
-- 934 because 561 was independently claimed by 561_gochara_v3_calibration.sql
-- in the interim (migration_number_guard.ts E2 collision) and the original PR
-- branch's other file (SAMPURTI_STATE.md) had drifted into an unrelated,
-- long-stale merge conflict against main — this file carries only the
-- migration, unchanged in substance, no other diff.
--
-- The rename was ALSO applied manually to production on 2026-08-10 (see
-- PR #1180's own description); this migration is verified idempotent no-op
-- against current production state (bg_sky_calendar already exists,
-- bg_sky_events does not, count_sql already canonical) — it exists to close
-- the migration-ledger gap so a fresh bootstrap / DR restore also lands on
-- the canonical table name, not to change live production behavior.
--
-- §N.4: surgical, verified. NEVER edit this file after it has been applied.
-- Idempotency: the DO block makes the rename a no-op if already applied.

BEGIN;

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_tables WHERE schemaname='public' AND tablename='bg_sky_events')
     AND NOT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname='public' AND tablename='bg_sky_calendar')
  THEN
    ALTER TABLE bg_sky_events RENAME TO bg_sky_calendar;
  END IF;
END
$$;

-- Update count_sql in asset_registry to use the canonical name
UPDATE asset_registry
SET count_sql = 'SELECT COUNT(*) FROM bg_sky_calendar'
WHERE asset_id = 'bg_sky_calendar'
  AND count_sql = 'SELECT COUNT(*) FROM bg_sky_events';

COMMIT;
