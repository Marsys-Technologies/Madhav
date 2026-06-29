-- Migration 360: Align bodha asset_registry sort_order to topological execution order
-- Fixes 5 dependency ordering violations where dependencies had higher sort_order
-- than the assets depending on them. The Build Plan dialog uses topo sort (correct)
-- while the expanded layer table uses sort_order — these now agree.
-- Build execution is unaffected (orchestrator always uses topo sort, not sort_order).
--
-- Violations fixed:
--   bo_karanajala (was 2) depends on bo_bimba (was 3)  → bimba must come first
--   bo_samvada    (was 7) depends on bo_pramana_mapa (was 8) → pramana_mapa must come first
--   bo_pramana_mapa (was 8) depends on bo_drishti (was 9) + bo_anveshana (was 10)
--   bo_chart_gestalt (was 90) depends on bo_cgm_paths (was 93)
--
-- Full Bodha sort_order reassigned (all 14 assets) using Kahn's topological sort
-- with alphabetical tiebreaking within levels.
--
-- New order (level → asset):
--   1  bo_laksana      (root, no bodha deps)
--   2  bo_bimba        (dep: bo_laksana)
--   3  bo_karanajala   (dep: bo_laksana, bo_bimba)
--   4  bo_cgm_motifs   (dep: bo_bimba, bo_karanajala)
--   5  bo_cgm_paths    (dep: bo_bimba, bo_karanajala)
--   6  bo_samskara     (dep: bo_laksana)
--   7  bo_sangati      (dep: bo_laksana, bo_karanajala)
--   8  bo_cdlm_summary (dep: bo_sangati)
--   9  bo_drishti      (dep: bo_laksana, bo_sangati, bo_karanajala)
--  10  bo_anveshana    (dep: bo_sangati, bo_karanajala, bo_samskara, bo_drishti, bo_bimba, bo_laksana)
--  11  bo_chart_gestalt(dep: bo_laksana, bo_sangati, bo_bimba, bo_cgm_paths, bo_anveshana)
--  12  bo_upaya        (dep: bo_laksana, bo_sangati)
--  13  bo_pramana_mapa (dep: bo_upaya, bo_drishti, bo_anveshana, bo_laksana, bo_sangati, bo_bimba, bo_karanajala, bo_samskara)
--  14  bo_samvada      (dep: bo_laksana, bo_karanajala, bo_upaya, bo_sangati, bo_pramana_mapa)

UPDATE asset_registry SET sort_order = 1  WHERE asset_id = 'bo_laksana';
UPDATE asset_registry SET sort_order = 2  WHERE asset_id = 'bo_bimba';
UPDATE asset_registry SET sort_order = 3  WHERE asset_id = 'bo_karanajala';
UPDATE asset_registry SET sort_order = 4  WHERE asset_id = 'bo_cgm_motifs';
UPDATE asset_registry SET sort_order = 5  WHERE asset_id = 'bo_cgm_paths';
UPDATE asset_registry SET sort_order = 6  WHERE asset_id = 'bo_samskara';
UPDATE asset_registry SET sort_order = 7  WHERE asset_id = 'bo_sangati';
UPDATE asset_registry SET sort_order = 8  WHERE asset_id = 'bo_cdlm_summary';
UPDATE asset_registry SET sort_order = 9  WHERE asset_id = 'bo_drishti';
UPDATE asset_registry SET sort_order = 10 WHERE asset_id = 'bo_anveshana';
UPDATE asset_registry SET sort_order = 11 WHERE asset_id = 'bo_chart_gestalt';
UPDATE asset_registry SET sort_order = 12 WHERE asset_id = 'bo_upaya';
UPDATE asset_registry SET sort_order = 13 WHERE asset_id = 'bo_pramana_mapa';
UPDATE asset_registry SET sort_order = 14 WHERE asset_id = 'bo_samvada';
