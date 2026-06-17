-- =============================================================================
-- 292_ga_nakshatra_registry.sql
-- Register ga_nakshatra in asset_registry.
-- No new tables — writes into chart_facts.
-- target_floor = NULL until first build (§N.4 floors aspirational).
-- Applied surgically — never via deploy.yml.
-- =============================================================================

BEGIN;

INSERT INTO asset_registry (
    asset_id, layer, sort_order,
    sanskrit_name, english_name, english_description,
    storage_type, target_table,
    count_sql, size_sql,
    target_floor, depends_on, scope, is_active
) VALUES (
    'ga_nakshatra', 'ganita', 20,
    'Nakṣatra-Paṭala', 'Nakshatra Parallel Chart',
    'Per-chart parallel nakshatra chart: placement+attribute JOIN from bg_nakshatra, '
    'KP sub-lords (star/sub/sub-sub/prana) per body and house cusp, nakshatra dispositor '
    'graph, gaṇḍānta severity flags, tara bala, per-chart statistics. Into chart_facts. '
    'Authoritative L1 nakshatra grain. Depends on bg_nakshatra + ga_positions.',
    'postgres_table', 'chart_facts',
    $count$SELECT count(*) FROM chart_facts
      WHERE chart_id = $1
        AND fact_category IN (
          'graha_nakshatra_join','graha_pada_join','nakshatra_lord_placement',
          'graha_kp_lords','cusp_kp_lords','graha_gandanta','graha_degree_flags',
          'nakshatra_dispositor','nakshatra_exchange','nakshatra_conjunction',
          'nakshatra_cogravity','graha_tara_bala','nakshatra_statistics',
          'nakshatra_cross_ayanamsha'
        )$count$,
    $$SELECT pg_total_relation_size('chart_facts')$$,
    NULL,
    ARRAY['bg_nakshatra','ga_positions'],
    'per_chart', true
)
ON CONFLICT (asset_id) DO UPDATE SET
    sort_order          = EXCLUDED.sort_order,
    english_name        = EXCLUDED.english_name,
    english_description = EXCLUDED.english_description,
    count_sql           = EXCLUDED.count_sql,
    depends_on          = EXCLUDED.depends_on;

COMMIT;
