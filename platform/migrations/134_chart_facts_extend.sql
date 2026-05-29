-- Migration 134: chart_facts extension — citation + verification + subject + unit columns
-- MARSYS-JIS A3 Schema Specification [A3-S1]
-- Idempotent: yes (ADD COLUMN IF NOT EXISTS / DO-block guards throughout)

BEGIN;

-- ────────────────────────────────────────────────────────────────────────────
-- Step 1: New columns (A3 spec §1)
-- engine_version already exists (added by earlier migration); IF NOT EXISTS skips it safely.
-- ────────────────────────────────────────────────────────────────────────────
ALTER TABLE chart_facts ADD COLUMN IF NOT EXISTS fact_subject             TEXT NOT NULL DEFAULT 'CHART';
ALTER TABLE chart_facts ADD COLUMN IF NOT EXISTS unit                     TEXT          DEFAULT '';
ALTER TABLE chart_facts ADD COLUMN IF NOT EXISTS citation_ref             TEXT NOT NULL DEFAULT '';
ALTER TABLE chart_facts ADD COLUMN IF NOT EXISTS citation_human           TEXT NOT NULL DEFAULT '';
ALTER TABLE chart_facts ADD COLUMN IF NOT EXISTS source_calculation       TEXT NOT NULL DEFAULT '';
ALTER TABLE chart_facts ADD COLUMN IF NOT EXISTS verification_pass_status TEXT NOT NULL DEFAULT 'single';
ALTER TABLE chart_facts ADD COLUMN IF NOT EXISTS engine_version           TEXT NOT NULL DEFAULT '';
ALTER TABLE chart_facts ADD COLUMN IF NOT EXISTS salience_formula_ver     TEXT;

-- Additional columns required by the A3 UNIQUE constraint and §9 indexes
-- (fact_category / fact_key separate from legacy category / fact_id columns)
ALTER TABLE chart_facts ADD COLUMN IF NOT EXISTS fact_category   TEXT  NOT NULL DEFAULT '';
ALTER TABLE chart_facts ADD COLUMN IF NOT EXISTS fact_key        TEXT  NOT NULL DEFAULT '';
ALTER TABLE chart_facts ADD COLUMN IF NOT EXISTS fact_value_jsonb JSONB;

-- ────────────────────────────────────────────────────────────────────────────
-- Step 2: CHECK constraint on verification_pass_status
-- ────────────────────────────────────────────────────────────────────────────
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.check_constraints
    WHERE constraint_name = 'chart_facts_verification_pass_status_check'
  ) THEN
    ALTER TABLE chart_facts
      ADD CONSTRAINT chart_facts_verification_pass_status_check
      CHECK (verification_pass_status IN (
        'single', 'two_pass_verified', 'classical_match', 'divergent_flagged'
      ));
  END IF;
END $$;

-- ────────────────────────────────────────────────────────────────────────────
-- Step 3: UNIQUE constraint — drop old signatures, add new A3 signature
-- Old constraints used (fact_id, chart_id, ayanamsha_id) which no longer
-- matches the A3 key space. All existing rows have chart_id IS NULL so the
-- new constraint (NULLs treated as distinct) introduces no violations.
-- ────────────────────────────────────────────────────────────────────────────
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.table_constraints
    WHERE constraint_name = 'uq_chart_facts_engine'
      AND table_name = 'chart_facts'
  ) THEN
    ALTER TABLE chart_facts DROP CONSTRAINT uq_chart_facts_engine;
  END IF;
END $$;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.table_constraints
    WHERE constraint_name = 'uq_chart_facts_legacy'
      AND table_name = 'chart_facts'
  ) THEN
    ALTER TABLE chart_facts DROP CONSTRAINT uq_chart_facts_legacy;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.table_constraints
    WHERE constraint_name = 'uq_chart_facts_a3'
      AND table_name = 'chart_facts'
  ) THEN
    ALTER TABLE chart_facts
      ADD CONSTRAINT uq_chart_facts_a3
      UNIQUE (chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, build_id);
  END IF;
END $$;

-- ────────────────────────────────────────────────────────────────────────────
-- Step 4: Indexes (A3 spec §9) — all idempotent via IF NOT EXISTS
-- ────────────────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS chart_facts_chart_aya_cat_idx
    ON chart_facts (chart_id, ayanamsha_id, fact_category);

CREATE INDEX IF NOT EXISTS chart_facts_chart_aya_sub_idx
    ON chart_facts (chart_id, ayanamsha_id, fact_subject);

CREATE INDEX IF NOT EXISTS chart_facts_chart_cat_sub_key_idx
    ON chart_facts (chart_id, fact_category, fact_subject, fact_key);

CREATE INDEX IF NOT EXISTS chart_facts_build_idx
    ON chart_facts (build_id);

CREATE INDEX IF NOT EXISTS chart_facts_verification_idx
    ON chart_facts (verification_pass_status)
    WHERE verification_pass_status != 'single';

CREATE INDEX IF NOT EXISTS chart_facts_jsonb_gin
    ON chart_facts USING gin (fact_value_jsonb)
    WHERE fact_value_jsonb IS NOT NULL;

COMMIT;
