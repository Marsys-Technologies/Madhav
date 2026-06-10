-- Migration 209: GA6 chart_divisionals extension + MVs for vargas writer
-- Source: A6_VARGAS_SPEC_v1_0.md §4 §8 + GA6 brief §9 §12
-- Extends chart_divisionals with atomic per-category columns for:
--   - Section-B enrichment (6 universal enrichment columns per brief)
--   - fact_category + fact_key columns for atomic-grain storage
--   - 30-varga × 25-category rows targeting this table
-- Adds: mv_chart_vargas_summary + mv_chart_super_vargottama_bodies
-- All DDL idempotent (ALTER TABLE ADD COLUMN IF NOT EXISTS + CREATE IF NOT EXISTS).

BEGIN;

-- ── 1. Extend chart_divisionals for atomic GA6 per-row storage ──────────────
-- GA6 stores one row per (chart_id, ayanamsha_id, varga, graha, fact_category, fact_key, build_id)
-- We add atomic columns to support the GA6 emission model.
-- The existing unique index is on (chart_id, graha, ayanamsha_id, varga) — too broad for atomic rows.
-- We add a new primary storage pattern via a new composite index on the extended PK.

-- Add atomic fact columns (all nullable for backward compat)
ALTER TABLE chart_divisionals
  ADD COLUMN IF NOT EXISTS fact_category        TEXT,
  ADD COLUMN IF NOT EXISTS fact_key             TEXT,
  ADD COLUMN IF NOT EXISTS fact_value_text      TEXT,
  ADD COLUMN IF NOT EXISTS fact_value_num       NUMERIC,
  ADD COLUMN IF NOT EXISTS fact_subject         TEXT,
  ADD COLUMN IF NOT EXISTS build_id_uuid        UUID,
  ADD COLUMN IF NOT EXISTS verification_pass_status TEXT
    CHECK (verification_pass_status IN ('two_pass_verified','classical_match','divergent_flagged','single')),
  ADD COLUMN IF NOT EXISTS engine_version       TEXT,
  ADD COLUMN IF NOT EXISTS citation_ref         TEXT,
  ADD COLUMN IF NOT EXISTS citation_human       TEXT,
  ADD COLUMN IF NOT EXISTS source_calculation   TEXT,
  ADD COLUMN IF NOT EXISTS computed_at          TIMESTAMPTZ;

-- Relax legacy wide-row NOT NULLs: the GA6 atomic model writes one row per
-- (fact_category, fact_key); non-position fact rows do not populate the legacy
-- position columns. chart_id/ayanamsha_id/varga/build_id remain required.
ALTER TABLE chart_divisionals ALTER COLUMN graha          DROP NOT NULL;
ALTER TABLE chart_divisionals ALTER COLUMN sign           DROP NOT NULL;
ALTER TABLE chart_divisionals ALTER COLUMN sign_number    DROP NOT NULL;
ALTER TABLE chart_divisionals ALTER COLUMN degree_in_sign DROP NOT NULL;

-- Section-B enrichment columns (A5 §3 universal enrichments, per GA6 brief §intro)
ALTER TABLE chart_divisionals
  ADD COLUMN IF NOT EXISTS tolerance_arcsec                   NUMERIC,
  ADD COLUMN IF NOT EXISTS near_sign_boundary_flag            BOOLEAN,
  ADD COLUMN IF NOT EXISTS near_nakshatra_boundary_flag       BOOLEAN,
  ADD COLUMN IF NOT EXISTS vargottama_flag_at_point           BOOLEAN,
  ADD COLUMN IF NOT EXISTS formula_provenance_text            TEXT,
  ADD COLUMN IF NOT EXISTS cross_ayanamsha_divergence_arcsec  NUMERIC;

-- ── 2. New indexes for GA6 atomic-grain query patterns ───────────────────────

-- Composite index: chart × ayanamsha × varga × fact_category
CREATE INDEX IF NOT EXISTS cd_ga6_cat_idx
  ON chart_divisionals (chart_id, ayanamsha_id, varga, fact_category);

-- Composite index: chart × ayanamsha × fact_category × fact_subject
CREATE INDEX IF NOT EXISTS cd_ga6_subject_idx
  ON chart_divisionals (chart_id, ayanamsha_id, fact_category, fact_subject);

-- Composite index: chart × varga × fact_category × fact_key
CREATE INDEX IF NOT EXISTS cd_ga6_key_idx
  ON chart_divisionals (chart_id, varga, fact_category, fact_key);

-- build_id_uuid index for incremental writes
CREATE INDEX IF NOT EXISTS cd_ga6_build_uuid_idx
  ON chart_divisionals (build_id_uuid);

-- verification status index
CREATE INDEX IF NOT EXISTS cd_ga6_verification_idx
  ON chart_divisionals (verification_pass_status)
  WHERE verification_pass_status IS NOT NULL;

-- ── 3. Materialized view: mv_chart_vargas_summary ───────────────────────────
-- Wide row per (chart_id, ayanamsha_id, graha, varga) joining position + dignity.
-- Refreshed at build close per A6 §8.

DROP MATERIALIZED VIEW IF EXISTS mv_chart_vargas_summary;

CREATE MATERIALIZED VIEW mv_chart_vargas_summary AS
SELECT
  cd.chart_id,
  cd.ayanamsha_id,
  cd.graha                          AS body,
  cd.varga,
  MAX(CASE WHEN cd.fact_key = 'sign'            THEN cd.fact_value_text END) AS sign,
  MAX(CASE WHEN cd.fact_key = 'sign_id'         THEN cd.fact_value_num  END) AS sign_id,
  MAX(CASE WHEN cd.fact_key = 'house'           THEN cd.fact_value_num  END) AS house,
  MAX(CASE WHEN cd.fact_key = 'degree_in_sign'  THEN cd.fact_value_num  END) AS degree_in_sign,
  MAX(CASE WHEN cd.fact_key = 'dignity'         THEN cd.fact_value_text END) AS dignity,
  MAX(CASE WHEN cd.fact_key = 'vargottama'      THEN cd.fact_value_text END) AS vargottama,
  MAX(CASE WHEN cd.fact_key = 'deity'           THEN cd.fact_value_text END) AS deity,
  MAX(CASE WHEN cd.fact_key = 'formula_id'      THEN cd.fact_value_text END) AS formula_id,
  MAX(cd.build_id_uuid::text)::uuid                                                       AS build_id_uuid,
  MAX(cd.computed_at)                                                         AS computed_at
FROM chart_divisionals cd
WHERE cd.fact_category IN ('varga_position', 'varga_dignity', 'varga_vargottama_flag', 'varga_deity_attribution')
GROUP BY cd.chart_id, cd.ayanamsha_id, cd.graha, cd.varga;

CREATE UNIQUE INDEX IF NOT EXISTS mv_chart_vargas_summary_idx
  ON mv_chart_vargas_summary (chart_id, ayanamsha_id, body, varga);

-- ── 4. Materialized view: mv_chart_super_vargottama_bodies ──────────────────
-- Bodies that are super-vargottama (same sign in >= 3 vargas).
-- Small but high-signal for tools querying strong bodies quickly.

DROP MATERIALIZED VIEW IF EXISTS mv_chart_super_vargottama_bodies;

CREATE MATERIALIZED VIEW mv_chart_super_vargottama_bodies AS
SELECT
  cd.chart_id,
  cd.ayanamsha_id,
  cd.graha                                    AS body,
  cd.fact_value_text                          AS super_vargottama,
  MAX(cd.build_id_uuid::text)::uuid                       AS build_id_uuid,
  MAX(cd.computed_at)                         AS computed_at
FROM chart_divisionals cd
WHERE cd.fact_category = 'varga_super_vargottama_flag'
  AND cd.fact_key = 'super_vargottama'
  AND cd.fact_value_text = 'True'
GROUP BY cd.chart_id, cd.ayanamsha_id, cd.graha, cd.fact_value_text;

CREATE UNIQUE INDEX IF NOT EXISTS mv_chart_super_vargottama_idx
  ON mv_chart_super_vargottama_bodies (chart_id, ayanamsha_id, body);

COMMIT;

-- DOWN (manual rollback):
-- DROP MATERIALIZED VIEW IF EXISTS mv_chart_super_vargottama_bodies;
-- DROP MATERIALIZED VIEW IF EXISTS mv_chart_vargas_summary;
-- DROP INDEX IF EXISTS cd_ga6_verification_idx;
-- DROP INDEX IF EXISTS cd_ga6_build_uuid_idx;
-- DROP INDEX IF EXISTS cd_ga6_key_idx;
-- DROP INDEX IF EXISTS cd_ga6_subject_idx;
-- DROP INDEX IF EXISTS cd_ga6_cat_idx;
-- ALTER TABLE chart_divisionals DROP COLUMN IF EXISTS cross_ayanamsha_divergence_arcsec;
-- ... (remove all added columns)
