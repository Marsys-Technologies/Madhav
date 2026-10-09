-- 1344_charts_build_ayanamshas_column.sql
--
-- ONE_AYANAMSHA P2-1 (SS N-309/N-315/N-316): the per-chart source of "which ayanamshas does this chart build".
-- charts.build_ayanamshas text[]: NULL = the five canonical ids (lahiri_chitrapaksha, true_chitra, krishnamurti, raman,
-- surya_siddhanta_classical), i.e. today's behaviour for every chart; a non-NULL value is the exact set the chart builds, e.g.
-- ARRAY['lahiri_chitrapaksha'] for chart 482012f1 after the Lahiri-only switch. This migration only ADDS the column (all rows NULL);
-- nothing reads a non-NULL value until the later phases write one. Readers: brahmagyan/ayanamsha_scope.py (ayanamshas_for_chart,
-- which already probes information_schema for this column) and the chart-aware integrity checks of migrations 1345-1348.
--
-- CHECK charts_build_ayanamshas_check: NULL is allowed; otherwise the array is NOT empty (an empty list must never silently widen to
-- five or narrow to nothing) and every element is one of the five ids (<@ is false for an array holding a NULL element, so NULL
-- elements are rejected too). Added through a guarded DO block (idempotent: skipped if the named constraint already exists).
-- Duplicates inside the array are tolerated by the constraint (the helper and the integrity checks de-duplicate).
--
-- ROUTINE PATH. public.charts is a plain table owned by amjis_app (the routine migration role), no event triggers, no dependent views
-- (read-only verification by SS 2026-10-10), existing CHECKs charts_chart_type_check and charts_role_check. ALTER TABLE ... ADD COLUMN
-- IF NOT EXISTS and ADD CONSTRAINT take a brief ACCESS EXCLUSIVE lock (lock_timeout 5s below); the column is nullable with no default,
-- so there is no table rewrite and the CHECK is validated against all-NULL rows. No CREATE TABLE/INDEX/FUNCTION/TRIGGER in public, no
-- GRANT ON SCHEMA (check_public_schema_migration_privilege.py reports 0 findings).
--
-- TIMING (SS N-316). This column may apply EARLIER than 1345-1348 (those apply in the Phase 4 window). It does not touch the staling
-- trigger (migration 596 watches asset_registry columns; this is a column of charts). Transaction ownership belongs to
-- platform/scripts/migrate.ts (no BEGIN/COMMIT here).
--
-- VERIFICATION (as suvarna_reader, after the apply): SELECT column_name, data_type FROM information_schema.columns WHERE table_name =
-- 'charts' AND column_name = 'build_ayanamshas';  SELECT conname FROM pg_constraint WHERE conname = 'charts_build_ayanamshas_check';
-- SELECT count(*) FROM charts WHERE build_ayanamshas IS NOT NULL;  (expect 0 until the Lahiri-only switch).
--
-- ROLLBACK (not executed by migrate.ts): ALTER TABLE charts DROP CONSTRAINT IF EXISTS charts_build_ayanamshas_check;
-- ALTER TABLE charts DROP COLUMN IF EXISTS build_ayanamshas;  (only while no chart holds a non-NULL value and nothing reads it).

SET LOCAL lock_timeout = '5s';

ALTER TABLE charts ADD COLUMN IF NOT EXISTS build_ayanamshas text[];

DO $c$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint
                  WHERE conname = 'charts_build_ayanamshas_check' AND conrelid = 'public.charts'::regclass) THEN
    ALTER TABLE charts ADD CONSTRAINT charts_build_ayanamshas_check CHECK (
      build_ayanamshas IS NULL
      OR (cardinality(build_ayanamshas) >= 1
          AND build_ayanamshas <@ ARRAY['lahiri_chitrapaksha','true_chitra','krishnamurti','raman','surya_siddhanta_classical']::text[])
    );
  END IF;
END
$c$;

COMMENT ON COLUMN charts.build_ayanamshas IS
  'ONE_AYANAMSHA: the ayanamsha ids this chart builds. NULL = the five canonical ids (default). Non-NULL = exactly that set (non-empty, ids from the five). Read by brahmagyan.ayanamsha_scope.ayanamshas_for_chart and the chart-aware integrity checks (migrations 1345-1348).';
