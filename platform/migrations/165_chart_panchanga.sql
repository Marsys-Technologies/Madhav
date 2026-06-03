-- 165_chart_panchanga.sql
-- Brahma GA-1-7: ganita.panchanga — birth-moment panchanga per chart.
--
-- Stores the five classical panchanga limbs (tithi, vara, nakshatra, yoga, karana)
-- at the exact birth time and location for a given chart_id.
-- Ayanamsha-invariant: tithi/vara/yoga/karana are astronomical and ayanamsha-independent;
-- nakshatra is sidereal-Lahiri (canonical); tagged explicitly.
--
-- Differs from panchanga_daily (date-keyed, sunrise-anchored, observer-fixed):
-- chart_panchanga is chart-keyed and computed at the exact birth moment.
--
-- Source: BRAHMA_L1_L5_REGISTRY_SEED_v1_0 §B ganita.panchanga (GA-1-7)
-- Author: Brahma swarm Śilpī, 2026-06-03
-- Migration: 165

BEGIN;

CREATE TABLE IF NOT EXISTS chart_panchanga (
  id                        BIGSERIAL   PRIMARY KEY,
  chart_id                  UUID        NOT NULL,           -- FK to charts.id (not declared to allow standalone operation)
  build_id                  TEXT        NOT NULL,           -- build provenance tag

  -- ── Tithi ────────────────────────────────────────────────────────────
  tithi_num                 SMALLINT    NOT NULL,           -- 1..30
  tithi_name                TEXT        NOT NULL,           -- e.g. 'Shukla Tritiya'
  paksha                    TEXT        NOT NULL,           -- 'shukla' | 'krishna'
  tithi_elapsed_pct         NUMERIC(6,3),                  -- 0..100 (% elapsed within tithi at birth)

  -- ── Vara ─────────────────────────────────────────────────────────────
  vara_num                  SMALLINT    NOT NULL,           -- 1=Sun..7=Sat
  vara_name                 TEXT        NOT NULL,           -- e.g. 'Ravivara'

  -- ── Nakshatra (Moon, sidereal Lahiri) ────────────────────────────────
  moon_nakshatra            TEXT        NOT NULL,           -- e.g. 'Purva Bhadrapada'
  moon_nakshatra_index      SMALLINT    NOT NULL,           -- 0..26 (0=Ashwini)
  moon_nakshatra_pada       SMALLINT    NOT NULL,           -- 1..4
  moon_longitude_deg        NUMERIC(12,8),                 -- sidereal Lahiri at birth moment
  sun_longitude_deg         NUMERIC(12,8),                 -- sidereal Lahiri at birth moment

  -- ── Yoga ─────────────────────────────────────────────────────────────
  yoga_num                  SMALLINT    NOT NULL,           -- 1..27
  yoga_name                 TEXT        NOT NULL,           -- e.g. 'Shiva'

  -- ── Karana ───────────────────────────────────────────────────────────
  karana_num                SMALLINT    NOT NULL,           -- 1..11
  karana_name               TEXT        NOT NULL,           -- e.g. 'Garaja'

  -- ── Sunrise context ──────────────────────────────────────────────────
  sunrise_ist               TEXT,                          -- 'HH:MM:SS' IST at birth location
  sunrise_utc               TIMESTAMPTZ,                   -- exact UTC sunrise for birth date

  -- ── Provenance ───────────────────────────────────────────────────────
  ayanamsha_id              TEXT        NOT NULL DEFAULT 'lahiri',
  source_citation           TEXT        NOT NULL,           -- canonical source reference
  engine_version            TEXT        NOT NULL,           -- natal_engine version tag
  computed_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  -- Uniqueness: one row per chart per build
  UNIQUE (chart_id, build_id)
);

-- Indexes for retrieval
CREATE INDEX IF NOT EXISTS idx_chart_panchanga_chart_id
  ON chart_panchanga (chart_id);
CREATE INDEX IF NOT EXISTS idx_chart_panchanga_tithi
  ON chart_panchanga (tithi_num);
CREATE INDEX IF NOT EXISTS idx_chart_panchanga_nakshatra
  ON chart_panchanga (moon_nakshatra);
CREATE INDEX IF NOT EXISTS idx_chart_panchanga_yoga
  ON chart_panchanga (yoga_name);
CREATE INDEX IF NOT EXISTS idx_chart_panchanga_vara
  ON chart_panchanga (vara_num);

COMMIT;
