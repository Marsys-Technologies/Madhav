-- brahma_ganita.sql
-- BRAHMA L1 Gaṇita — ganita_positions + ganita_dashas tables
--
-- Contract (BRAHMA_L1_L5_REGISTRY_SEED §B):
--   ganita.positions: one row per graha per chart per ayanamsha
--   ganita.dashas:    MD / AD / PD rows per chart (Vimshottari; canonical PyJHora-mathematical dates)
--
-- Gate notes:
--   GA-1-2 positions gate: astronomical sanity + internal structural anchors (NOT FORENSIC parity)
--   GA-1-4 dashas gate: Vimshottari correctness using canonical mathematical dates (NOT FORENSIC dates)
--
-- ROLLBACK:
--   DROP TABLE IF EXISTS ganita_dashas;
--   DROP TABLE IF EXISTS ganita_positions;
-- ─────────────────────────────────────────────────────────────────────────────

-- ── ganita_positions ──────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS ganita_positions (
  id                 UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  chart_id           UUID        NOT NULL REFERENCES charts(id) ON DELETE CASCADE,
  build_id           TEXT        NOT NULL,
  ayanamsha_id       TEXT        NOT NULL,
  planet             TEXT        NOT NULL,
  tropical_longitude DOUBLE PRECISION NOT NULL,
  sidereal_longitude DOUBLE PRECISION NOT NULL,
  sign_id            SMALLINT    NOT NULL CHECK (sign_id BETWEEN 1 AND 12),
  sign_name          TEXT        NOT NULL,
  nakshatra_id       SMALLINT    NOT NULL CHECK (nakshatra_id BETWEEN 1 AND 27),
  nakshatra_name     TEXT        NOT NULL,
  nakshatra_pada     SMALLINT    NOT NULL CHECK (nakshatra_pada BETWEEN 1 AND 4),
  speed_dps          DOUBLE PRECISION NOT NULL DEFAULT 0,
  is_retrograde      BOOLEAN     NOT NULL DEFAULT FALSE,
  source_citation    TEXT        NOT NULL,
  computed_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT ganita_positions_unique
    UNIQUE (chart_id, ayanamsha_id, planet)
);

CREATE INDEX IF NOT EXISTS idx_ganita_positions_chart
  ON ganita_positions (chart_id, ayanamsha_id);

COMMENT ON TABLE ganita_positions IS
  'BRAHMA L1 Gaṇita: sidereal graha positions computed via pyswisseph DE441. '
  'One row per planet per chart per ayanamsha. Astronomical ground truth — '
  'NOT FORENSIC value-parity. Gate: GA-1-2.';

-- ── ganita_dashas ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS ganita_dashas (
  id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  chart_id         UUID        NOT NULL REFERENCES charts(id) ON DELETE CASCADE,
  build_id         TEXT        NOT NULL,
  dasha_system     TEXT        NOT NULL DEFAULT 'vimshottari',
  level            SMALLINT    NOT NULL CHECK (level IN (1, 2, 3)),  -- 1=MD 2=AD 3=PD
  lord             TEXT        NOT NULL,
  parent_lord      TEXT,        -- NULL for MD (level=1)
  start_date       DATE        NOT NULL,
  end_date         DATE        NOT NULL,
  years            DOUBLE PRECISION NOT NULL,
  source_citation  TEXT        NOT NULL,
  computed_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT ganita_dashas_unique
    UNIQUE (chart_id, dasha_system, level, lord, start_date)
);

CREATE INDEX IF NOT EXISTS idx_ganita_dashas_chart
  ON ganita_dashas (chart_id, dasha_system, level);

CREATE INDEX IF NOT EXISTS idx_ganita_dashas_date
  ON ganita_dashas (chart_id, start_date, end_date);

COMMENT ON TABLE ganita_dashas IS
  'BRAHMA L1 Gaṇita: Vimshottari dasha tree (MD/AD/PD) computed mathematically from '
  'Moon nakshatra position. Canonical PyJHora-mathematical dates — NOT FORENSIC dates '
  '(which have a ~7-9 day discrepancy). Gate: GA-1-4.';
