-- 088_l25_rm_ucn_keyed.sql
-- Unit 2a — RM remedy lookup + UCN computed-signature digest, keyed by
-- (chart_id, ayanamsha_id).
--
-- RM is the deterministic remedy lookup: for a structural condition (e.g.,
-- a debilitated planet, an afflicted house, a malefic-ruled nakshatra), the
-- remedy entries the lookup returns are pure functions of the chart state.
-- The actual remedy *prescription* (text + classical attribution) is owned
-- by the corpus (legacy l25_rm_resonances rows + RM_v2_*.md). 2a writes the
-- *deterministic linkage* rows: which condition → which canonical RM
-- resonance(s).
--
-- UCN is the unified-chart-narrative computed-signature digest: for a given
-- (chart, ayanamsha), what are the structural signatures the chart exhibits?
-- Each row is a structural fact + a stable digest (sha256 of the structural
-- payload) so identical chart-states across runs hash identically.
--
-- ROLLBACK: see end of file.

BEGIN;

-- ─── 1. l25_rm_resonances: chart_id + ayanamsha_id (lookup keys) ─────────────
ALTER TABLE l25_rm_resonances
  ADD COLUMN IF NOT EXISTS chart_id        UUID REFERENCES charts(chart_id),
  ADD COLUMN IF NOT EXISTS ayanamsha_id    TEXT,
  ADD COLUMN IF NOT EXISTS engine_version  TEXT,
  -- Structural condition that triggered this lookup hit. Examples:
  --   'debilitated:Sun:Libra:7'  (planet:sign:house)
  --   'afflicted_house:7:malefic'
  --   'nakshatra_lord_dignity:Saturn:debilitated'
  ADD COLUMN IF NOT EXISTS structural_condition TEXT;

CREATE INDEX IF NOT EXISTS idx_l25_rm_chart_ayan
  ON l25_rm_resonances(chart_id, ayanamsha_id);

CREATE INDEX IF NOT EXISTS idx_l25_rm_structural_condition
  ON l25_rm_resonances(structural_condition)
  WHERE structural_condition IS NOT NULL;

ALTER TABLE l25_rm_resonances_staging
  ADD COLUMN IF NOT EXISTS chart_id        UUID,
  ADD COLUMN IF NOT EXISTS ayanamsha_id    TEXT,
  ADD COLUMN IF NOT EXISTS engine_version  TEXT,
  ADD COLUMN IF NOT EXISTS structural_condition TEXT;

-- ─── 2. l25_ucn_sections: chart_id + ayanamsha_id + computed-signature ──────
ALTER TABLE l25_ucn_sections
  ADD COLUMN IF NOT EXISTS chart_id        UUID REFERENCES charts(chart_id),
  ADD COLUMN IF NOT EXISTS ayanamsha_id    TEXT,
  ADD COLUMN IF NOT EXISTS engine_version  TEXT,
  -- sha256(canonicalized structural payload). Same chart-state ⇒ same digest.
  ADD COLUMN IF NOT EXISTS computed_signature TEXT,
  -- The structural payload itself (deterministic JSONB), kept compact.
  ADD COLUMN IF NOT EXISTS signature_payload JSONB;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'l25_ucn_sections_section_id_key'
  ) THEN
    ALTER TABLE l25_ucn_sections
      DROP CONSTRAINT l25_ucn_sections_section_id_key;
  END IF;
END$$;

CREATE UNIQUE INDEX IF NOT EXISTS uq_l25_ucn_engine
  ON l25_ucn_sections(section_id, chart_id, ayanamsha_id)
  WHERE chart_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_l25_ucn_legacy
  ON l25_ucn_sections(section_id)
  WHERE chart_id IS NULL;

CREATE INDEX IF NOT EXISTS idx_l25_ucn_chart_ayan
  ON l25_ucn_sections(chart_id, ayanamsha_id);

CREATE INDEX IF NOT EXISTS idx_l25_ucn_computed_signature
  ON l25_ucn_sections(computed_signature)
  WHERE computed_signature IS NOT NULL;

ALTER TABLE l25_ucn_sections_staging
  ADD COLUMN IF NOT EXISTS chart_id        UUID,
  ADD COLUMN IF NOT EXISTS ayanamsha_id    TEXT,
  ADD COLUMN IF NOT EXISTS engine_version  TEXT,
  ADD COLUMN IF NOT EXISTS computed_signature TEXT,
  ADD COLUMN IF NOT EXISTS signature_payload  JSONB;

-- Extend the never-drop floor for L2.5 structural assets — the engine, for
-- the canonical native chart at jh_true_chitra, MUST emit at least these
-- per-category row counts. (Lower bound; engine free to emit more.)
--
-- SHAPE GUARD (added 2026-05-28, v1.2 patch): see 086_l25_chart_id_ayanamsha_keyed.sql
-- §4 for the rationale. Live prod has the Wave-3+ tool-coverage shape; the
-- Wave-2 (category, divisional_chart, min_row_count, notes) floor is only
-- writable when the Wave-2 columns are present.
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
     WHERE table_name = 'data_source_expected'
       AND column_name = 'divisional_chart'
  ) THEN
    INSERT INTO data_source_expected (category, divisional_chart, min_row_count, notes) VALUES
      ('l25_msr_signal',  'D1', 9,  'one structural MSR row per graha minimum'),
      ('l25_cdlm_link',   'D1', 8,  'minimum 8 shared-factor links across the 9 domains'),
      ('l25_cgm_node',    'D1', 21, '9 grahas + 12 houses minimum'),
      ('l25_cgm_edge',    'D1', 9,  'minimum 9 lordship edges (one per graha)'),
      ('l25_ucn_section', 'D1', 1,  'at least one signature digest per chart')
    ON CONFLICT (category, divisional_chart) DO NOTHING;
  ELSE
    RAISE NOTICE 'data_source_expected is modern Wave-3+ shape; skipping Wave-2 L2.5 floor seed.';
  END IF;
END $$;

COMMIT;

-- ROLLBACK
-- BEGIN;
-- DELETE FROM data_source_expected WHERE category LIKE 'l25_%';
-- ALTER TABLE l25_ucn_sections
--   DROP COLUMN IF EXISTS chart_id, DROP COLUMN IF EXISTS ayanamsha_id,
--   DROP COLUMN IF EXISTS engine_version, DROP COLUMN IF EXISTS computed_signature,
--   DROP COLUMN IF EXISTS signature_payload;
-- ALTER TABLE l25_rm_resonances
--   DROP COLUMN IF EXISTS chart_id, DROP COLUMN IF EXISTS ayanamsha_id,
--   DROP COLUMN IF EXISTS engine_version, DROP COLUMN IF EXISTS structural_condition;
-- COMMIT;
