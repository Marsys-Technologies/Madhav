-- Migration 071: sade_sati_cycles
--
-- Stores Sade Sati periods for each native — the 7.5-year window when Saturn
-- transits the natal Moon sign and the two adjacent signs (preceding + following).
-- Three phases per cycle: rising (preceding sign), peak (natal Moon sign), setting (following sign).
--
-- For Abhisek Mohanty (natal Moon in Aquarius, Kumbha):
--   Rising  : Saturn in Capricorn  (Makara)
--   Peak    : Saturn in Aquarius   (Kumbha)
--   Setting : Saturn in Pisces     (Meena)
--
-- Populated by platform/scripts/data/populate_sade_sati.py from ephemeris_daily.
-- Covers 1984-01-01 to 2100-12-31 for the native (≥ 8 complete cycles).

CREATE TABLE IF NOT EXISTS sade_sati_cycles (
  id                  uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  native_id           text        NOT NULL,
  start_date          date        NOT NULL,
  end_date            date        NOT NULL,
  phase               text        NOT NULL CHECK (phase IN ('rising', 'peak', 'setting')),
  moon_sign           text        NOT NULL,
  saturn_sign         text        NOT NULL,
  severity_weight     numeric     NOT NULL CHECK (severity_weight > 0 AND severity_weight <= 1.0),
  computation_source  text        NOT NULL DEFAULT 'ephemeris_daily',
  created_at          timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT sade_sati_cycles_dates_check CHECK (end_date > start_date)
);

COMMENT ON TABLE sade_sati_cycles IS
  'Sade Sati (7.5-year Saturn transit over natal Moon sign ± adjacent sign) periods per native. Seeded by populate_sade_sati.py from ephemeris_daily Saturn longitude data.';

COMMENT ON COLUMN sade_sati_cycles.native_id IS
  'Canonical native identifier — matches chart_facts.native_id (e.g. abhisek_mohanty).';

COMMENT ON COLUMN sade_sati_cycles.phase IS
  'rising = Saturn in preceding sign; peak = Saturn in natal Moon sign; setting = Saturn in following sign.';

COMMENT ON COLUMN sade_sati_cycles.severity_weight IS
  'Conventional Jyotish severity: peak = 1.0, rising = 0.7, setting = 0.7.';

COMMENT ON COLUMN sade_sati_cycles.moon_sign IS
  'The native natal Moon sign (constant for all rows per native). Verified against FORENSIC §1 at population time.';

COMMENT ON COLUMN sade_sati_cycles.saturn_sign IS
  'The sign Saturn occupies during this phase. Derived from ephemeris_daily.sign column for Saturn.';

CREATE INDEX IF NOT EXISTS idx_sade_sati_cycles_native_id
  ON sade_sati_cycles (native_id);

CREATE INDEX IF NOT EXISTS idx_sade_sati_cycles_native_dates
  ON sade_sati_cycles (native_id, start_date, end_date);
