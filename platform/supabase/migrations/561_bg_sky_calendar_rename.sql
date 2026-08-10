-- Migration 561: rename bg_sky_events → bg_sky_calendar
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
