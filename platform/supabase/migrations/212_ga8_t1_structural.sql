-- Migration 212: GA8 T1 Structural writer — three new materialized views
-- Creates MVs for structural/convergence categories produced by ga_structural_writer.py.
-- Rule (locked): MVs are ONLY for time-invariant natal data.
-- Refresh: synchronous at build close.
-- Per: A8_T1_STRUCTURAL_SPEC_v1_0.md §6.
-- All MVs: IF NOT EXISTS (idempotent).
-- DOES NOT redeclare migrations 207 MVs (those remain in 207_ga3_materialized_views.sql).

BEGIN;

-- ── 1. mv_chart_yogas_fired_summary ──────────────────────────────────────────
-- One row per (chart_id, ayanamsha_id, build_id, yoga_name) joining yoga firing flag +
-- cancellation state + strength score.
-- Source: chart_facts WHERE fact_category = 'yoga_fires'.

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_chart_yogas_fired_summary AS
SELECT
  chart_id,
  ayanamsha_id,
  build_id,
  fact_subject                                                         AS yoga_name,
  MAX(CASE WHEN fact_key = 'yoga_name'          THEN fact_value_text END) AS yoga_name_text,
  MAX(CASE WHEN fact_key = 'yoga_strength_score' THEN fact_value_num  END) AS yoga_strength_score,
  MAX(
    CASE WHEN fact_key = 'yoga_name'
    THEN (fact_value_jsonb->>'cancellation_flag')::boolean END
  )                                                                    AS cancellation_flag,
  MAX(
    CASE WHEN fact_key = 'yoga_name'
    THEN fact_value_jsonb->>'yoga_group' END
  )                                                                    AS yoga_group,
  MAX(
    CASE WHEN fact_key = 'yoga_name'
    THEN fact_value_jsonb->>'classical_citation_id' END
  )                                                                    AS classical_citation_id,
  MAX(
    CASE WHEN fact_key = 'yoga_name'
    THEN fact_value_jsonb->>'cancelled_by_yoga_name' END
  )                                                                    AS cancelled_by,
  MAX(
    CASE WHEN fact_key = 'yoga_name'
    THEN fact_value_jsonb->>'constituent_facts_array' END
  )                                                                    AS constituent_facts_array_raw
FROM chart_facts
WHERE fact_category = 'yoga_fires'
GROUP BY chart_id, ayanamsha_id, build_id, fact_subject;

CREATE UNIQUE INDEX IF NOT EXISTS mv_chart_yogas_fired_summary_idx
  ON mv_chart_yogas_fired_summary (chart_id, ayanamsha_id, build_id, yoga_name);

CREATE INDEX IF NOT EXISTS mv_chart_yogas_fired_summary_chart_ay_idx
  ON mv_chart_yogas_fired_summary (chart_id, ayanamsha_id, build_id);

CREATE INDEX IF NOT EXISTS mv_chart_yogas_fired_summary_group_idx
  ON mv_chart_yogas_fired_summary (chart_id, ayanamsha_id, yoga_group);


-- ── 2. mv_chart_aspect_matrix ─────────────────────────────────────────────────
-- One row per (chart_id, ayanamsha_id, build_id, graha_or_house, target_house_or_source)
-- showing aspect_parashari_given + aspect_parashari_received + conjunction pairs.
-- Source: chart_facts WHERE fact_category IN ('aspect_parashari_given', 'aspect_parashari_received').

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_chart_aspect_matrix AS
SELECT
  chart_id,
  ayanamsha_id,
  build_id,
  fact_subject                                 AS source,
  fact_key                                     AS target_key,
  fact_category                                AS aspect_type,
  fact_value_num                               AS aspect_strength,
  verification_pass_status,
  citation_human
FROM chart_facts
WHERE fact_category IN (
  'aspect_parashari_given',
  'aspect_parashari_received',
  'conjunction_within_orb',
  'aspect_jaimini',
  'aspect_tajik'
);

CREATE INDEX IF NOT EXISTS mv_chart_aspect_matrix_source_idx
  ON mv_chart_aspect_matrix (chart_id, ayanamsha_id, build_id, source);

CREATE INDEX IF NOT EXISTS mv_chart_aspect_matrix_type_idx
  ON mv_chart_aspect_matrix (chart_id, ayanamsha_id, aspect_type);

CREATE INDEX IF NOT EXISTS mv_chart_aspect_matrix_chart_ay_idx
  ON mv_chart_aspect_matrix (chart_id, ayanamsha_id, build_id);


-- ── 3. mv_chart_t1_composite_strengths ───────────────────────────────────────
-- Aggregates composite per-graha structural strength indicators into one row per
-- (chart_id, ayanamsha_id, build_id, graha):
--   • graha_in_house_composite_strength (bphs_weighted for the natal house)
--   • graha_vargottama_amplification_factor
--   • effective_dignity_score
--   • baladi_avastha
--   • functional_class (bphs_canonical)
--   • pranic_strength
--   • tri_deva_role_strength
-- Source: chart_facts across multiple GA8 categories.

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_chart_t1_composite_strengths AS
SELECT
  cf.chart_id,
  cf.ayanamsha_id,
  cf.build_id,
  cf.fact_subject                                                            AS graha,
  MAX(CASE WHEN cf.fact_category = 'graha_vargottama_amplification_factor'
            AND cf.fact_key = 'amplification_factor'
           THEN cf.fact_value_num END)                                       AS vargottama_factor,
  MAX(CASE WHEN cf.fact_category = 'graha_effective_dignity_modified_by_aspects'
            AND cf.fact_key = 'effective_dignity_score'
           THEN cf.fact_value_num END)                                       AS effective_dignity_score,
  MAX(CASE WHEN cf.fact_category = 'graha_avastha_baladi'
            AND cf.fact_key = 'baladi_state'
           THEN cf.fact_value_text END)                                      AS baladi_avastha,
  MAX(CASE WHEN cf.fact_category = 'graha_avastha_deepta'
            AND cf.fact_key = 'deepta_state'
           THEN cf.fact_value_text END)                                      AS deepta_avastha,
  MAX(CASE WHEN cf.fact_category = 'graha_functional_class_per_ascendant'
            AND cf.fact_key = 'bphs_canonical'
           THEN cf.fact_value_text END)                                      AS functional_class_bphs,
  MAX(CASE WHEN cf.fact_category = 'graha_yoga_karaka_flag'
            AND cf.fact_key = 'is_yoga_karaka'
           THEN cf.fact_value_text END)                                      AS is_yoga_karaka,
  MAX(CASE WHEN cf.fact_category = 'pranic_strength_per_graha'
            AND cf.fact_key = 'prana_score'
           THEN cf.fact_value_num END)                                       AS prana_score,
  MAX(CASE WHEN cf.fact_category = 'graha_tri_deva_role_strength'
            AND cf.fact_key = 'role_strength'
           THEN cf.fact_value_num END)                                       AS tri_deva_role_strength,
  MAX(CASE WHEN cf.fact_category = 'jaimini_tri_deva_role_per_graha'
            AND cf.fact_key = 'tri_deva_role'
           THEN cf.fact_value_text END)                                      AS tri_deva_role,
  MAX(CASE WHEN cf.fact_category = 'graha_composite_state_classification'
            AND cf.fact_key = 'classification'
           THEN cf.fact_value_text END)                                      AS composite_state,
  MAX(CASE WHEN cf.fact_category = 'graha_special_state_rollup'
            AND cf.fact_key = 'is_vargottama'
           THEN cf.fact_value_text END)                                      AS is_vargottama,
  MAX(CASE WHEN cf.fact_category = 'graha_special_state_rollup'
            AND cf.fact_key = 'is_combust'
           THEN cf.fact_value_text END)                                      AS is_combust,
  MAX(CASE WHEN cf.fact_category = 'graha_special_state_rollup'
            AND cf.fact_key = 'is_retrograde'
           THEN cf.fact_value_text END)                                      AS is_retrograde
FROM chart_facts cf
WHERE cf.fact_category IN (
  'graha_vargottama_amplification_factor',
  'graha_effective_dignity_modified_by_aspects',
  'graha_avastha_baladi',
  'graha_avastha_deepta',
  'graha_functional_class_per_ascendant',
  'graha_yoga_karaka_flag',
  'pranic_strength_per_graha',
  'graha_tri_deva_role_strength',
  'jaimini_tri_deva_role_per_graha',
  'graha_composite_state_classification',
  'graha_special_state_rollup'
)
  AND cf.fact_subject IN (
    'SUN','MOON','MAR','MER','JUP','VEN','SAT','RAH_MEAN','KET_MEAN'
  )
GROUP BY cf.chart_id, cf.ayanamsha_id, cf.build_id, cf.fact_subject;

CREATE UNIQUE INDEX IF NOT EXISTS mv_chart_t1_composite_strengths_idx
  ON mv_chart_t1_composite_strengths (chart_id, ayanamsha_id, build_id, graha);

CREATE INDEX IF NOT EXISTS mv_chart_t1_composite_strengths_chart_ay_idx
  ON mv_chart_t1_composite_strengths (chart_id, ayanamsha_id, build_id);


COMMIT;

-- DOWN:
-- DROP MATERIALIZED VIEW IF EXISTS mv_chart_t1_composite_strengths;
-- DROP MATERIALIZED VIEW IF EXISTS mv_chart_aspect_matrix;
-- DROP MATERIALIZED VIEW IF EXISTS mv_chart_yogas_fired_summary;
