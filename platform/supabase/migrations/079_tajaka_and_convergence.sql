-- Migration 079: Tajaka annual table + school_convergence_index materialized view
-- MCP Transformation v3.2-S5 — MARSYS-JIS project.
--
-- 1. school_convergence_index MV (row-based, correct for school_signal_coverage schema)
-- 2. tajaka_annual table (muntha_sign deterministic; year_lord/annual_lagna/saham NULL = EXTERNAL_COMPUTATION_REQUIRED)

-- ────────────────────────────────────────────────────────────────────────────
-- 1. school_convergence_index MATERIALIZED VIEW
-- ────────────────────────────────────────────────────────────────────────────
-- Reads from school_signal_coverage (one row per signal_id × school).
-- convergence_score = fraction of 4 schools that have primary or secondary coverage.
-- missing_schools = array of school names absent from coverage for that signal.

CREATE MATERIALIZED VIEW IF NOT EXISTS school_convergence_index AS
SELECT
  signal_id,
  count(*) FILTER (WHERE school = 'parashari' AND coverage_type IN ('primary','secondary')) AS parashari_present,
  count(*) FILTER (WHERE school = 'jaimini'   AND coverage_type IN ('primary','secondary')) AS jaimini_present,
  count(*) FILTER (WHERE school = 'kp'        AND coverage_type IN ('primary','secondary')) AS kp_present,
  count(*) FILTER (WHERE school = 'tajika'    AND coverage_type IN ('primary','secondary')) AS tajika_present,
  ROUND(
    (
      (CASE WHEN count(*) FILTER (WHERE school='parashari' AND coverage_type IN ('primary','secondary')) > 0 THEN 1 ELSE 0 END)
    + (CASE WHEN count(*) FILTER (WHERE school='jaimini'   AND coverage_type IN ('primary','secondary')) > 0 THEN 1 ELSE 0 END)
    + (CASE WHEN count(*) FILTER (WHERE school='kp'        AND coverage_type IN ('primary','secondary')) > 0 THEN 1 ELSE 0 END)
    + (CASE WHEN count(*) FILTER (WHERE school='tajika'    AND coverage_type IN ('primary','secondary')) > 0 THEN 1 ELSE 0 END)
    )::numeric / 4.0, 2
  ) AS convergence_score,
  array_remove(ARRAY[
    CASE WHEN count(*) FILTER (WHERE school='parashari' AND coverage_type IN ('primary','secondary')) = 0 THEN 'Parashari' END,
    CASE WHEN count(*) FILTER (WHERE school='jaimini'   AND coverage_type IN ('primary','secondary')) = 0 THEN 'Jaimini' END,
    CASE WHEN count(*) FILTER (WHERE school='kp'        AND coverage_type IN ('primary','secondary')) = 0 THEN 'KP' END,
    CASE WHEN count(*) FILTER (WHERE school='tajika'    AND coverage_type IN ('primary','secondary')) = 0 THEN 'Tajika' END
  ], NULL) AS missing_schools
FROM school_signal_coverage
GROUP BY signal_id;

CREATE UNIQUE INDEX ON school_convergence_index (signal_id);

COMMENT ON MATERIALIZED VIEW school_convergence_index IS
  'Per-signal cross-school convergence. convergence_score = [0.00, 1.00] fraction of 4 schools '
  '(Parashari, Jaimini, KP, Tajika) with primary or secondary coverage. '
  'Refresh with: REFRESH MATERIALIZED VIEW CONCURRENTLY school_convergence_index. '
  'Added by MCP Transformation v3.2-S5 migration 079.';

-- ────────────────────────────────────────────────────────────────────────────
-- 2. tajaka_annual TABLE
-- ────────────────────────────────────────────────────────────────────────────
-- Stores per-year Tajaka (Varshaphal) computed values for the native.
-- Native: Abhisek Mohanty, born 1984-02-05, 10:43 IST, Bhubaneswar.
-- Natal Lagna = Cancer (FORENSIC authoritative; FORENSIC_ASTROLOGICAL_DATA_v8_0.md).
--
-- muntha_sign: DETERMINISTIC — advances 1 sign per year from natal Lagna.
--   1984 (age 0→1, year 1) = Cancer (native Lagna); 1985 = Leo; 1986 = Virgo; etc.
-- year_lord: NULL = [EXTERNAL_COMPUTATION_REQUIRED] (requires Jagannatha Hora or Swiss Ephemeris)
-- annual_lagna: NULL = [EXTERNAL_COMPUTATION_REQUIRED] (requires JH solar return calculation)
-- saham_names: NULL = [EXTERNAL_COMPUTATION_REQUIRED] (requires JH Saham calculation)

CREATE TABLE IF NOT EXISTS tajaka_annual (
  native_year    integer PRIMARY KEY,    -- Calendar year of solar return (e.g. 1984, 1985, ...)
  varsha_number  integer NOT NULL,       -- Year of life (1 = first year, born 1984)
  muntha_sign    text    NOT NULL,       -- Deterministic: natal Lagna + (varsha_number - 1) signs, cyclically
  year_lord      text,                   -- NULL = requires JH calculation
  annual_lagna   text,                   -- NULL = requires JH calculation (solar-return Lagna sign)
  saham_names    text[],                 -- NULL = requires JH calculation (list of activated Sahamas)
  notes          text                    -- Freeform; used to flag EXTERNAL_COMPUTATION_REQUIRED
);

CREATE INDEX ON tajaka_annual (native_year);

COMMENT ON TABLE tajaka_annual IS
  'Per-year Tajaka (Varshaphal) data for Abhisek Mohanty (born 1984-02-05, Lagna=Cancer). '
  'muntha_sign is deterministic (Cancer→Leo→...→Gemini cycle). '
  'year_lord, annual_lagna, saham_names are NULL pending JH/Swiss-Ephemeris computation (B.10). '
  'Added by MCP Transformation v3.2-S5 migration 079.';

COMMENT ON COLUMN tajaka_annual.muntha_sign IS
  'Deterministic Muntha sign: natal Cancer Lagna + (varsha_number - 1) signs mod 12. '
  'Sequence: Cancer, Leo, Virgo, Libra, Scorpio, Sagittarius, Capricorn, Aquarius, Pisces, Aries, Taurus, Gemini, Cancer, ...';

COMMENT ON COLUMN tajaka_annual.year_lord IS
  '[EXTERNAL_COMPUTATION_REQUIRED] Planet with highest Harsha Bala in the Varsha Kundali. '
  'Requires solar return chart computation in Jagannatha Hora or Swiss Ephemeris.';

COMMENT ON COLUMN tajaka_annual.annual_lagna IS
  '[EXTERNAL_COMPUTATION_REQUIRED] Lagna sign of the solar return chart for native''s residence location. '
  'Requires solar return computation with location-at-time-of-return.';

COMMENT ON COLUMN tajaka_annual.saham_names IS
  '[EXTERNAL_COMPUTATION_REQUIRED] Sahamas (Arabic Parts) in the annual chart. '
  'Primary: Punya, Vidya, Yasha, Mitra, Mahadasha, Paradesa, Kali, Dara, Roga, Vivaha. '
  'Requires JH Saham calculation engine.';
