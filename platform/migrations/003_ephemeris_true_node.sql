-- brahmagyan.ephemeris — true_node + mean_node dual storage.
-- Adds node_type column so both Rahu/Ketu variants can coexist in the table.
-- Default 'mean' preserves existing row semantics.
-- UNIQUE constraint updated from (date, planet) to (date, planet, node_type).
BEGIN;

ALTER TABLE ephemeris_daily
  ADD COLUMN IF NOT EXISTS node_type TEXT NOT NULL DEFAULT 'mean'
    CHECK (node_type IN ('mean', 'true'));

ALTER TABLE ephemeris_daily_staging
  ADD COLUMN IF NOT EXISTS node_type TEXT NOT NULL DEFAULT 'mean'
    CHECK (node_type IN ('mean', 'true'));

-- Drop old unique constraint; replace with three-column version.
ALTER TABLE ephemeris_daily  DROP CONSTRAINT IF EXISTS ephemeris_daily_date_planet_key;
ALTER TABLE ephemeris_daily  ADD CONSTRAINT ephemeris_daily_date_planet_node_key
  UNIQUE (date, planet, node_type);

ALTER TABLE ephemeris_daily_staging  DROP CONSTRAINT IF EXISTS ephemeris_daily_staging_date_planet_key;
ALTER TABLE ephemeris_daily_staging  ADD CONSTRAINT ephemeris_daily_staging_date_planet_node_key
  UNIQUE (date, planet, node_type);

CREATE INDEX IF NOT EXISTS idx_ephemeris_node_type
  ON ephemeris_daily(planet, node_type, date);

COMMIT;
