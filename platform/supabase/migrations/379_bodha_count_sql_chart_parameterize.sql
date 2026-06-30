-- Migration 379: parameterize remaining bo_* count_sqls
--
-- Migration 230 (bodha_registry_reconcile) hardcoded the native chart_id
-- '482012f1-710e-4a25-994a-93821f5871aa' in 8 bo_* count_sqls.
-- Migrations 370/371 fixed bo_samvada and bo_upaya (the only two addressed so far).
-- The remaining 6 still reference the native chart_id, so the stats route
-- returns incorrect row counts for every non-native chart build.
--
-- Pattern: replace literal UUID with $1 — the stats route passes chart_id as $1
-- (platform/src/app/api/cockpit/stats/route.ts line ~160:
--   const countParams = /\$1/.test(asset.count_sql) ? [chartId] : []
-- )
--
-- Assets fixed here:
--   bo_laksana    → bodha_msr_signals
--   bo_bimba      → bodha_cgm_nodes
--   bo_karanajala → bodha_cgm_edges
--   bo_samskara   → bodha_signal_embeddings
--   bo_sangati    → bodha_cdlm_cells
--   bo_pramana_mapa → synthesis_quality_scorecard

UPDATE asset_registry
SET count_sql = 'SELECT count(*) FROM bodha_msr_signals WHERE chart_id = $1'
WHERE asset_id = 'bo_laksana';

UPDATE asset_registry
SET count_sql = 'SELECT count(*) FROM bodha_cgm_nodes WHERE chart_id = $1'
WHERE asset_id = 'bo_bimba';

UPDATE asset_registry
SET count_sql = 'SELECT count(*) FROM bodha_cgm_edges WHERE chart_id = $1'
WHERE asset_id = 'bo_karanajala';

UPDATE asset_registry
SET count_sql = 'SELECT count(*) FROM bodha_signal_embeddings WHERE chart_id = $1'
WHERE asset_id = 'bo_samskara';

UPDATE asset_registry
SET count_sql = 'SELECT count(*) FROM bodha_cdlm_cells WHERE chart_id = $1'
WHERE asset_id = 'bo_sangati';

UPDATE asset_registry
SET count_sql = 'SELECT count(*) FROM synthesis_quality_scorecard WHERE chart_id = $1'
WHERE asset_id = 'bo_pramana_mapa';

-- Sanity check: confirm all 6 rows were updated (no orphan asset_ids)
DO $$
DECLARE
  still_hardcoded int;
BEGIN
  SELECT count(*) INTO still_hardcoded
  FROM asset_registry
  WHERE asset_id IN ('bo_laksana','bo_bimba','bo_karanajala','bo_samskara','bo_sangati','bo_pramana_mapa')
    AND count_sql LIKE '%482012f1%';

  IF still_hardcoded > 0 THEN
    RAISE EXCEPTION
      'migration 379 sanity check failed: % bo_* assets still have hardcoded native chart_id in count_sql.',
      still_hardcoded;
  END IF;
END $$;
