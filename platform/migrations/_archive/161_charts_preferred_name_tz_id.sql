-- Migration 161: Add preferred_name and timezone_id to charts
--
-- Context: Stream D (D-S2) form schema extension adds preferred_name and
-- timezone_id to the client creation flow. These columns persist the IANA
-- timezone identifier and the preferred display name for the native.
--
-- Idempotent: ADD COLUMN IF NOT EXISTS guards each statement.
-- Rollback: ALTER TABLE charts DROP COLUMN IF EXISTS preferred_name,
--           ALTER TABLE charts DROP COLUMN IF EXISTS timezone_id;

ALTER TABLE public.charts
  ADD COLUMN IF NOT EXISTS preferred_name TEXT,
  ADD COLUMN IF NOT EXISTS timezone_id    TEXT;

COMMENT ON COLUMN public.charts.preferred_name IS 'Display name for the native; defaults to first word of name.';
COMMENT ON COLUMN public.charts.timezone_id IS 'IANA timezone identifier e.g. Asia/Kolkata. Sourced from explicit TZ select.';
