-- 162_charts_preferred_name_tz_id_idempotent.sql
--
-- Backfills the schema additions from migration 161 that never reached
-- production because the migrate.ts CI step was skipped (PROD_DATABASE_URL
-- secret unset at deploy time). Idempotent — safe to run regardless of
-- whether 161 was previously applied.
--
-- Rollback:
--   ALTER TABLE public.charts
--     DROP COLUMN IF EXISTS preferred_name,
--     DROP COLUMN IF EXISTS timezone_id;

BEGIN;

ALTER TABLE public.charts
  ADD COLUMN IF NOT EXISTS preferred_name TEXT,
  ADD COLUMN IF NOT EXISTS timezone_id    TEXT;

COMMENT ON COLUMN public.charts.preferred_name IS
  'Display name for the native; defaults to first word of name.';

COMMENT ON COLUMN public.charts.timezone_id IS
  'IANA timezone identifier e.g. Asia/Kolkata. Sourced from explicit TZ select.';

COMMIT;
