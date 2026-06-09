-- Migration 207: GA3 materialized views
-- Creates MVs for natal-fixed chart_facts categories (A3 §10).
-- Rule (locked): MVs are ONLY for time-invariant natal data.
-- Refresh: synchronous at build close. builds.status only flips to 'complete'
--          after MVs refresh.
-- Per: GA3_CHART_FACTS_WRITER_BRIEF §10, A3_CHART_FACTS_SPEC §10.
-- All MVs: IF NOT EXISTS (idempotent).

BEGIN;

-- ── 1. mv_chart_planet_summary ────────────────────────────────────────────────
-- One row per (chart_id, ayanamsha_id, build_id, graha) aggregating core position facts.

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_chart_planet_summary AS
SELECT
  chart_id,
  ayanamsha_id,
  build_id,
  fact_subject                                  AS graha,
  MAX(CASE WHEN fact_key = 'longitude_sidereal' THEN fact_value_num END) AS longitude_sidereal,
  MAX(CASE WHEN fact_key = 'sign'               THEN fact_value_text END) AS sign,
  MAX(CASE WHEN fact_key = 'nakshatra'           THEN fact_value_text END) AS nakshatra,
  MAX(CASE WHEN fact_key = 'pada'               THEN fact_value_num END)  AS pada,
  MAX(CASE WHEN fact_key = 'house_d1'           THEN fact_value_num END)  AS house_d1,
  MAX(CASE WHEN fact_key = 'retrograde_flag'    THEN fact_value_text END) AS retrograde_flag,
  MAX(CASE WHEN fact_key = 'sign_lord'          THEN fact_value_text END) AS sign_lord,
  MAX(CASE WHEN fact_key = 'nakshatra_lord'     THEN fact_value_text END) AS nakshatra_lord
FROM chart_facts
WHERE fact_category IN ('graha_position', 'graha_speed_state', 'graha_retrogression_state',
                         'graha_sign_attributes', 'graha_combustion_state')
GROUP BY chart_id, ayanamsha_id, build_id, fact_subject;

CREATE UNIQUE INDEX IF NOT EXISTS mv_chart_planet_summary_idx
  ON mv_chart_planet_summary (chart_id, ayanamsha_id, build_id, graha);

-- ── 2. mv_chart_shadbala_summary ─────────────────────────────────────────────
-- One row per (chart_id, ayanamsha_id, build_id, graha) joining all shadbala sub-scores + total.

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_chart_shadbala_summary AS
SELECT
  chart_id,
  ayanamsha_id,
  build_id,
  fact_subject                                    AS graha,
  MAX(CASE WHEN fact_category = 'graha_shadbala_sthana'     THEN fact_value_num END) AS shadbala_sthana,
  MAX(CASE WHEN fact_category = 'graha_shadbala_dig'        THEN fact_value_num END) AS shadbala_dig,
  MAX(CASE WHEN fact_category = 'graha_shadbala_kala'       THEN fact_value_num END) AS shadbala_kala,
  MAX(CASE WHEN fact_category = 'graha_shadbala_cheshta'    THEN fact_value_num END) AS shadbala_cheshta,
  MAX(CASE WHEN fact_category = 'graha_shadbala_naisargika' THEN fact_value_num END) AS shadbala_naisargika,
  MAX(CASE WHEN fact_category = 'graha_shadbala_drik'       THEN fact_value_num END) AS shadbala_drik,
  MAX(CASE WHEN fact_category = 'graha_shadbala_total'      THEN fact_value_num END) AS shadbala_total,
  MAX(CASE WHEN fact_category = 'graha_ishta_phala'         THEN fact_value_num END) AS ishta_phala,
  MAX(CASE WHEN fact_category = 'graha_kashta_phala'        THEN fact_value_num END) AS kashta_phala,
  MAX(CASE WHEN fact_category = 'graha_vimsopaka_shodasavarga' THEN fact_value_num END) AS vimsopaka_shodasavarga
FROM chart_facts
WHERE fact_category IN (
  'graha_shadbala_sthana', 'graha_shadbala_dig', 'graha_shadbala_kala',
  'graha_shadbala_cheshta', 'graha_shadbala_naisargika', 'graha_shadbala_drik',
  'graha_shadbala_total', 'graha_ishta_phala', 'graha_kashta_phala',
  'graha_vimsopaka_shodasavarga'
)
GROUP BY chart_id, ayanamsha_id, build_id, fact_subject;

CREATE UNIQUE INDEX IF NOT EXISTS mv_chart_shadbala_summary_idx
  ON mv_chart_shadbala_summary (chart_id, ayanamsha_id, build_id, graha);

-- ── 3. mv_chart_ashtakavarga_summary ─────────────────────────────────────────
-- Per-graha ashtakavarga totals + sarvashtakavarga rollup.

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_chart_ashtakavarga_summary AS
SELECT
  chart_id,
  ayanamsha_id,
  build_id,
  fact_subject                                    AS graha_or_sarva,
  MAX(CASE WHEN fact_category = 'ashtakavarga_pinda_sodhita' THEN fact_value_num END) AS pinda_sodhita,
  MAX(CASE WHEN fact_category = 'ashtakavarga_pinda_bhinna'  THEN fact_value_num END) AS pinda_bhinna,
  MAX(CASE WHEN fact_category = 'ashtakavarga_pinda_sarva'   THEN fact_value_num END) AS pinda_sarva,
  SUM(CASE WHEN fact_category = 'ashtakavarga_bindu'         THEN fact_value_num ELSE 0 END) AS total_bindus
FROM chart_facts
WHERE fact_category IN (
  'ashtakavarga_bindu', 'ashtakavarga_pinda_sodhita', 'ashtakavarga_pinda_bhinna',
  'ashtakavarga_pinda_sarva'
)
GROUP BY chart_id, ayanamsha_id, build_id, fact_subject;

CREATE UNIQUE INDEX IF NOT EXISTS mv_chart_ashtakavarga_summary_idx
  ON mv_chart_ashtakavarga_summary (chart_id, ayanamsha_id, build_id, graha_or_sarva);

-- ── 4. mv_chart_bhava_bala_summary ───────────────────────────────────────────
-- One row per (chart_id, ayanamsha_id, build_id, house) joining all bhava_bala subscores + total.

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_chart_bhava_bala_summary AS
SELECT
  chart_id,
  ayanamsha_id,
  build_id,
  fact_subject                                    AS house,
  MAX(CASE WHEN fact_key = 'total' THEN fact_value_num END) AS bhava_bala_total,
  SUM(CASE WHEN fact_category = 'house_bhava_bala_subscore' THEN fact_value_num ELSE 0 END) AS bhava_bala_sum_subscores
FROM chart_facts
WHERE fact_category IN ('house_bhava_bala_subscore', 'house_bhava_bala_total')
GROUP BY chart_id, ayanamsha_id, build_id, fact_subject;

CREATE UNIQUE INDEX IF NOT EXISTS mv_chart_bhava_bala_summary_idx
  ON mv_chart_bhava_bala_summary (chart_id, ayanamsha_id, build_id, house);

-- ── 5. mv_cross_ayanamsha_consensus ──────────────────────────────────────────
-- Per (chart_id, fact_category, fact_subject, fact_key, build_id):
-- count of ayanamshas that agree (same text value) vs diverge.

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_cross_ayanamsha_consensus AS
SELECT
  chart_id,
  build_id,
  fact_category,
  fact_subject,
  fact_key,
  COUNT(DISTINCT ayanamsha_id)                    AS ayanamsha_count,
  COUNT(DISTINCT fact_value_text)                 AS distinct_text_values,
  COUNT(DISTINCT ROUND(fact_value_num, 2))        AS distinct_num_values,
  MIN(fact_value_num)                             AS min_value,
  MAX(fact_value_num)                             AS max_value,
  MAX(fact_value_num) - MIN(fact_value_num)       AS max_divergence,
  CASE WHEN COUNT(DISTINCT fact_value_text) = 1
            OR COUNT(DISTINCT ROUND(fact_value_num, 4)) = 1
       THEN TRUE ELSE FALSE END                   AS all_ayanamshas_agree
FROM chart_facts
GROUP BY chart_id, build_id, fact_category, fact_subject, fact_key;

CREATE INDEX IF NOT EXISTS mv_cross_ayanamsha_consensus_chart_idx
  ON mv_cross_ayanamsha_consensus (chart_id, build_id, fact_category);

COMMIT;

-- DOWN:
-- DROP MATERIALIZED VIEW IF EXISTS mv_cross_ayanamsha_consensus;
-- DROP MATERIALIZED VIEW IF EXISTS mv_chart_bhava_bala_summary;
-- DROP MATERIALIZED VIEW IF EXISTS mv_chart_ashtakavarga_summary;
-- DROP MATERIALIZED VIEW IF EXISTS mv_chart_shadbala_summary;
-- DROP MATERIALIZED VIEW IF EXISTS mv_chart_planet_summary;
