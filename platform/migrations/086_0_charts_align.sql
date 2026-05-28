-- 086_0_charts_align.sql
-- Bring the LEGACY pre-modernization `charts` table forward into the
-- modernization-arc shape, non-destructively, so migrations 086–089 can land
-- without touching the existing data.
--
-- Origin: OPERATOR_CLEANUP_HALT_LOG.md §2 (schema-design impedance) +
-- OPERATOR_CLEANUP_V1_2_PATCH_BRIEF.md §2(a). Halt root cause: mig 086 was
-- authored assuming a greenfield `charts(chart_id TEXT PRIMARY KEY, role, ...)`
-- but prod is `charts(id UUID PK, birth_date, birth_time, ...)`. CREATE TABLE
-- IF NOT EXISTS was a no-op so the new-shape columns were never created, and
-- the next statement `CREATE INDEX ... ON charts(role)` failed.
--
-- Design (patch brief §2(a)):
--   * `chart_id` is UUID — matches legacy PK `id UUID` 1:1 so the FK target
--     type stays index-friendly and joins remain efficient. The 086 family is
--     patched in lockstep (TEXT → UUID on every chart_id column).
--   * Legacy `id` stays as PK to preserve every existing FK that already
--     references `charts(id)` (e.g. `chart_grants.chart_id → charts.id`).
--     `chart_id` becomes a secondary uniquely-indexed key that 086+ FK to.
--   * `role` allowed values match mig 086 line 53 intent: 'native', 'tertiary',
--     'fixture'. The one prod row (FORENSIC native, UUID
--     362f9f17-95a5-490b-a5a7-027d3e0efda0) gets role='native'; any
--     hypothetical future row prior to apply gets 'tertiary'.
--   * `created_at_iso` is TIMESTAMPTZ (the patch brief and the modernization
--     arc use _iso as a naming convention for ISO 8601 / RFC 3339 timestamps;
--     TIMESTAMPTZ already serializes to RFC 3339 over JSON, so no separate
--     TEXT field is needed).
--
-- Idempotent: every ADD COLUMN guards with IF NOT EXISTS; every CREATE INDEX
-- guards with IF NOT EXISTS; the CHECK constraint is added under a DO $$ ...
-- EXISTS guard so re-running this migration is safe.
--
-- ROLLBACK: see end of file. The pre-Phase-C cloud-sql backup
-- `1779968691961` (and the fresh 'pre-v1.2-patch-cleanup' backup taken at
-- the start of this session) remains the operator-grade rollback target.

BEGIN;

-- ─── 1. Add the modernization-arc columns ───────────────────────────────────
ALTER TABLE charts
  ADD COLUMN IF NOT EXISTS chart_id        UUID,
  ADD COLUMN IF NOT EXISTS role            TEXT,
  ADD COLUMN IF NOT EXISTS created_at_iso  TIMESTAMPTZ;

-- ─── 2. Backfill ────────────────────────────────────────────────────────────
-- chart_id := id (1:1). UUID-to-UUID copy; idempotent because we guard on
-- chart_id IS NULL.
UPDATE charts
   SET chart_id = id
 WHERE chart_id IS NULL;

-- role: FORENSIC native gets 'native'; anything else gets 'tertiary'. The
-- WHERE role IS NULL guard makes this idempotent.
UPDATE charts
   SET role = CASE
                WHEN id::text = '362f9f17-95a5-490b-a5a7-027d3e0efda0'
                  THEN 'native'
                ELSE 'tertiary'
              END
 WHERE role IS NULL;

-- created_at_iso := created_at (timestamptz-to-timestamptz). Guard on NULL.
UPDATE charts
   SET created_at_iso = created_at
 WHERE created_at_iso IS NULL;

-- ─── 3. Tighten to NOT NULL now that backfill is complete ───────────────────
ALTER TABLE charts
  ALTER COLUMN chart_id        SET NOT NULL,
  ALTER COLUMN role            SET NOT NULL,
  ALTER COLUMN created_at_iso  SET NOT NULL;

-- ─── 4. Indexes ─────────────────────────────────────────────────────────────
-- chart_id needs UNIQUE so it can serve as an FK target for 086–089.
CREATE UNIQUE INDEX IF NOT EXISTS uq_charts_chart_id ON charts(chart_id);

-- Role lookup index (matches mig 086 step-35 intent — but here as a real
-- effective index, since 086's identical CREATE INDEX statement is now a
-- no-op against the aligned schema).
CREATE INDEX IF NOT EXISTS idx_charts_role ON charts(role);

-- ─── 5. Role CHECK constraint (matches mig 086 line 53) ─────────────────────
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'charts_role_check'
  ) THEN
    ALTER TABLE charts
      ADD CONSTRAINT charts_role_check
      CHECK (role IN ('native', 'tertiary', 'fixture'));
  END IF;
END $$;

COMMIT;

-- ─── ROLLBACK (commented; manual operator action) ───────────────────────────
-- BEGIN;
-- ALTER TABLE charts DROP CONSTRAINT IF EXISTS charts_role_check;
-- DROP INDEX IF EXISTS idx_charts_role;
-- DROP INDEX IF EXISTS uq_charts_chart_id;
-- ALTER TABLE charts ALTER COLUMN chart_id        DROP NOT NULL;
-- ALTER TABLE charts ALTER COLUMN role            DROP NOT NULL;
-- ALTER TABLE charts ALTER COLUMN created_at_iso  DROP NOT NULL;
-- ALTER TABLE charts
--   DROP COLUMN IF EXISTS chart_id,
--   DROP COLUMN IF EXISTS role,
--   DROP COLUMN IF EXISTS created_at_iso;
-- COMMIT;
