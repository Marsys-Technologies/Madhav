-- Migration 208: GA4 panchanga birth-instant materialized view
-- Brief: CLAUDECODE_BRIEF_GA4_PANCHANGA_WRITER_v1_0.md
-- Spec:  A4_PANCHANGA_SPEC_v1_0.md §7
--
-- Creates mv_chart_panchanga_birth_summary — a fast-lookup MV that joins
-- chart_facts panchanga categories across all ayanamshas for a given chart_id.
--
-- Category coverage:
--   INVARIANT: panchanga_tithi, panchanga_vara, panchanga_yoga, panchanga_karana,
--              panchanga_nakshatra_moon (INVARIANT), panchanga_solar_context,
--              panchanga_calendrical, panchanga_sun_moon_dynamics, panchanga_disha_shul,
--              panchanga_tithi_shoonya_rashi, panchanga_nakshatra_shoonya_rashi,
--              panchanga_agni_vasa, panchanga_hora_birth, panchanga_choghadiya_birth,
--              bhadra_flag
--   DEPENDENT (×5 ayanamshas): panchanga_nakshatra_moon, panchanga_special_yoga_combinations,
--              panchanga_panchaka_classification, panchaka_flag, eclipse_proximity_natal,
--              tara_bala_natal_baseline (27 rows/ay), chandra_bala_natal_baseline (12 rows/ay)

-- ── Main wide-row panchanga summary (INVARIANT rows only — ayanamsha-independent) ──

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_chart_panchanga_birth_summary AS
WITH panchanga_facts AS (
    SELECT
        cf.chart_id,
        cf.ayanamsha_id,
        cf.build_id,
        cf.fact_category,
        cf.fact_subject,
        cf.fact_key,
        cf.fact_value_text,
        cf.fact_value_num,
        cf.fact_value_jsonb,
        cf.source_calculation,
        cf.computed_at
    FROM chart_facts cf
    WHERE cf.fact_category IN (
        -- INVARIANT categories
        'panchanga_tithi',
        'panchanga_vara',
        'panchanga_yoga',
        'panchanga_karana',
        'panchanga_solar_context',
        'panchanga_calendrical',
        'panchanga_sun_moon_dynamics',
        'panchanga_disha_shul',
        'panchanga_tithi_shoonya_rashi',
        'panchanga_nakshatra_shoonya_rashi',
        'panchanga_agni_vasa',
        'panchanga_hora_birth',
        'panchanga_choghadiya_birth',
        'bhadra_flag',
        -- DEPENDENT categories
        'panchanga_nakshatra_moon',
        'panchanga_special_yoga_combinations',
        'panchanga_panchaka_classification',
        'panchaka_flag',
        'eclipse_proximity_natal',
        'tara_bala_natal_baseline',
        'chandra_bala_natal_baseline'
    )
)
SELECT
    pf.chart_id,
    pf.ayanamsha_id,
    pf.build_id,
    pf.fact_category,
    pf.fact_subject,
    pf.fact_key,
    pf.fact_value_text,
    pf.fact_value_num,
    pf.fact_value_jsonb,
    pf.source_calculation,
    pf.computed_at
FROM panchanga_facts pf;

-- ── Indexes ──────────────────────────────────────────────────────────────────

CREATE UNIQUE INDEX IF NOT EXISTS mv_chart_panchanga_birth_summary_pk
    ON mv_chart_panchanga_birth_summary (chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, build_id);

CREATE INDEX IF NOT EXISTS mv_chart_panchanga_birth_summary_chart_ay
    ON mv_chart_panchanga_birth_summary (chart_id, ayanamsha_id);

CREATE INDEX IF NOT EXISTS mv_chart_panchanga_birth_summary_category
    ON mv_chart_panchanga_birth_summary (chart_id, fact_category, fact_subject);

-- ── Tara Bala specific index (frequent 27-row lookups) ────────────────────

CREATE INDEX IF NOT EXISTS mv_chart_panchanga_tara_bala_idx
    ON mv_chart_panchanga_birth_summary (chart_id, ayanamsha_id, fact_subject)
    WHERE fact_category = 'tara_bala_natal_baseline';

-- ── Chandra Bala specific index (frequent 12-row lookups) ─────────────────

CREATE INDEX IF NOT EXISTS mv_chart_panchanga_chandra_bala_idx
    ON mv_chart_panchanga_birth_summary (chart_id, ayanamsha_id, fact_subject)
    WHERE fact_category = 'chandra_bala_natal_baseline';

-- ── Comments ──────────────────────────────────────────────────────────────────

COMMENT ON MATERIALIZED VIEW mv_chart_panchanga_birth_summary IS
    'GA4 panchanga birth-instant summary. Covers INVARIANT (ayanamsha=INVARIANT) '
    'and DEPENDENT (×5 ayanamshas) panchanga categories from chart_facts. '
    'Tara bala: 27 rows/ay. Chandra bala: 12 rows/ay. '
    'Refresh via: REFRESH MATERIALIZED VIEW CONCURRENTLY mv_chart_panchanga_birth_summary. '
    'Brief: CLAUDECODE_BRIEF_GA4_PANCHANGA_WRITER_v1_0.md. '
    'Spec: A4_PANCHANGA_SPEC_v1_0.md §7.';
