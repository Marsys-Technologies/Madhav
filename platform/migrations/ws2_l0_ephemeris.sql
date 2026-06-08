-- ws2_l0_ephemeris.sql
-- BRAHMA WS-2 L0 Brahmagyan: ephemeris_daily table
--
-- Contract (L0_CONTRACT_REGISTRY_SEED §C 0.6):
--   brahmagyan.ephemeris: daily tropical positions for 10 bodies
--   Source: pyswisseph DE441
--   ayanamsha_id stored as 'tropical' (ayanamsha subtracted at read time)
--
-- Volume floor: >= 29,200 rows × 10 bodies for period 1980-2060
-- SUPERSEDED: floor updated to 825,084 (91,676 days × 9 grahas, 1900-2150) via migration 182 / PR #228.
--
-- Gate: COUNT(*) >= floor; native birth date 1984-02-05 has Sun in Capricorn
--
-- ROLLBACK:
--   DROP TABLE IF EXISTS ephemeris_daily CASCADE;
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS ephemeris_daily (
  id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  date              DATE        NOT NULL,
  body              TEXT        NOT NULL,           -- 'Sun','Moon','Mars', etc.
  ayanamsha_id      TEXT        NOT NULL DEFAULT 'tropical',
  tropical_longitude NUMERIC(9,6) NOT NULL,         -- degrees 0-360
  latitude          NUMERIC(8,6)  NOT NULL DEFAULT 0.0,
  speed_dps         NUMERIC(10,7) NOT NULL DEFAULT 0.0,  -- degrees per day
  is_retrograde     BOOLEAN     NOT NULL DEFAULT FALSE,
  sign_number       SMALLINT    GENERATED ALWAYS AS
                      (FLOOR(tropical_longitude / 30)::SMALLINT + 1) STORED,
  degree_in_sign    NUMERIC(6,3) GENERATED ALWAYS AS
                      (MOD(tropical_longitude, 30)) STORED,
  nakshatra_number  SMALLINT    GENERATED ALWAYS AS
                      (FLOOR(tropical_longitude / (360.0/27))::SMALLINT + 1) STORED,
  source_citation   TEXT        NOT NULL DEFAULT 'pyswisseph DE441 + Swiss Ephemeris',
  computed_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (date, body, ayanamsha_id)
);

COMMENT ON TABLE ephemeris_daily IS
  'BRAHMA L0 Brahmagyan: daily tropical planetary positions via pyswisseph DE441. '
  'ayanamsha_id = tropical (subtract ayanamsha at read time for sidereal). '
  'One row per (date, body, ayanamsha_id). BRAHMA-BG-0-6.';

CREATE INDEX IF NOT EXISTS idx_ephemeris_date ON ephemeris_daily (date);
CREATE INDEX IF NOT EXISTS idx_ephemeris_body ON ephemeris_daily (body);
CREATE INDEX IF NOT EXISTS idx_ephemeris_date_body ON ephemeris_daily (date, body);
CREATE INDEX IF NOT EXISTS idx_ephemeris_ayanamsha ON ephemeris_daily (ayanamsha_id);
