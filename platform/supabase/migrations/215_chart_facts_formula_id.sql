-- Migration 215: Add formula_id column to chart_facts + restructure UNIQUE constraint
--
-- ga_sensitive_writer._insert_rows includes formula_id in its INSERT column list.
-- chart_facts was built without this column (migration 204), causing a column-not-found
-- error that aborts the entire transaction and blocks the L1 Gaṇita build.
--
-- Adds formula_id TEXT (nullable) and replaces the flat UNIQUE constraint with a
-- functional one using COALESCE(formula_id, '') so NULL and non-null variants
-- are handled correctly (NULL variants still deduplicated; non-null variants
-- with different formula_ids allowed alongside each other).

ALTER TABLE chart_facts ADD COLUMN IF NOT EXISTS formula_id TEXT;

-- Drop the old flat UNIQUE constraint (build without formula_id)
ALTER TABLE chart_facts
  DROP CONSTRAINT IF EXISTS "chart_facts_chart_id_ayanamsha_id_fact_category_fact_subjec_key";

-- Recreate with COALESCE to handle NULL formula_id:
--   COALESCE(formula_id, '') groups NULL variants together so they still dedup,
--   while non-null formula_ids are treated as distinct variant families.
CREATE UNIQUE INDEX IF NOT EXISTS chart_facts_unique_dedup
  ON chart_facts (chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, build_id, COALESCE(formula_id, ''));
