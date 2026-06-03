-- 002_brahmagyan_reference.sql
-- brahmagyan.reference asset — versioned classical lookup tables.
-- Each row carries source_citation. Build mode: delta (Brahma arc).
-- Run after 001_baseline.sql.

BEGIN;

-- ─────────────────────────────────────────────────────────────────────────────
-- §1  reference_nakshatra_attrs (27 rows)
-- Columns: id, nakshatra_id (1-based), name, deity, lord (Vimshottari),
--          type (ashwini_start=0deg Aries), source_citation
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.reference_nakshatra_attrs (
  id               SERIAL       PRIMARY KEY,
  nakshatra_id     INT          NOT NULL UNIQUE CHECK (nakshatra_id BETWEEN 1 AND 27),
  name             TEXT         NOT NULL,
  deity            TEXT         NOT NULL,
  lord             TEXT         NOT NULL,
  source_citation  TEXT         NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ref_nakshatra_id ON public.reference_nakshatra_attrs(nakshatra_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- §2  reference_tithi_attrs (30 rows)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.reference_tithi_attrs (
  id               SERIAL       PRIMARY KEY,
  tithi_id         INT          NOT NULL UNIQUE CHECK (tithi_id BETWEEN 1 AND 30),
  name             TEXT         NOT NULL,
  paksha           TEXT         NOT NULL CHECK (paksha IN ('shukla', 'krishna')),
  source_citation  TEXT         NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ref_tithi_id ON public.reference_tithi_attrs(tithi_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- §3  reference_yoga_attrs (27 rows)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.reference_yoga_attrs (
  id               SERIAL       PRIMARY KEY,
  yoga_id          INT          NOT NULL UNIQUE CHECK (yoga_id BETWEEN 1 AND 27),
  name             TEXT         NOT NULL,
  source_citation  TEXT         NOT NULL
);

-- ─────────────────────────────────────────────────────────────────────────────
-- §4  reference_karana_attrs (11 rows)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.reference_karana_attrs (
  id               SERIAL       PRIMARY KEY,
  karana_id        INT          NOT NULL UNIQUE CHECK (karana_id BETWEEN 1 AND 11),
  name             TEXT         NOT NULL,
  karana_type      TEXT         NOT NULL CHECK (karana_type IN ('movable', 'fixed')),
  source_citation  TEXT         NOT NULL
);

-- ─────────────────────────────────────────────────────────────────────────────
-- §5  reference_vara_attrs (7 rows)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.reference_vara_attrs (
  id               SERIAL       PRIMARY KEY,
  vara_id          INT          NOT NULL UNIQUE CHECK (vara_id BETWEEN 1 AND 7),
  name_sanskrit    TEXT         NOT NULL,
  name_english     TEXT         NOT NULL,
  lord             TEXT         NOT NULL,
  color            TEXT         NOT NULL,
  rahu_kalam_part  INT          NOT NULL,   -- which 1/8 day-part is Rahu Kalam (1-based)
  yamagandam_part  INT          NOT NULL,
  gulika_part      INT          NOT NULL,
  source_citation  TEXT         NOT NULL
);

-- ─────────────────────────────────────────────────────────────────────────────
-- §6  reference_sign_attrs (12 rows)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.reference_sign_attrs (
  id               SERIAL       PRIMARY KEY,
  sign_id          INT          NOT NULL UNIQUE CHECK (sign_id BETWEEN 1 AND 12),
  name             TEXT         NOT NULL,   -- Sanskrit (Mesha etc.)
  lord             TEXT         NOT NULL,
  source_citation  TEXT         NOT NULL
);

-- ─────────────────────────────────────────────────────────────────────────────
-- §7  reference_hora_cycle (7 rows — one per vara, giving the starting planet)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.reference_hora_cycle (
  id               SERIAL       PRIMARY KEY,
  vara_id          INT          NOT NULL UNIQUE CHECK (vara_id BETWEEN 1 AND 7),
  hora_start_planet TEXT         NOT NULL,  -- planet ruling first hora at sunrise
  chaldean_cycle   TEXT[]        NOT NULL,  -- 7-element ordered cycle starting from this vara
  source_citation  TEXT         NOT NULL
);

-- ─────────────────────────────────────────────────────────────────────────────
-- §8  reference_combustion_orbs (8 rows — 7 planets + Rahu/Ketu)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.reference_combustion_orbs (
  id               SERIAL       PRIMARY KEY,
  planet           TEXT         NOT NULL UNIQUE,
  orb_direct_deg   NUMERIC(5,2),            -- NULL for shadow planets
  orb_retro_deg    NUMERIC(5,2),            -- NULL for shadow planets
  source_citation  TEXT         NOT NULL
);

-- ─────────────────────────────────────────────────────────────────────────────
-- §9  reference_event_quality (≥18 rows: 6 events × 3 factor_types × N entries)
-- Factor types: tithi, nakshatra, vara. Score 0.0–1.0.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.reference_event_quality (
  id               SERIAL       PRIMARY KEY,
  event_type       TEXT         NOT NULL,   -- vivah|griha_pravesh|vyapara|yatra|property_purchase|mantra_initiation
  factor_type      TEXT         NOT NULL CHECK (factor_type IN ('tithi', 'nakshatra', 'vara')),
  factor_id        INT          NOT NULL,   -- tithi_id / nakshatra_id / vara_id
  quality_score    NUMERIC(4,2) NOT NULL CHECK (quality_score BETWEEN 0.0 AND 1.0),
  source_citation  TEXT         NOT NULL,
  UNIQUE (event_type, factor_type, factor_id)
);
CREATE INDEX IF NOT EXISTS idx_ref_event_quality_lookup
  ON public.reference_event_quality(event_type, factor_type, factor_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- §10  reference_inauspicious_periods (7 rows — one per vara)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.reference_inauspicious_periods (
  id               SERIAL       PRIMARY KEY,
  vara_id          INT          NOT NULL UNIQUE CHECK (vara_id BETWEEN 1 AND 7),
  rahu_kalam_part  INT          NOT NULL,
  yamagandam_part  INT          NOT NULL,
  gulika_part      INT          NOT NULL,
  source_citation  TEXT         NOT NULL
);

COMMIT;
