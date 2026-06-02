-- Phase 14C Stream A: eclipses, eclipses_staging, retrogrades, retrogrades_staging
-- Eclipses: ~400-700 rows for 1900-2100.
-- Retrogrades: ~4K-8K station rows (retrograde_start/retrograde_end) for 1900-2100.
BEGIN;

CREATE TABLE IF NOT EXISTS eclipses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  date DATE NOT NULL,
  type TEXT NOT NULL,                  -- 'solar_total'|'solar_partial'|'solar_annular'|'lunar_total'|'lunar_penumbral'|'lunar_partial'
  longitude_deg NUMERIC(11,7),
  sign TEXT,
  nakshatra TEXT,
  visibility_region TEXT,
  build_id TEXT NOT NULL REFERENCES build_manifests(build_id),
  source_uri TEXT NOT NULL,
  UNIQUE(date, type)
);

CREATE INDEX IF NOT EXISTS idx_eclipses_date ON eclipses(date);

CREATE TABLE IF NOT EXISTS eclipses_staging (LIKE eclipses INCLUDING ALL);

CREATE TABLE IF NOT EXISTS retrogrades (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  planet TEXT NOT NULL,
  station_type TEXT NOT NULL CHECK (station_type IN ('retrograde_start', 'retrograde_end')),
  date DATE NOT NULL,
  longitude_deg NUMERIC(11,7),
  sign TEXT,
  nakshatra TEXT,
  build_id TEXT NOT NULL REFERENCES build_manifests(build_id),
  source_uri TEXT NOT NULL,
  UNIQUE(planet, station_type, date)
);

CREATE INDEX IF NOT EXISTS idx_retrogrades_date ON retrogrades(date);
CREATE INDEX IF NOT EXISTS idx_retrogrades_planet_date ON retrogrades(planet, date);

CREATE TABLE IF NOT EXISTS retrogrades_staging (LIKE retrogrades INCLUDING ALL);

COMMIT;
