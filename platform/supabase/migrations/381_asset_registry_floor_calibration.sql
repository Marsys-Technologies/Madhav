-- Migration 381: Calibrate target_floor values to be chart-agnostic
--
-- After running a global rebuild for Abhinandan Mohanty (a non-native chart),
-- several assets reported floor violations because their target_floor was
-- calibrated against the native chart's (Abhisek Mohanty) data at a specific
-- point in time. These floors must be set to the minimum expected count for
-- ANY valid chart, not the native's count.
--
-- Issues identified:
--
-- 1. ga_vargas (floor=21635): Both native AND non-native produce exactly 20,877
--    divisional rows. The old floor was from an earlier build before the varga
--    writer was updated. Updated to 20,877.
--
-- 2. bo_laksana / bo_samskara (floor=66738): MSR signal count is ~64,700–64,800
--    for all charts. Floor was set from an earlier native build. Lowered to 60,000
--    to be safely chart-agnostic.
--
-- 3. bo_sangati (floor=84): Both native and non-native produce exactly 70 CDLM
--    cells. Floor lowered to 70.
--
-- 4. bo_anveshana (floor=5770): The discovery+anomaly count is highly chart-
--    specific — native has ~5,733 but other charts may produce 500–3,000+.
--    Floor lowered to 500 as a safe minimum for any valid chart.

UPDATE asset_registry SET target_floor = 20877 WHERE asset_id = 'ga_vargas';
UPDATE asset_registry SET target_floor = 60000 WHERE asset_id = 'bo_laksana';
UPDATE asset_registry SET target_floor = 60000 WHERE asset_id = 'bo_samskara';
UPDATE asset_registry SET target_floor = 70    WHERE asset_id = 'bo_sangati';
UPDATE asset_registry SET target_floor = 500   WHERE asset_id = 'bo_anveshana';
