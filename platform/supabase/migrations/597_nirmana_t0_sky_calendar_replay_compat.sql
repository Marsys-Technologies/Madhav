-- Migration 597: NIRMĀṆA T0 sky-calendar replay compatibility
--
-- REPLAY ORDER: platform/scripts/migrate.ts schedules this exact file immediately
-- before 594_nirmana_t0_sky_calendar_contract.sql.  The historical live rename
-- from bg_sky_events to bg_sky_calendar was not retained as a replayable file;
-- without this compatibility step, a blank database cannot reach migration 594.
--
-- EXISTING PRODUCTION: when only public.bg_sky_calendar exists this is a no-op.
-- SAFETY: when both relations exist, stop instead of choosing, merging, deleting,
-- or silently preferring one.  In particular, two populated relations are an
-- ambiguous split-brain state that requires an operator decision.
-- IDEMPOTENT: old-only -> one rename; canonical-only -> no-op; all other states
-- fail closed before mutation.

BEGIN;

DO $$
DECLARE
  legacy_relation regclass := to_regclass('public.bg_sky_events');
  canonical_relation regclass := to_regclass('public.bg_sky_calendar');
  legacy_has_rows boolean := false;
  canonical_has_rows boolean := false;
BEGIN
  IF legacy_relation IS NOT NULL AND canonical_relation IS NOT NULL THEN
    EXECUTE 'SELECT EXISTS (SELECT 1 FROM public.bg_sky_events LIMIT 1)'
      INTO legacy_has_rows;
    EXECUTE 'SELECT EXISTS (SELECT 1 FROM public.bg_sky_calendar LIMIT 1)'
      INTO canonical_has_rows;
    RAISE EXCEPTION
      'migration 597 refuses ambiguous sky-calendar relations: bg_sky_events rows=%, bg_sky_calendar rows=%',
      legacy_has_rows, canonical_has_rows;
  END IF;

  IF legacy_relation IS NOT NULL THEN
    ALTER TABLE public.bg_sky_events RENAME TO bg_sky_calendar;
  ELSIF canonical_relation IS NULL THEN
    RAISE EXCEPTION
      'migration 597 requires exactly one sky-calendar relation: neither public.bg_sky_events nor public.bg_sky_calendar exists';
  END IF;

  IF to_regclass('public.bg_sky_calendar') IS NULL
     OR to_regclass('public.bg_sky_events') IS NOT NULL THEN
    RAISE EXCEPTION
      'migration 597 failed to establish public.bg_sky_calendar as the sole sky-calendar relation';
  END IF;
END $$;

COMMIT;
