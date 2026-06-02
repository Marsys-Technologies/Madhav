-- Migration 138: 12 materialized views for A3/A4/A5 natal-fixed query layer
-- MARSYS-JIS A3 Schema Specification [A3-S6]
-- Idempotent: yes (CREATE MATERIALIZED VIEW IF NOT EXISTS throughout)
-- MVs start empty; populated after A3/A4/A5 writers run.
-- chart_facts columns: value_number (numeric), value_text (text), fact_value_jsonb (jsonb)

BEGIN;

-- ─────────────────────────────────────────────────────────────────────────────
-- MV 1: mv_chart_planet_summary
-- Per (chart, ayanamsha, graha): position + sign + nakshatra + dignity
-- Source: graha_position
-- ─────────────────────────────────────────────────────────────────────────────
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_chart_planet_summary AS
  SELECT
    chart_id,
    ayanamsha_id,
    fact_subject                                                         AS graha,
    MAX(CASE WHEN fact_key = 'lon'           THEN value_number END)     AS longitude_sidereal,
    MAX(CASE WHEN fact_key = 'sign'          THEN value_text   END)     AS sign,
    MAX(CASE WHEN fact_key = 'sign_num'      THEN value_number END)     AS sign_num,
    MAX(CASE WHEN fact_key = 'deg_in_sign'   THEN value_number END)     AS deg_in_sign,
    MAX(CASE WHEN fact_key = 'nakshatra'     THEN value_text   END)     AS nakshatra,
    MAX(CASE WHEN fact_key = 'nakshatra_pada' THEN value_number END)    AS nakshatra_pada,
    MAX(CASE WHEN fact_key = 'house_num'     THEN value_number END)     AS house_num,
    MAX(CASE WHEN fact_key = 'dignity'       THEN value_text   END)     AS dignity,
    build_id
  FROM chart_facts
  WHERE fact_category = 'graha_position'
  GROUP BY chart_id, ayanamsha_id, fact_subject, build_id
WITH DATA;

CREATE UNIQUE INDEX IF NOT EXISTS mv_chart_planet_summary_idx
  ON mv_chart_planet_summary (chart_id, ayanamsha_id, graha, build_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- MV 2: mv_chart_house_summary
-- Per (chart, ayanamsha, house): cusp + lord + occupants
-- Sources: house_cusp_per_system, house_lord_placement, house_occupant
-- ─────────────────────────────────────────────────────────────────────────────
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_chart_house_summary AS
  SELECT
    chart_id,
    ayanamsha_id,
    fact_subject                                                                                    AS house_num,
    MAX(CASE WHEN fact_category = 'house_cusp_per_system' AND fact_key = 'cusp_lon'          THEN value_number END) AS cusp_lon,
    MAX(CASE WHEN fact_category = 'house_cusp_per_system' AND fact_key = 'cusp_sign'         THEN value_text   END) AS cusp_sign,
    MAX(CASE WHEN fact_category = 'house_cusp_per_system' AND fact_key = 'cusp_deg_in_sign'  THEN value_number END) AS cusp_deg_in_sign,
    MAX(CASE WHEN fact_category = 'house_lord_placement'  AND fact_key = 'lord_graha'        THEN value_text   END) AS lord_graha,
    MAX(CASE WHEN fact_category = 'house_lord_placement'  AND fact_key = 'lord_sign'         THEN value_text   END) AS lord_sign,
    MAX(CASE WHEN fact_category = 'house_lord_placement'  AND fact_key = 'lord_house'        THEN value_number END) AS lord_house,
    MAX(CASE WHEN fact_category = 'house_lord_placement'  AND fact_key = 'lord_dignity'      THEN value_text   END) AS lord_dignity,
    MAX(CASE WHEN fact_category = 'house_occupant'        AND fact_key = 'occupant_graha'    THEN value_text   END) AS primary_occupant,
    build_id
  FROM chart_facts
  WHERE fact_category IN ('house_cusp_per_system', 'house_lord_placement', 'house_occupant')
  GROUP BY chart_id, ayanamsha_id, fact_subject, build_id
WITH DATA;

CREATE UNIQUE INDEX IF NOT EXISTS mv_chart_house_summary_idx
  ON mv_chart_house_summary (chart_id, ayanamsha_id, house_num, build_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- MV 3: mv_chart_yogas_active_at_birth
-- Fired yogas per chart
-- Source: yoga_fires
-- ─────────────────────────────────────────────────────────────────────────────
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_chart_yogas_active_at_birth AS
  SELECT
    chart_id,
    ayanamsha_id,
    fact_subject                                                              AS yoga_name,
    MAX(CASE WHEN fact_key = 'yoga_type'          THEN value_text   END)     AS yoga_type,
    MAX(CASE WHEN fact_key = 'yoga_active'        THEN value_text   END)     AS yoga_active,
    MAX(CASE WHEN fact_key = 'yoga_strength'      THEN value_number END)     AS yoga_strength,
    MAX(CASE WHEN fact_key = 'bhanga_factor'      THEN value_text   END)     AS bhanga_factor,
    MAX(CASE WHEN fact_key = 'triggering_planets' THEN value_text   END)     AS triggering_planets,
    build_id
  FROM chart_facts
  WHERE fact_category = 'yoga_fires'
  GROUP BY chart_id, ayanamsha_id, fact_subject, build_id
WITH DATA;

CREATE UNIQUE INDEX IF NOT EXISTS mv_chart_yogas_active_at_birth_idx
  ON mv_chart_yogas_active_at_birth (chart_id, ayanamsha_id, yoga_name, build_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- MV 4: mv_chart_vargas_summary
-- Per (chart, ayanamsha, graha×varga key, category): sign + dignity
-- Sources: varga_position, graha_dignity_per_varga
-- fact_subject encodes graha×varga (e.g. "SUN_D9"); writers set the convention.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_chart_vargas_summary AS
  SELECT
    chart_id,
    ayanamsha_id,
    fact_subject                                                               AS graha_varga_key,
    fact_category,
    MAX(CASE WHEN fact_key = 'varga'               THEN value_text   END)     AS varga,
    MAX(CASE WHEN fact_key = 'varga_sign'          THEN value_text   END)     AS varga_sign,
    MAX(CASE WHEN fact_key = 'varga_dignity'       THEN value_text   END)     AS varga_dignity,
    MAX(CASE WHEN fact_key = 'varga_house'         THEN value_number END)     AS varga_house,
    MAX(CASE WHEN fact_key = 'varga_pushkara_flag'    THEN value_text END)    AS varga_pushkara_flag,
    MAX(CASE WHEN fact_key = 'varga_vargottama_flag'  THEN value_text END)    AS varga_vargottama_flag,
    build_id
  FROM chart_facts
  WHERE fact_category IN ('varga_position', 'graha_dignity_per_varga')
  GROUP BY chart_id, ayanamsha_id, fact_subject, fact_category, build_id
WITH DATA;

CREATE UNIQUE INDEX IF NOT EXISTS mv_chart_vargas_summary_idx
  ON mv_chart_vargas_summary (chart_id, ayanamsha_id, graha_varga_key, fact_category, build_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- MV 5: mv_chart_sahams
-- All Saham positions per chart
-- Source: saham_position
-- ─────────────────────────────────────────────────────────────────────────────
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_chart_sahams AS
  SELECT
    chart_id,
    ayanamsha_id,
    fact_subject                                                          AS saham_name,
    MAX(CASE WHEN fact_key = 'saham_lon'      THEN value_number END)     AS saham_lon,
    MAX(CASE WHEN fact_key = 'saham_sign'     THEN value_text   END)     AS saham_sign,
    MAX(CASE WHEN fact_key = 'house_num'      THEN value_number END)     AS house_num,
    MAX(CASE WHEN fact_key = 'saham_category' THEN value_text   END)     AS saham_category,
    build_id
  FROM chart_facts
  WHERE fact_category = 'saham_position'
  GROUP BY chart_id, ayanamsha_id, fact_subject, build_id
WITH DATA;

CREATE UNIQUE INDEX IF NOT EXISTS mv_chart_sahams_idx
  ON mv_chart_sahams (chart_id, ayanamsha_id, saham_name, build_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- MV 6: mv_chart_arudhas
-- All arudha padas per chart
-- Sources: arudha_pada, house_arudha
-- ─────────────────────────────────────────────────────────────────────────────
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_chart_arudhas AS
  SELECT
    chart_id,
    ayanamsha_id,
    fact_subject                                                                  AS arudha_key,
    fact_category,
    MAX(CASE WHEN fact_key = 'arudha_sign'            THEN value_text   END)     AS arudha_sign,
    MAX(CASE WHEN fact_key = 'arudha_lon'             THEN value_number END)     AS arudha_lon,
    MAX(CASE WHEN fact_key = 'pada_name'              THEN value_text   END)     AS pada_name,
    MAX(CASE WHEN fact_key = 'arudha_house_from_lagna' THEN value_number END)    AS arudha_house_from_lagna,
    build_id
  FROM chart_facts
  WHERE fact_category IN ('arudha_pada', 'house_arudha')
  GROUP BY chart_id, ayanamsha_id, fact_subject, fact_category, build_id
WITH DATA;

CREATE UNIQUE INDEX IF NOT EXISTS mv_chart_arudhas_idx
  ON mv_chart_arudhas (chart_id, ayanamsha_id, arudha_key, fact_category, build_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- MV 7: mv_chart_shadbala_summary
-- Per (chart, ayanamsha, graha): all 6 sub-balas + total
-- Sources: graha_shadbala_* (6 sub-bala categories + total)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_chart_shadbala_summary AS
  SELECT
    chart_id,
    ayanamsha_id,
    fact_subject                                                                                AS graha,
    MAX(CASE WHEN fact_category = 'graha_shadbala_sthana'     AND fact_key = 'sthana_bala_rupas'    THEN value_number END) AS sthana_bala,
    MAX(CASE WHEN fact_category = 'graha_shadbala_dig'        AND fact_key = 'dig_bala_rupas'        THEN value_number END) AS dig_bala,
    MAX(CASE WHEN fact_category = 'graha_shadbala_kala'       AND fact_key = 'kala_bala_rupas'       THEN value_number END) AS kala_bala,
    MAX(CASE WHEN fact_category = 'graha_shadbala_cheshta'    AND fact_key = 'cheshta_bala_rupas'    THEN value_number END) AS cheshta_bala,
    MAX(CASE WHEN fact_category = 'graha_shadbala_naisargika' AND fact_key = 'naisargika_bala_rupas' THEN value_number END) AS naisargika_bala,
    MAX(CASE WHEN fact_category = 'graha_shadbala_drik'       AND fact_key = 'drik_bala_rupas'       THEN value_number END) AS drik_bala,
    MAX(CASE WHEN fact_category = 'graha_shadbala_total'      AND fact_key = 'total_rupas'           THEN value_number END) AS shadbala_total,
    MAX(CASE WHEN fact_category = 'graha_shadbala_total'      AND fact_key = 'minimum_required'      THEN value_number END) AS minimum_required,
    MAX(CASE WHEN fact_category = 'graha_shadbala_total'      AND fact_key = 'percent_of_required'   THEN value_number END) AS percent_of_required,
    MAX(CASE WHEN fact_category = 'graha_shadbala_total'      AND fact_key = 'shadbala_verdict'      THEN value_text   END) AS shadbala_verdict,
    build_id
  FROM chart_facts
  WHERE fact_category IN (
    'graha_shadbala_sthana', 'graha_shadbala_dig', 'graha_shadbala_kala',
    'graha_shadbala_cheshta', 'graha_shadbala_naisargika', 'graha_shadbala_drik',
    'graha_shadbala_total'
  )
  GROUP BY chart_id, ayanamsha_id, fact_subject, build_id
WITH DATA;

CREATE UNIQUE INDEX IF NOT EXISTS mv_chart_shadbala_summary_idx
  ON mv_chart_shadbala_summary (chart_id, ayanamsha_id, graha, build_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- MV 8: mv_chart_bhava_bala_summary
-- Per (chart, ayanamsha, house): sub-bala scores + total
-- Sources: house_bhava_bala_subscore, house_bhava_bala_total
-- ─────────────────────────────────────────────────────────────────────────────
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_chart_bhava_bala_summary AS
  SELECT
    chart_id,
    ayanamsha_id,
    fact_subject                                                                                  AS house_num,
    MAX(CASE WHEN fact_category = 'house_bhava_bala_subscore' AND fact_key = 'bhava_adhipati_bala' THEN value_number END) AS bhava_adhipati_bala,
    MAX(CASE WHEN fact_category = 'house_bhava_bala_subscore' AND fact_key = 'bhava_digbala'       THEN value_number END) AS bhava_digbala,
    MAX(CASE WHEN fact_category = 'house_bhava_bala_subscore' AND fact_key = 'bhava_drik_bala'     THEN value_number END) AS bhava_drik_bala,
    MAX(CASE WHEN fact_category = 'house_bhava_bala_total'    AND fact_key = 'bhava_bala_total'    THEN value_number END) AS bhava_bala_total,
    MAX(CASE WHEN fact_category = 'house_bhava_bala_total'    AND fact_key = 'rank_in_chart'       THEN value_number END) AS rank_in_chart,
    MAX(CASE WHEN fact_category = 'house_bhava_bala_total'    AND fact_key = 'bhava_verdict'       THEN value_text   END) AS bhava_verdict,
    build_id
  FROM chart_facts
  WHERE fact_category IN ('house_bhava_bala_subscore', 'house_bhava_bala_total')
  GROUP BY chart_id, ayanamsha_id, fact_subject, build_id
WITH DATA;

CREATE UNIQUE INDEX IF NOT EXISTS mv_chart_bhava_bala_summary_idx
  ON mv_chart_bhava_bala_summary (chart_id, ayanamsha_id, house_num, build_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- MV 9: mv_chart_ashtakavarga_summary
-- Per-graha + sarvashtakavarga rollups per (chart, ayanamsha, subject, category)
-- Sources: ashtakavarga_bindu, ashtakavarga_pinda_sarva, bhinashtakavarga_per_graha,
--          ashtakavarga_trikona_shodhana, ashtakavarga_ekadhipathya_shodhana,
--          ashtakavarga_pinda_sodhita, ashtakavarga_pinda_bhinna, ashtakavarga_kakshya
-- ─────────────────────────────────────────────────────────────────────────────
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_chart_ashtakavarga_summary AS
  SELECT
    chart_id,
    ayanamsha_id,
    fact_subject                                                             AS graha_or_house,
    fact_category,
    MAX(CASE WHEN fact_key = 'bindu_count'     THEN value_number END)       AS bindu_count,
    MAX(CASE WHEN fact_key = 'sarva_bindu'     THEN value_number END)       AS sarva_bindu,
    MAX(CASE WHEN fact_key = 'total_score'     THEN value_number END)       AS total_score,
    MAX(CASE WHEN fact_key = 'trikona_average' THEN value_number END)       AS trikona_average,
    build_id
  FROM chart_facts
  WHERE fact_category IN (
    'ashtakavarga_bindu', 'ashtakavarga_pinda_sarva', 'bhinashtakavarga_per_graha',
    'ashtakavarga_trikona_shodhana', 'ashtakavarga_ekadhipathya_shodhana',
    'ashtakavarga_pinda_sodhita', 'ashtakavarga_pinda_bhinna', 'ashtakavarga_kakshya'
  )
  GROUP BY chart_id, ayanamsha_id, fact_subject, fact_category, build_id
WITH DATA;

CREATE UNIQUE INDEX IF NOT EXISTS mv_chart_ashtakavarga_summary_idx
  ON mv_chart_ashtakavarga_summary (chart_id, ayanamsha_id, graha_or_house, fact_category, build_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- MV 10: mv_cross_ayanamsha_consensus
-- Per (chart, fact_category, fact_subject, fact_key):
--   agreement/divergence across all ayanamshas in the build
-- Source: all chart_facts rows (cross-ayanamsha pivot)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_cross_ayanamsha_consensus AS
  SELECT
    chart_id,
    fact_category,
    fact_subject,
    fact_key,
    COUNT(DISTINCT ayanamsha_id)  AS ayanamsha_count,
    COUNT(DISTINCT value_text)    AS text_divergence_count,
    MIN(value_number)             AS value_min,
    MAX(value_number)             AS value_max,
    ROUND(
      (MAX(value_number) - MIN(value_number))::numeric, 4
    )                             AS value_range,
    build_id
  FROM chart_facts
  GROUP BY chart_id, fact_category, fact_subject, fact_key, build_id
WITH DATA;

CREATE UNIQUE INDEX IF NOT EXISTS mv_cross_ayanamsha_consensus_idx
  ON mv_cross_ayanamsha_consensus (chart_id, fact_category, fact_subject, fact_key, build_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- MV 11: mv_chart_panchanga_birth_summary
-- Birth-day panchanga wide row per (chart, ayanamsha)
-- Sources: all panchanga_* categories
-- ─────────────────────────────────────────────────────────────────────────────
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_chart_panchanga_birth_summary AS
  SELECT
    chart_id,
    ayanamsha_id,
    MAX(CASE WHEN fact_category = 'panchanga_tithi'             AND fact_key = 'tithi_name'      THEN value_text   END) AS tithi_name,
    MAX(CASE WHEN fact_category = 'panchanga_tithi'             AND fact_key = 'tithi_num'       THEN value_number END) AS tithi_num,
    MAX(CASE WHEN fact_category = 'panchanga_tithi'             AND fact_key = 'tithi_elapsed_pct' THEN value_number END) AS tithi_elapsed_pct,
    MAX(CASE WHEN fact_category = 'panchanga_vara'              AND fact_key = 'vara_name'       THEN value_text   END) AS vara_name,
    MAX(CASE WHEN fact_category = 'panchanga_vara'              AND fact_key = 'vara_num'        THEN value_number END) AS vara_num,
    MAX(CASE WHEN fact_category = 'panchanga_nakshatra_moon'    AND fact_key = 'nakshatra'       THEN value_text   END) AS moon_nakshatra,
    MAX(CASE WHEN fact_category = 'panchanga_nakshatra_moon'    AND fact_key = 'nakshatra_pada'  THEN value_number END) AS moon_nakshatra_pada,
    MAX(CASE WHEN fact_category = 'panchanga_yoga'              AND fact_key = 'yoga_name'       THEN value_text   END) AS yoga_name,
    MAX(CASE WHEN fact_category = 'panchanga_karana'            AND fact_key = 'karana_name'     THEN value_text   END) AS karana_name,
    MAX(CASE WHEN fact_category = 'panchanga_calendrical'       AND fact_key = 'paksha'          THEN value_text   END) AS paksha,
    MAX(CASE WHEN fact_category = 'panchanga_calendrical'       AND fact_key = 'lunar_month_name' THEN value_text  END) AS lunar_month_name,
    MAX(CASE WHEN fact_category = 'panchanga_solar_context'     AND fact_key = 'sunrise_time'    THEN value_text   END) AS sunrise_time,
    MAX(CASE WHEN fact_category = 'panchanga_solar_context'     AND fact_key = 'sunset_time'     THEN value_text   END) AS sunset_time,
    MAX(CASE WHEN fact_category = 'panchanga_sun_moon_dynamics' AND fact_key = 'sun_moon_gap_deg' THEN value_number END) AS sun_moon_gap_deg,
    MAX(CASE WHEN fact_category = 'panchanga_special_yoga_combinations' AND fact_key = 'yoga_name' THEN value_text END) AS special_yoga_name,
    MAX(CASE WHEN fact_category = 'panchanga_hora_birth'        AND fact_key = 'hora_lord'       THEN value_text   END) AS hora_lord,
    MAX(CASE WHEN fact_category = 'panchanga_choghadiya_birth'  AND fact_key = 'choghadiya_name' THEN value_text   END) AS choghadiya_name,
    MAX(CASE WHEN fact_category = 'panchanga_rahu_kalam'        AND fact_key = 'covers_birth'    THEN value_text   END) AS rahu_kalam_covers_birth,
    MAX(CASE WHEN fact_category = 'panchanga_amrit_kaal'        AND fact_key = 'covers_birth'    THEN value_text   END) AS amrit_kaal_covers_birth,
    build_id
  FROM chart_facts
  WHERE fact_category IN (
    'panchanga_tithi', 'panchanga_vara', 'panchanga_nakshatra_moon',
    'panchanga_yoga', 'panchanga_karana', 'panchanga_calendrical',
    'panchanga_astronomical', 'panchanga_solar_context',
    'panchanga_sun_moon_dynamics', 'panchanga_special_yoga_combinations',
    'panchanga_abhijit_muhurta', 'panchanga_brahma_muhurta',
    'panchanga_rahu_kalam', 'panchanga_yamaganda_kalam',
    'panchanga_gulika_kalam', 'panchanga_durmuhurta',
    'panchanga_hora_birth', 'panchanga_choghadiya_birth',
    'panchanga_amrit_kaal', 'panchanga_varjyam'
  )
  GROUP BY chart_id, ayanamsha_id, build_id
WITH DATA;

CREATE UNIQUE INDEX IF NOT EXISTS mv_chart_panchanga_birth_summary_idx
  ON mv_chart_panchanga_birth_summary (chart_id, ayanamsha_id, build_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- MV 12: mv_chart_sensitive_points_summary
-- All sensitive points per (chart, ayanamsha, point_subject, category)
-- Sources: upagraha_position, aprakasha_position, esoteric_point_*,
--          lagna_position, mc_position, ic_position, descendant_position,
--          saturn_derived_point, swamsa_position, karakamsa_position
-- ─────────────────────────────────────────────────────────────────────────────
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_chart_sensitive_points_summary AS
  SELECT
    chart_id,
    ayanamsha_id,
    fact_subject                                                          AS point_subject,
    fact_category,
    MAX(CASE WHEN fact_key = 'lon'       THEN value_number END)          AS lon,
    MAX(CASE WHEN fact_key = 'sign'      THEN value_text   END)          AS sign,
    MAX(CASE WHEN fact_key = 'nakshatra' THEN value_text   END)          AS nakshatra,
    MAX(CASE WHEN fact_key = 'house_num' THEN value_number END)          AS house_num,
    build_id
  FROM chart_facts
  WHERE fact_category IN (
    'upagraha_position', 'aprakasha_position',
    'esoteric_point_yogi', 'esoteric_point_avayogi', 'esoteric_point_bhrigu_bindu',
    'esoteric_point_chatushphuta', 'esoteric_point_mrityu',
    'esoteric_point_panchasphuta', 'esoteric_point_trisphuta',
    'lagna_position', 'mc_position', 'ic_position', 'descendant_position',
    'saturn_derived_point', 'swamsa_position', 'karakamsa_position'
  )
  GROUP BY chart_id, ayanamsha_id, fact_subject, fact_category, build_id
WITH DATA;

CREATE UNIQUE INDEX IF NOT EXISTS mv_chart_sensitive_points_summary_idx
  ON mv_chart_sensitive_points_summary (chart_id, ayanamsha_id, point_subject, fact_category, build_id);

COMMIT;
