-- 343_ka_tulana_has_writer.sql
--
-- ka_tulana now has a self-test writer; include it in build plans so displayed=built (12/12).
-- Also defensively correct asset_type='service' for ka_gochara, ka_dasha_kala, ka_tulana
-- (only ka_graha_sancara + ka_muhurta_seva were corrected in migration 342).
--
-- METADATA-ONLY: touches asset_registry only — NO chart data tables.
-- Does NOT trigger a build or rebuild of any ka_* asset.

UPDATE asset_registry SET has_writer = true WHERE asset_id = 'ka_tulana';

UPDATE asset_registry
  SET asset_type = 'service'
  WHERE asset_id IN ('ka_gochara', 'ka_dasha_kala', 'ka_tulana')
    AND asset_type = 'data';
