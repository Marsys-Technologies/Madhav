-- Phase 4C: Panchanga daily — sunrise-anchored 5 limbs at Bhubaneswar observer.
-- Single-observer mode (lat 20.27021°N, lon 85.82966°E, alt 45m).
-- Vara boundary is sunrise, not midnight; consumers must respect this.
-- M7 multi-native extension will require either per-observer rows or
-- query-time observer params + on-the-fly compute via sidecar.
BEGIN;

CREATE TABLE IF NOT EXISTS panchanga_daily (
  id BIGSERIAL PRIMARY KEY,
  date DATE NOT NULL UNIQUE,                       -- ISO date for which sunrise is computed
  sunrise_utc TIMESTAMP NOT NULL,                  -- exact sunrise moment in UTC
  sunrise_jd DOUBLE PRECISION NOT NULL,            -- Julian Day at sunrise (UTC)
  sunrise_ist TIME NOT NULL,                       -- local time at observer (UTC + 5:30)
  -- Tithi
  tithi SMALLINT NOT NULL,                         -- 1..30 (1=Shukla Pratipada, 15=Purnima, 16=Krishna Pratipada, 30=Amavasya)
  tithi_name TEXT NOT NULL,                        -- 'Shukla Pratipada' .. 'Krishna Amavasya'
  paksha TEXT NOT NULL,                            -- 'shukla' | 'krishna'
  tithi_fraction NUMERIC(7,5) NOT NULL,            -- fractional tithi at sunrise [0, 30), useful for karana boundary
  -- Vara
  vara TEXT NOT NULL,                              -- 'Ravivara' .. 'Shanivara'
  vara_lord TEXT NOT NULL,                         -- 'Sun' .. 'Saturn'
  vara_index SMALLINT NOT NULL,                    -- 0=Sun .. 6=Saturn
  -- Moon at sunrise
  moon_nakshatra TEXT NOT NULL,                    -- 'Ashwini' .. 'Revati'
  moon_nakshatra_index SMALLINT NOT NULL,          -- 0..26
  moon_nakshatra_pada SMALLINT NOT NULL,           -- 1..4
  moon_longitude_deg NUMERIC(11,7) NOT NULL,       -- sidereal Lahiri at sunrise
  sun_longitude_deg NUMERIC(11,7) NOT NULL,        -- sidereal Lahiri at sunrise (handy for cross-checks)
  -- Yoga
  yoga TEXT NOT NULL,                              -- 'Vishkumbha' .. 'Vaidhriti'
  yoga_index SMALLINT NOT NULL,                    -- 1..27
  -- Karana
  karana TEXT NOT NULL,                            -- 'Bava'..'Vishti' (movable) | 'Kintughna'|'Shakuni'|'Catushpada'|'Naga' (fixed)
  karana_position_in_month SMALLINT NOT NULL,      -- 0..59 — useful for karana boundary debugging
  -- Provenance
  ayanamsha TEXT NOT NULL DEFAULT 'lahiri',
  observer_lat NUMERIC(8,5) NOT NULL DEFAULT 20.27021,
  observer_lon NUMERIC(8,5) NOT NULL DEFAULT 85.82966,
  observer_alt_m NUMERIC(8,2) NOT NULL DEFAULT 45,
  ephemeris_version TEXT NOT NULL,                 -- 'pyswisseph-2.10.03.2+4C-panchanga-v1'
  build_id TEXT NOT NULL REFERENCES build_manifests(build_id)
);

CREATE INDEX IF NOT EXISTS idx_panchanga_date ON panchanga_daily(date);
CREATE INDEX IF NOT EXISTS idx_panchanga_tithi ON panchanga_daily(tithi);
CREATE INDEX IF NOT EXISTS idx_panchanga_tithi_purnima ON panchanga_daily(date) WHERE tithi = 15;
CREATE INDEX IF NOT EXISTS idx_panchanga_tithi_amavasya ON panchanga_daily(date) WHERE tithi = 30;
CREATE INDEX IF NOT EXISTS idx_panchanga_tithi_ekadashi ON panchanga_daily(date) WHERE tithi IN (11, 26);
CREATE INDEX IF NOT EXISTS idx_panchanga_nakshatra ON panchanga_daily(moon_nakshatra);
CREATE INDEX IF NOT EXISTS idx_panchanga_vara ON panchanga_daily(vara_lord);

CREATE TABLE IF NOT EXISTS panchanga_daily_staging (LIKE panchanga_daily INCLUDING ALL);

COMMIT;
