-- 727_bo_pratijna_volume_formula.sql
--
-- NIRMĀṆA L2-W3 IMPLEMENT (C12; F-L2-14 -- expected_volume_formula gap).
-- Transaction ownership belongs to platform/scripts/migrate.ts.
--
-- Fifth asset in the F-L2-14 sweep (660_nirmana_l2_registry_accuracy.sql
-- fixed six; 723/724/725/726 added bo_arudha, bo_special_lagna,
-- bo_sudarshana, bo_vargottama_dhana this campaign). Back to a clean
-- fixed-tiling formula, same shape as bo_drishti's.
--
-- bo_pratijna (PRATIJÑĀ v4 rubric engine, bodha_pratijna table) emits
-- exactly one row per (chart_id, ayanamsha_id, event_class_id) -- a real
-- UNIQUE-style tiling, not an estimate: this asset's own M-14 check already
-- enforces BOTH directions of it live --
--   1. completeness: a FULL OUTER JOIN-equivalent check confirms every
--      (ayanamsha x event_class) combination in the fixed 5 x 27 grid has a
--      row (the check's own hardcoded ayanamsha/event_class arrays);
--   2. no-duplication: GROUP BY (chart_id, ayanamsha_id, event_class_id)
--      HAVING count(*) > 1 fails outright.
-- AYANAMSHAS=5, EVENT_CLASSES=27 (the check's own literal array, alphabetic:
-- achievement_recognition .. travel_event) => 135 rows/chart, exactly.
--
-- Measured live across all three production charts before landing (C12:
-- never a formula that has yet to be checked against real data): all three
-- charts measure exactly 135 -- no exceptions, matching the tiling exactly.

UPDATE asset_registry
   SET expected_volume_formula = 'AYANAMSHAS * EVENT_CLASSES',
       expected_volume_inputs = jsonb_build_object(
         'AYANAMSHAS', 5,
         'EVENT_CLASSES', 27,
         'uniqueness', '(chart_id, ayanamsha_id, event_class_id)',
         'measured', 135,
         'measured_on_charts', jsonb_build_array(
           '482012f1-710e-4a25-994a-93821f5871aa',
           '1c826d5a-41cb-4450-b4dc-59d440e5f75a',
           'cb73cd3d-9eba-4220-9902-0de91566e980'
         ),
         'contract_ref', 'this asset''s own integrity_check_sql (asset_registry.bo_pratijna) -- the 27-element event_class_id array and 5-element ayanamsha array are its own literals'
       ),
       volume_explanation = '5 ayanamshas x 27 event classes = 135 pratijna rows per chart, one '
         || 'per (chart_id, ayanamsha_id, event_class_id). Not an estimate: this asset''s own '
         || 'M-14 check already enforces this as a tiling in both directions -- a completeness '
         || 'join over the fixed grid AND a no-duplicate GROUP BY HAVING count(*) > 1 guard. A '
         || 'count other than 135 means a partially-completed build the completeness check would '
         || 'already have caught; this migration restates that same claim at the registry level.'
 WHERE asset_id = 'bo_pratijna';
