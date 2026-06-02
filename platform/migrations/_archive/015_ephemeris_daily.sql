-- Phase 14C Stream A: ephemeris_daily and ephemeris_daily_staging
-- Swiss Ephemeris computed; one row per (date, planet); sidereal Lahiri ayanamsha.
-- ~657K rows for 9 planets × 1900-01-01 through 2100-12-31.
BEGIN;

CREATE TABLE IF NOT EXISTS ephemeris_daily (
  id BIGSERIAL PRIMARY KEY,
  date DATE NOT NULL,
  planet TEXT NOT NULL,                -- 'sun'|'moon'|'mars'|'mercury'|'jupiter'|'venus'|'saturn'|'rahu'|'ketu'
  longitude_deg NUMERIC(11,7) NOT NULL,  -- 0.0000000 - 359.9999999, sidereal Lahiri
  latitude_deg NUMERIC(11,7),
  speed_deg_per_day NUMERIC(11,7) NOT NULL,
  is_retrograde BOOLEAN NOT NULL,
  sign TEXT NOT NULL,                  -- 'Aries'|'Taurus'|...
  sign_degree NUMERIC(11,7) NOT NULL,  -- 0-30
  nakshatra TEXT NOT NULL,             -- 'Ashwini'|...
  nakshatra_pada SMALLINT NOT NULL,    -- 1-4
  ayanamsha TEXT NOT NULL DEFAULT 'lahiri',
  ephemeris_version TEXT NOT NULL,     -- 'pyswisseph-2.10.3.2' or similar
  build_id TEXT NOT NULL REFERENCES build_manifests(build_id),
  UNIQUE(date, planet)
);

CREATE INDEX IF NOT EXISTS idx_ephemeris_date ON ephemeris_daily(date);
CREATE INDEX IF NOT EXISTS idx_ephemeris_planet_date ON ephemeris_daily(planet, date);
CREATE INDEX IF NOT EXISTS idx_ephemeris_retro ON ephemeris_daily(planet, date) WHERE is_retrograde = TRUE;

CREATE TABLE IF NOT EXISTS ephemeris_daily_staging (LIKE ephemeris_daily INCLUDING ALL);

COMMIT;
