-- Migration 213: GA9 Sade Sati — materialized view + asset registry
-- Source: A9_SADE_SATI_SPEC_v1_0.md §9 (LOCKED 2026-05-29)
-- GA9 writes ~875 rows into chart_facts (chart_facts created in 204).
-- This migration creates:
--   1. mv_chart_sade_sati_lifetime_summary — natal-fixed wide MV per (chart, ayanamsha)
--   2. asset_throughput entry for ga_sade_sati
-- Per A9 §9: NO mv_chart_sade_sati_active_at_date (time-varying = forbidden).
-- Atomic-grain rule: all row-level fields are atomic; 5 sanctioned JSONB fields
--   (saturn_nakshatra_transitions_jsonb_atomic, quarter_intensity_rationale_jsonb,
--    cancellation_rules_invoked_jsonb, d10_karya_activation_facts_jsonb,
--    argala_during_period_jsonb) stored in chart_facts.fact_value_jsonb.
-- Per build_runner.py step: MV refreshed synchronously at GA9 build close.

BEGIN;

-- ── 1. mv_chart_sade_sati_lifetime_summary ────────────────────────────────────
-- One wide row per (chart_id, ayanamsha_id, build_id, cycle_id) joining
-- cycle-level + phase-level + cancellation Sade Sati facts for fast retrieval.
-- Per A9 §9: natal-fixed only. Refresh synchronous at build close.

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_chart_sade_sati_lifetime_summary AS
SELECT
  cf.chart_id,
  cf.ayanamsha_id,
  cf.build_id,
  cf.fact_subject                                                          AS cycle_id,
  MAX(CASE WHEN cf.fact_key = 'cycle_start_iso'       THEN cf.fact_value_text END)  AS cycle_start_iso,
  MAX(CASE WHEN cf.fact_key = 'cycle_end_iso'         THEN cf.fact_value_text END)  AS cycle_end_iso,
  MAX(CASE WHEN cf.fact_key = 'duration_days'         THEN cf.fact_value_num  END)  AS duration_days,
  MAX(CASE WHEN cf.fact_key = 'duration_years'        THEN cf.fact_value_num  END)  AS duration_years,
  MAX(CASE WHEN cf.fact_key = 'moon_sign_for_cycle'   THEN cf.fact_value_text END)  AS moon_sign_for_cycle,
  MAX(CASE WHEN cf.fact_key = 'cycle_type'            THEN cf.fact_value_text END)  AS cycle_type,
  MAX(CASE WHEN cf.fact_key = 'compound_with_next_cycle_flag'  THEN cf.fact_value_text END) AS compound_with_next,
  MAX(CASE WHEN cf.fact_key = 'compound_with_prior_cycle_flag' THEN cf.fact_value_text END) AS compound_with_prior,
  -- Cancellation summary (from sade_sati_cancellation_check rows)
  (
    SELECT cc.fact_value_text
    FROM chart_facts cc
    WHERE cc.chart_id    = cf.chart_id
      AND cc.ayanamsha_id = cf.ayanamsha_id
      AND cc.build_id    = cf.build_id
      AND cc.fact_category = 'sade_sati_cancellation_check'
      AND cc.fact_subject  = cf.fact_subject
      AND cc.fact_key      = 'cancellation_active_flag'
    LIMIT 1
  ) AS cancellation_active_flag,
  -- Janma phase start (Saturn over natal Moon)
  (
    SELECT ph.fact_value_text
    FROM chart_facts ph
    WHERE ph.chart_id    = cf.chart_id
      AND ph.ayanamsha_id = cf.ayanamsha_id
      AND ph.build_id    = cf.build_id
      AND ph.fact_category = 'sade_sati_phase'
      AND ph.fact_subject  = cf.fact_subject || '.JANMA'
      AND ph.fact_key      = 'phase_start_iso'
    LIMIT 1
  ) AS janma_phase_start_iso,
  -- Janma phase end
  (
    SELECT ph.fact_value_text
    FROM chart_facts ph
    WHERE ph.chart_id    = cf.chart_id
      AND ph.ayanamsha_id = cf.ayanamsha_id
      AND ph.build_id    = cf.build_id
      AND ph.fact_category = 'sade_sati_phase'
      AND ph.fact_subject  = cf.fact_subject || '.JANMA'
      AND ph.fact_key      = 'phase_end_iso'
    LIMIT 1
  ) AS janma_phase_end_iso,
  -- Saturn dignity at Janma
  (
    SELECT ph.fact_value_text
    FROM chart_facts ph
    WHERE ph.chart_id    = cf.chart_id
      AND ph.ayanamsha_id = cf.ayanamsha_id
      AND ph.build_id    = cf.build_id
      AND ph.fact_category = 'sade_sati_phase'
      AND ph.fact_subject  = cf.fact_subject || '.JANMA'
      AND ph.fact_key      = 'saturn_dignity'
    LIMIT 1
  ) AS janma_saturn_dignity
FROM chart_facts cf
WHERE cf.fact_category = 'sade_sati_cycle'
  AND cf.fact_key IN (
    'cycle_start_iso', 'cycle_end_iso', 'duration_days', 'duration_years',
    'moon_sign_for_cycle', 'cycle_type',
    'compound_with_next_cycle_flag', 'compound_with_prior_cycle_flag'
  )
GROUP BY cf.chart_id, cf.ayanamsha_id, cf.build_id, cf.fact_subject;

-- Unique index for CONCURRENT refresh support
CREATE UNIQUE INDEX IF NOT EXISTS mv_sade_sati_summary_idx
  ON mv_chart_sade_sati_lifetime_summary (chart_id, ayanamsha_id, build_id, cycle_id);

-- Retrieval index for chart + ayanamsha queries
CREATE INDEX IF NOT EXISTS mv_sade_sati_chart_ay_idx
  ON mv_chart_sade_sati_lifetime_summary (chart_id, ayanamsha_id);


-- ── 2. asset_throughput entry for ga_sade_sati — REMOVED ──────────────────────
-- The original INSERT here targeted asset_throughput columns (asset_label, row_count,
-- target_row_count, build_state, count_sql, last_build_id) that do not exist on the
-- redesigned asset_throughput telemetry table — it would fail on any real database.
-- Superseded by migration 214, which registers count_sql on asset_registry (the table
-- the cockpit stats route actually reads). Intentionally left as a no-op.


COMMIT;
