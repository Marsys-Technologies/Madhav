-- Migration 208: GA5 Sensitive Points Materialized View
-- =========================================================
-- Creates mv_chart_sensitive_points_summary for querying A5 sensitive points
-- across all 30 categories and 5 ayanamshas.
--
-- Prerequisites: chart_facts table from migration 204 with Section-B
-- enrichment columns (tolerance_arcsec, near_sign_boundary_flag,
-- near_nakshatra_boundary_flag, vargottama_flag_at_point,
-- formula_provenance_text, cross_ayanamsha_divergence_arcsec).
--
-- GA5 categories covered:
--   upagraha_position, saturn_derived_point, esoteric_point_bhrigu_bindu,
--   esoteric_point_yogi, esoteric_point_avayogi, esoteric_point_mrityu,
--   esoteric_point_trisphuta, esoteric_point_chatushphuta,
--   esoteric_point_panchasphuta, esoteric_point_pranapada_sphuta,
--   esoteric_point_trikona_dasha_sphuta, esoteric_point_sri_yantra_position,
--   esoteric_point_brahma, esoteric_point_vishnu, esoteric_point_shiva,
--   saham_position, karaka_chara_position, karakamsa_position,
--   swamsa_position, arudha_pada, midpoint,
--   kp_ruling_planets_natal, kp_cuspal_significators, aprakasha_position,
--   tajik_hadda_lord, tajik_triraashipathi, tajik_vargottama_specific,
--   lal_kitab_special_point, maharsi_specific_point, bhrigu_nadi_point,
--   nakshatra_pada_sensitive

-- ── Add Section-B enrichment columns if not present ──────────────────────────
-- (May already exist from GA3 migration; idempotent additions)

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='chart_facts' AND column_name='tolerance_arcsec'
    ) THEN
        ALTER TABLE chart_facts ADD COLUMN tolerance_arcsec FLOAT;
    END IF;
END
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='chart_facts' AND column_name='near_sign_boundary_flag'
    ) THEN
        ALTER TABLE chart_facts ADD COLUMN near_sign_boundary_flag BOOLEAN DEFAULT FALSE;
    END IF;
END
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='chart_facts' AND column_name='near_nakshatra_boundary_flag'
    ) THEN
        ALTER TABLE chart_facts ADD COLUMN near_nakshatra_boundary_flag BOOLEAN DEFAULT FALSE;
    END IF;
END
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='chart_facts' AND column_name='vargottama_flag_at_point'
    ) THEN
        ALTER TABLE chart_facts ADD COLUMN vargottama_flag_at_point BOOLEAN DEFAULT FALSE;
    END IF;
END
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='chart_facts' AND column_name='formula_provenance_text'
    ) THEN
        ALTER TABLE chart_facts ADD COLUMN formula_provenance_text TEXT;
    END IF;
END
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='chart_facts' AND column_name='cross_ayanamsha_divergence_arcsec'
    ) THEN
        ALTER TABLE chart_facts ADD COLUMN cross_ayanamsha_divergence_arcsec FLOAT DEFAULT 0.0;
    END IF;
END
$$;

-- ── Materialized view ─────────────────────────────────────────────────────────
-- Summarizes one row per (chart_id, ayanamsha_id, fact_category, fact_subject)
-- with the key longitude + sign + nakshatra values for the most common keys.

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_chart_sensitive_points_summary AS
SELECT
    cf.chart_id,
    cf.ayanamsha_id,
    cf.fact_category,
    cf.fact_subject,
    cf.build_id,
    -- Core longitude value
    MAX(CASE WHEN cf.fact_key = 'longitude_sidereal' THEN cf.fact_value_num END)
        AS longitude_sidereal,
    -- Sign
    MAX(CASE WHEN cf.fact_key = 'sign' THEN cf.fact_value_text END)
        AS sign,
    -- Sign lord
    MAX(CASE WHEN cf.fact_key = 'sign_lord' THEN cf.fact_value_text END)
        AS sign_lord,
    -- Nakshatra
    MAX(CASE WHEN cf.fact_key = 'nakshatra' THEN cf.fact_value_text END)
        AS nakshatra,
    -- Nakshatra lord
    MAX(CASE WHEN cf.fact_key = 'nakshatra_lord' THEN cf.fact_value_text END)
        AS nakshatra_lord,
    -- Pada
    MAX(CASE WHEN cf.fact_key = 'pada' THEN cf.fact_value_num END)
        AS pada,
    -- House (D1 whole-sign)
    MAX(CASE WHEN cf.fact_key = 'house_d1' THEN cf.fact_value_num END)
        AS house_d1,
    -- For karaka rows: assigned graha
    MAX(CASE WHEN cf.fact_key = 'assigned_graha' THEN cf.fact_value_text END)
        AS assigned_graha,
    -- For saham/karaka: formula_id (from any row in group)
    MIN(cf.formula_id)
        AS formula_id,
    -- Section-B enrichment aggregates
    BOOL_OR(cf.near_sign_boundary_flag)
        AS near_sign_boundary_flag,
    BOOL_OR(cf.near_nakshatra_boundary_flag)
        AS near_nakshatra_boundary_flag,
    BOOL_OR(cf.vargottama_flag_at_point)
        AS vargottama_flag_at_point,
    MAX(cf.formula_provenance_text)
        AS formula_provenance_text,
    MAX(cf.cross_ayanamsha_divergence_arcsec)
        AS cross_ayanamsha_divergence_arcsec,
    -- Verification pass (must all be two_pass_verified)
    MIN(cf.verification_pass_status)
        AS verification_pass_status,
    -- Row count
    COUNT(*) AS fact_key_count
FROM chart_facts cf
WHERE cf.fact_category IN (
    'upagraha_position',
    'saturn_derived_point',
    'esoteric_point_bhrigu_bindu',
    'esoteric_point_yogi',
    'esoteric_point_avayogi',
    'esoteric_point_mrityu',
    'esoteric_point_trisphuta',
    'esoteric_point_chatushphuta',
    'esoteric_point_panchasphuta',
    'esoteric_point_pranapada_sphuta',
    'esoteric_point_trikona_dasha_sphuta',
    'esoteric_point_sri_yantra_position',
    'esoteric_point_brahma',
    'esoteric_point_vishnu',
    'esoteric_point_shiva',
    'saham_position',
    'karaka_chara_position',
    'karakamsa_position',
    'swamsa_position',
    'arudha_pada',
    'midpoint',
    'kp_ruling_planets_natal',
    'kp_cuspal_significators',
    'aprakasha_position',
    'tajik_hadda_lord',
    'tajik_triraashipathi',
    'tajik_vargottama_specific',
    'lal_kitab_special_point',
    'maharsi_specific_point',
    'bhrigu_nadi_point',
    'nakshatra_pada_sensitive'
)
GROUP BY cf.chart_id, cf.ayanamsha_id, cf.fact_category, cf.fact_subject, cf.build_id
WITH DATA;

-- ── Indexes ───────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_mv_sensitive_points_chart_ay
    ON mv_chart_sensitive_points_summary (chart_id, ayanamsha_id);

CREATE INDEX IF NOT EXISTS idx_mv_sensitive_points_category
    ON mv_chart_sensitive_points_summary (fact_category);

CREATE INDEX IF NOT EXISTS idx_mv_sensitive_points_chart_cat
    ON mv_chart_sensitive_points_summary (chart_id, fact_category);

CREATE INDEX IF NOT EXISTS idx_mv_sensitive_points_two_pass
    ON mv_chart_sensitive_points_summary (verification_pass_status);

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_sensitive_points_unique
    ON mv_chart_sensitive_points_summary (chart_id, ayanamsha_id, fact_category, fact_subject, build_id);

-- ── Cross-ayanamsha divergence summary view ───────────────────────────────────
-- Shows max divergence per sensitive point across all 5 ayanamshas
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_sensitive_points_cross_ayanamsha AS
SELECT
    chart_id,
    fact_category,
    fact_subject,
    COUNT(DISTINCT ayanamsha_id) AS ayanamsha_count,
    MAX(longitude_sidereal) - MIN(longitude_sidereal) AS longitude_range_deg,
    (MAX(longitude_sidereal) - MIN(longitude_sidereal)) * 3600.0 AS divergence_arcsec,
    array_agg(DISTINCT ayanamsha_id ORDER BY ayanamsha_id) AS ayanamsha_ids
FROM mv_chart_sensitive_points_summary
WHERE longitude_sidereal IS NOT NULL
GROUP BY chart_id, fact_category, fact_subject
HAVING COUNT(DISTINCT ayanamsha_id) > 1
WITH DATA;

CREATE INDEX IF NOT EXISTS idx_mv_spca_divergence
    ON mv_sensitive_points_cross_ayanamsha (chart_id, divergence_arcsec DESC);
