-- Migration 327: Activate is_active for all L2 Bodha assets so cockpit stats route includes them.
-- Also fixes bo_samvada count_sql (pointed to empty bodha_chart_gestalt; correct table is vw_chart_digest).
-- The stats route (platform/src/app/api/cockpit/stats/route.ts) filters WHERE is_active = true;
-- migration 326 set catalog_status=CURRENT but never set is_active, leaving 10 bo_* assets invisible.
BEGIN;

UPDATE asset_registry SET is_active = true
WHERE asset_id IN (
  'bo_laksana','bo_sangati','bo_karanajala','bo_bimba','bo_samskara',
  'bo_samvada','bo_upaya','bo_drishti','bo_anveshana','bo_pramana_mapa'
);

-- Fix bo_samvada count_sql: writer creates vw_chart_digest VIEW, not bodha_chart_gestalt table.
UPDATE asset_registry
SET count_sql = 'SELECT count(*) FROM vw_chart_digest WHERE chart_id = $1'
WHERE asset_id = 'bo_samvada';

COMMIT;
