-- Migration 216: Replace COALESCE functional index with two partial indexes
--
-- Migration 215 created a COALESCE(formula_id, '') functional unique index.
-- PostgreSQL ON CONFLICT requires the index expression to exactly match the
-- ON CONFLICT clause. The 5 standard writers use:
--   ON CONFLICT (chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, build_id)
-- which requires a non-functional unique constraint/index on exactly those 6 cols.
--
-- Fix: two partial indexes:
--   1. Partial unique index on 6 cols WHERE formula_id IS NULL
--      → matches the 5 standard writers' ON CONFLICT (after they add WHERE formula_id IS NULL)
--   2. Unique index on 7 cols WHERE formula_id IS NOT NULL
--      → handles ga_sensitive_writer variant rows (GULIKA_MEAN, GULIKA_TRIMSHAMSHA, etc.)
--      (ga_sensitive uses ON CONFLICT (fact_id) so this index is for dedup only, not ON CONFLICT)

-- Drop the COALESCE functional index from migration 215
DROP INDEX IF EXISTS chart_facts_unique_dedup;

-- Partial unique index for standard rows (formula_id IS NULL)
-- Matches writers' ON CONFLICT (...6 cols...) WHERE formula_id IS NULL
CREATE UNIQUE INDEX IF NOT EXISTS chart_facts_unique_null_formula
  ON chart_facts (chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, build_id)
  WHERE formula_id IS NULL;

-- Unique index for variant rows (formula_id IS NOT NULL)
-- Prevents duplicate formula variants; ga_sensitive uses ON CONFLICT (fact_id) not this
CREATE UNIQUE INDEX IF NOT EXISTS chart_facts_unique_with_formula
  ON chart_facts (chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, build_id, formula_id)
  WHERE formula_id IS NOT NULL;
