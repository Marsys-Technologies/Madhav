-- 002_ganita_divisionals.sql
-- Brahma GA-1-3: chart_divisionals table
-- Stores all varga (divisional chart) positions for every graha, per chart and ayanamsha.
-- Supports D1–D60. Each row is one graha in one varga under one ayanamsha.
--
-- Idempotent: yes (CREATE TABLE IF NOT EXISTS + CREATE INDEX IF NOT EXISTS).
-- Depends on: 001_baseline.sql (charts table must exist).
-- Asset: ganita.divisionals (GA-1-3)
-- Tool:  query_divisional(chart_id, varga, ayanamsha)
-- BRAHMA-GA-1-3

BEGIN;

-- ─────────────────────────────────────────────────────────────────────────────
-- chart_divisionals
-- Primary store for all varga chart positions.
-- graha         : canonical planet name (Sun, Moon, Mars, Mercury, Jupiter,
--                 Venus, Saturn, Rahu, Ketu, Lagna)
-- ayanamsha_id  : which ayanamsha system ('lahiri', 'kp', 'raman', 'true_pushya', 'tropical')
-- varga         : divisional chart ID — one of D1, D2, D3, D4, D7, D9, D10,
--                 D12, D16, D20, D24, D27, D30, D40, D45, D60
-- sign          : zodiac sign name (Aries … Pisces)
-- sign_number   : 1-based sign index (1=Aries, 12=Pisces)
-- degree_in_sign: degrees within sign (0.0 – 30.0)
-- house         : house number from divisional lagna (1–12, computed after Lagna is known)
-- vargottama    : true when D1 sign == D9 sign (stored for D9 only, NULL otherwise)
-- source_citation: traceable reference for this computation
-- build_id      : build run identifier for incremental rebuilds
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.chart_divisionals (
  id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
  chart_id        UUID        NOT NULL,                  -- references charts.id
  graha           TEXT        NOT NULL,                  -- planet name
  ayanamsha_id    TEXT        NOT NULL,                  -- lahiri | kp | raman | true_pushya | tropical
  varga           TEXT        NOT NULL,                  -- D1 | D2 | D3 | ... | D60
  sign            TEXT        NOT NULL,                  -- Aries .. Pisces
  sign_number     SMALLINT    NOT NULL CHECK (sign_number BETWEEN 1 AND 12),
  degree_in_sign  NUMERIC(8,4) NOT NULL CHECK (degree_in_sign >= 0 AND degree_in_sign < 30),
  house           SMALLINT    CHECK (house BETWEEN 1 AND 12),
  vargottama      BOOLEAN,                               -- NULL unless varga=D9
  source_citation TEXT        NOT NULL DEFAULT 'PyJHora DE441 / MARSYS-engine v1',
  build_id        TEXT        NOT NULL,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Unique constraint: one row per (chart, graha, ayanamsha, varga)
CREATE UNIQUE INDEX IF NOT EXISTS chart_divisionals_unique_idx
  ON public.chart_divisionals (chart_id, graha, ayanamsha_id, varga);

-- Query indexes
CREATE INDEX IF NOT EXISTS chart_divisionals_chart_ayan_idx
  ON public.chart_divisionals (chart_id, ayanamsha_id);

CREATE INDEX IF NOT EXISTS chart_divisionals_chart_varga_idx
  ON public.chart_divisionals (chart_id, ayanamsha_id, varga);

CREATE INDEX IF NOT EXISTS chart_divisionals_build_idx
  ON public.chart_divisionals (build_id);

-- Row-level security placeholder (inherit from charts table policy)
ALTER TABLE public.chart_divisionals ENABLE ROW LEVEL SECURITY;

-- Allow service role to read/write all rows (chart_id scoping done in application)
CREATE POLICY IF NOT EXISTS "service role full access"
  ON public.chart_divisionals
  AS PERMISSIVE FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

COMMIT;
