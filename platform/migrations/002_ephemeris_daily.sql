-- brahmagyan.ephemeris — Layer 0 foundation table.
-- Consolidates archived migrations 015 + 059 + 061 into a single clean-slate schema.
-- Swiss Ephemeris (pyswisseph) daily positions; Lahiri sidereal ayanamsha.
-- ~73,050 rows for 9 planets × 1900-01-01 through 2100-12-31.
-- Ayanamsha-at-source note: current build stores Lahiri-derived longitude directly.
-- Tropical-at-source + read-time derivation is a deferred future-arc item.
BEGIN;

-- build_manifests: Brahma-era asset provenance registry.
-- Schema: (build_id PK, asset_id, status, row_count, created_at).
-- Note: the pre-teardown build_manifests (archived migration 013) was a RAG-pipeline
-- specific table with a different schema. This is the Brahma clean-slate version,
-- designed for general asset provenance tracking across all Layer-0+ assets.
CREATE TABLE IF NOT EXISTS build_manifests (
  build_id    TEXT        PRIMARY KEY,
  asset_id    TEXT        NOT NULL,
  status      TEXT        NOT NULL CHECK (status IN ('in_progress', 'complete', 'rolled_back', 'failed')),
  row_count   BIGINT,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_build_manifests_asset_id ON build_manifests(asset_id);
CREATE INDEX IF NOT EXISTS idx_build_manifests_status ON build_manifests(status);

CREATE TABLE IF NOT EXISTS ephemeris_daily (
  id                BIGSERIAL PRIMARY KEY,
  date              DATE NOT NULL,
  planet            TEXT NOT NULL,
  longitude_deg     NUMERIC(11,7) NOT NULL,
  latitude_deg      NUMERIC(11,7),
  speed_deg_per_day NUMERIC(11,7) NOT NULL,
  is_retrograde     BOOLEAN NOT NULL,
  sign              TEXT NOT NULL,
  sign_degree       NUMERIC(11,7) NOT NULL,
  nakshatra         TEXT NOT NULL,
  nakshatra_pada    SMALLINT NOT NULL,
  ayanamsha         TEXT NOT NULL DEFAULT 'lahiri',
  ephemeris_version TEXT NOT NULL,
  build_id          TEXT NOT NULL REFERENCES build_manifests(build_id),
  -- Derived Vedic columns (populated by bootstrap; nullable until enriched)
  is_combust        BOOLEAN,
  combust_orb_deg   NUMERIC(7,4),
  dignity_d1        TEXT,
  vargottama_today  BOOLEAN,
  sign_ingress_today BOOLEAN,
  graha_yuddha_with TEXT,
  whole_sign_house  SMALLINT,
  bhava_chalit_house SMALLINT,
  UNIQUE(date, planet)
);

CREATE INDEX IF NOT EXISTS idx_ephemeris_date
  ON ephemeris_daily(date);
CREATE INDEX IF NOT EXISTS idx_ephemeris_planet_date
  ON ephemeris_daily(planet, date);
CREATE INDEX IF NOT EXISTS idx_ephemeris_retro
  ON ephemeris_daily(planet, date) WHERE is_retrograde = TRUE;
CREATE INDEX IF NOT EXISTS idx_ephemeris_combust
  ON ephemeris_daily(planet, date) WHERE is_combust = TRUE;
CREATE INDEX IF NOT EXISTS idx_ephemeris_dignity
  ON ephemeris_daily(planet, dignity_d1) WHERE dignity_d1 IN ('exalted','debilitated');
CREATE INDEX IF NOT EXISTS idx_ephemeris_ingress
  ON ephemeris_daily(planet, date) WHERE sign_ingress_today = TRUE;
CREATE INDEX IF NOT EXISTS idx_ephemeris_house
  ON ephemeris_daily(planet, whole_sign_house, date);
CREATE INDEX IF NOT EXISTS idx_ephemeris_bhava_chalit
  ON ephemeris_daily(planet, bhava_chalit_house, date);

CREATE TABLE IF NOT EXISTS ephemeris_daily_staging (LIKE ephemeris_daily INCLUDING ALL);

COMMIT;
