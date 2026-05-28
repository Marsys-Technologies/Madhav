-- 086_l25_chart_id_ayanamsha_keyed.sql
-- Unit 2a — deterministic L1→L2.5 build into chart_id + ayanamsha-keyed stores
-- (sets G4_no_native_lit).
--
-- Adds chart_id + ayanamsha_id keying to chart_facts and the l25_* family, and
-- decomposes the MSR coefficient into three structural columns:
--   deterministic_strength, verification_certainty, computed_salience.
-- (Gemini keeper — no fused score.)
--
-- Strangler discipline: legacy rows (pre-engine, model-attributed) are NOT
-- deleted. They are retained in place with provenance.attribution =
-- 'model_attributed' and chart_id/ayanamsha_id NULL until 089 freezes them.
--
-- ROLLBACK: see end of file.

BEGIN;

-- ─── 1. charts dimension table ────────────────────────────────────────────────
-- Lightweight registry so chart_id is a foreign key and `assert_no_native_literal`
-- has somewhere to point.
-- Greenfield shape (patched 2026-05-28 for v1.2 follow-on: chart_id TEXT → UUID
-- to align with the legacy prod schema where charts.id is UUID; chart_id
-- becomes a UUID secondary key per 086_0_charts_align.sql). When prod is
-- aligned (charts table already exists), this CREATE TABLE IF NOT EXISTS is a
-- no-op; the column type here only matters for greenfield environments (dev /
-- ephemeral CI).
CREATE TABLE IF NOT EXISTS charts (
  chart_id        UUID PRIMARY KEY,
  subject_label   TEXT NOT NULL,
  datetime_iso    TEXT NOT NULL,
  tz_offset_hours NUMERIC NOT NULL,
  latitude_deg    NUMERIC NOT NULL,
  longitude_deg   NUMERIC NOT NULL,
  place_name      TEXT NOT NULL,
  -- 'native' for the canonical subject; 'tertiary' for ad-hoc; 'fixture' for tests.
  role            TEXT NOT NULL DEFAULT 'tertiary'
                  CHECK (role IN ('native', 'tertiary', 'fixture')),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_charts_role ON charts(role);

-- ─── 2. chart_facts: add (chart_id, ayanamsha_id) keying ─────────────────────
-- chart_id NULL on legacy rows; new engine rows are NOT NULL.
ALTER TABLE chart_facts
  ADD COLUMN IF NOT EXISTS chart_id      UUID REFERENCES charts(chart_id),
  ADD COLUMN IF NOT EXISTS ayanamsha_id  TEXT,
  ADD COLUMN IF NOT EXISTS engine_version TEXT,
  ADD COLUMN IF NOT EXISTS computed_at_iso TEXT;

-- Drop the global UNIQUE(fact_id) — fact_id is now unique per (chart_id, ayanamsha_id).
-- The old unique index name is `chart_facts_fact_id_key` (auto-named by the
-- UNIQUE constraint). Drop conditionally.
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'chart_facts_fact_id_key'
  ) THEN
    ALTER TABLE chart_facts DROP CONSTRAINT chart_facts_fact_id_key;
  END IF;
END$$;

-- New composite uniqueness — but only for engine rows (chart_id NOT NULL).
CREATE UNIQUE INDEX IF NOT EXISTS uq_chart_facts_engine
  ON chart_facts(fact_id, chart_id, ayanamsha_id)
  WHERE chart_id IS NOT NULL;

-- Legacy rows (chart_id NULL) keep fact_id-only uniqueness.
CREATE UNIQUE INDEX IF NOT EXISTS uq_chart_facts_legacy
  ON chart_facts(fact_id)
  WHERE chart_id IS NULL;

CREATE INDEX IF NOT EXISTS idx_chart_facts_chart_ayan
  ON chart_facts(chart_id, ayanamsha_id);

-- Mirror to staging.
ALTER TABLE chart_facts_staging
  ADD COLUMN IF NOT EXISTS chart_id      UUID,
  ADD COLUMN IF NOT EXISTS ayanamsha_id  TEXT,
  ADD COLUMN IF NOT EXISTS engine_version TEXT,
  ADD COLUMN IF NOT EXISTS computed_at_iso TEXT;

-- ─── 3. l25_msr_signals: add chart_id + ayanamsha_id + 3-column coefficient ──
ALTER TABLE l25_msr_signals
  ADD COLUMN IF NOT EXISTS chart_id                 UUID REFERENCES charts(chart_id),
  ADD COLUMN IF NOT EXISTS ayanamsha_id             TEXT,
  ADD COLUMN IF NOT EXISTS engine_version           TEXT,
  -- Three SEPARATE columns; NO fused score column. (Gemini keeper.)
  ADD COLUMN IF NOT EXISTS deterministic_strength   NUMERIC,
  ADD COLUMN IF NOT EXISTS verification_certainty   NUMERIC,
  ADD COLUMN IF NOT EXISTS computed_salience        NUMERIC;

-- Validity bounds on the three coefficient columns (allowed to be NULL on
-- legacy / archived rows; non-null rows must sit in [0,1]).
ALTER TABLE l25_msr_signals
  DROP CONSTRAINT IF EXISTS l25_msr_signals_deterministic_strength_range;
ALTER TABLE l25_msr_signals
  ADD CONSTRAINT l25_msr_signals_deterministic_strength_range
  CHECK (deterministic_strength IS NULL
         OR (deterministic_strength >= 0 AND deterministic_strength <= 1));

ALTER TABLE l25_msr_signals
  DROP CONSTRAINT IF EXISTS l25_msr_signals_verification_certainty_range;
ALTER TABLE l25_msr_signals
  ADD CONSTRAINT l25_msr_signals_verification_certainty_range
  CHECK (verification_certainty IS NULL
         OR (verification_certainty >= 0 AND verification_certainty <= 1));

ALTER TABLE l25_msr_signals
  DROP CONSTRAINT IF EXISTS l25_msr_signals_computed_salience_range;
ALTER TABLE l25_msr_signals
  ADD CONSTRAINT l25_msr_signals_computed_salience_range
  CHECK (computed_salience IS NULL
         OR (computed_salience >= 0 AND computed_salience <= 1));

-- signal_id UNIQUE -> (signal_id, chart_id, ayanamsha_id) UNIQUE for engine rows.
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'l25_msr_signals_signal_id_key'
  ) THEN
    ALTER TABLE l25_msr_signals DROP CONSTRAINT l25_msr_signals_signal_id_key;
  END IF;
END$$;

CREATE UNIQUE INDEX IF NOT EXISTS uq_l25_msr_engine
  ON l25_msr_signals(signal_id, chart_id, ayanamsha_id)
  WHERE chart_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_l25_msr_legacy
  ON l25_msr_signals(signal_id)
  WHERE chart_id IS NULL;

CREATE INDEX IF NOT EXISTS idx_l25_msr_chart_ayan
  ON l25_msr_signals(chart_id, ayanamsha_id);

-- Mirror to staging.
ALTER TABLE l25_msr_signals_staging
  ADD COLUMN IF NOT EXISTS chart_id                 UUID,
  ADD COLUMN IF NOT EXISTS ayanamsha_id             TEXT,
  ADD COLUMN IF NOT EXISTS engine_version           TEXT,
  ADD COLUMN IF NOT EXISTS deterministic_strength   NUMERIC,
  ADD COLUMN IF NOT EXISTS verification_certainty   NUMERIC,
  ADD COLUMN IF NOT EXISTS computed_salience        NUMERIC;

-- ─── 4. data_source_expected (never-drop floor) ───────────────────────────────
-- For acceptance criterion #2: per-category row counts ≥ data_source_expected.
CREATE TABLE IF NOT EXISTS data_source_expected (
  category          TEXT NOT NULL,
  divisional_chart  TEXT NOT NULL DEFAULT 'D1',
  min_row_count     INTEGER NOT NULL,
  notes             TEXT,
  PRIMARY KEY (category, divisional_chart)
);

-- Seed the never-drop floor for the categories the engine emits. These are
-- structural floors (lambda <= expected); the engine is free to emit more.
INSERT INTO data_source_expected (category, divisional_chart, min_row_count, notes) VALUES
  ('planet',          'D1', 9,  '9 grahas — Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu'),
  ('house',           'D1', 12, '12 whole-sign houses'),
  ('panchanga',       'D1', 5,  'tithi, vara, nakshatra, yoga, karana'),
  ('ascendant',       'D1', 1,  'lagna'),
  ('sensitive_point', 'D1', 3,  'gulika, mandi at minimum; bhava madhya optional'),
  ('dasha_balance',   'D1', 1,  'vimshottari balance at birth')
ON CONFLICT (category, divisional_chart) DO NOTHING;

COMMIT;

-- ROLLBACK
-- BEGIN;
-- DROP TABLE IF EXISTS data_source_expected;
-- ALTER TABLE l25_msr_signals
--   DROP COLUMN IF EXISTS chart_id,
--   DROP COLUMN IF EXISTS ayanamsha_id,
--   DROP COLUMN IF EXISTS engine_version,
--   DROP COLUMN IF EXISTS deterministic_strength,
--   DROP COLUMN IF EXISTS verification_certainty,
--   DROP COLUMN IF EXISTS computed_salience;
-- ALTER TABLE chart_facts
--   DROP COLUMN IF EXISTS chart_id,
--   DROP COLUMN IF EXISTS ayanamsha_id,
--   DROP COLUMN IF EXISTS engine_version,
--   DROP COLUMN IF EXISTS computed_at_iso;
-- DROP TABLE IF EXISTS charts;
-- COMMIT;
