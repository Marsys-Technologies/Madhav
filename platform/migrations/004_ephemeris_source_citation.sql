-- brahmagyan.ephemeris — Gate-3 fix: add source_citation column.
-- Gate-3 requires: source_citation = 'SwissEph DE441' on every row (not null).
-- The prior schema recorded provenance via ephemeris_version; this column
-- provides an explicit, human-readable citation string per Gate-3 spec.
-- [BRAHMA-BG-0-1]
BEGIN;

ALTER TABLE ephemeris_daily
  ADD COLUMN IF NOT EXISTS source_citation TEXT NOT NULL DEFAULT 'SwissEph DE441';

ALTER TABLE ephemeris_daily_staging
  ADD COLUMN IF NOT EXISTS source_citation TEXT NOT NULL DEFAULT 'SwissEph DE441';

-- Backfill any existing rows that have NULL (shouldn't exist given DEFAULT,
-- but belt-and-suspenders for any rows written before this migration).
UPDATE ephemeris_daily         SET source_citation = 'SwissEph DE441' WHERE source_citation IS NULL;
UPDATE ephemeris_daily_staging SET source_citation = 'SwissEph DE441' WHERE source_citation IS NULL;

CREATE INDEX IF NOT EXISTS idx_ephemeris_source_citation
  ON ephemeris_daily(source_citation);

COMMIT;
