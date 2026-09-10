-- 765_bo_upaya_volume_formula_prescriptions_scope.sql
--
-- NIRMĀṆA L2-W3 FIX (C12/F-L2-14 -- stale expected_volume_formula, formula/count_sql drift).
-- Transaction ownership belongs to platform/scripts/migrate.ts.
--
-- Migration 760 set bo_upaya's expected_volume_formula to 'GRAHAS * AYANAMSHAS' (= 45),
-- explicitly scoped to bodha_rm_resonances only -- its own comment states
-- "out of scope for this migration ... the sibling bodha_rm_remedy_prescriptions
-- table belongs to a separately-registered asset" (referring to PR #1920, then
-- still in flight).
--
-- #1920 has since merged and deployed. bo_upaya's live count_sql now sums BOTH
-- tables:
--   SELECT (SELECT count(*) FROM bodha_rm_resonances WHERE chart_id = $1)
--        + (SELECT count(*) FROM bodha_rm_remedy_prescriptions WHERE chart_id = $1)
-- Measured live across all three production charts: resonances = 45 (unchanged,
-- still exactly GRAHAS*AYANAMSHAS on every chart) and prescriptions = 135 on
-- every chart -- count_sql therefore returns 180, not 45, on all three charts.
-- The stored formula '45' no longer describes what count_sql measures; this is
-- exactly the drift class F-L2-14 exists to catch, just on the metadata side
-- rather than the data side.
--
-- Corrected formula: bo_upaya.py's own bo_upaya's M-14 integrity_check_sql
-- (migration referenced in asset_registry, verified live loop 298) already
-- encodes prescriptions as CAPPED, not fixed, per resonance:
--   GROUP BY chart_id, ayanamsha_id, target_resonance_id HAVING count(*) > 3
-- i.e. 0-3 prescriptions per resonance, not always exactly 3 -- production
-- happens to be fully saturated today (135 = 3*45 on all three charts), but
-- the writer's own cap does not guarantee that saturation for every future
-- chart (a resonance can legitimately have fewer prescription matches).
-- Per the same discipline already used for bo_arudha/bo_vargottama_dhana
-- (bound formulas, not point formulas, when a sub-count is capped-but-variable),
-- this migration widens the formula to a bound rather than asserting the
-- currently-observed saturation as a permanent fact.

UPDATE asset_registry
   SET expected_volume_formula = 'GRAHAS * AYANAMSHAS <= ROWS <= GRAHAS * AYANAMSHAS * (1 + MAX_PRESCRIPTIONS_PER_RESONANCE)',
       expected_volume_inputs = jsonb_build_object(
         'GRAHAS', 9,
         'AYANAMSHAS', 5,
         'MAX_PRESCRIPTIONS_PER_RESONANCE', 3,
         'lower_bound', 45,
         'upper_bound', 180,
         'grahas_meaning', 'Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu (bo_upaya.py KNOWN_GRAHAS)',
         'scope_correction', 'migration 760 scoped this formula to bodha_rm_resonances only (45), matching count_sql at the time; #1920 (merged) broadened count_sql to sum bodha_rm_resonances + bodha_rm_remedy_prescriptions, making the old point-formula stale relative to what count_sql now measures',
         'prescriptions_bound_source', 'this asset''s own integrity_check_sql: GROUP BY chart_id, ayanamsha_id, target_resonance_id HAVING count(*) > 3 (0-3 prescriptions per resonance, not fixed)',
         'measured', 180,
         'measured_resonances', 45,
         'measured_prescriptions', 135,
         'measured_on_charts', jsonb_build_array(
           '482012f1-710e-4a25-994a-93821f5871aa',
           '1c826d5a-41cb-4450-b4dc-59d440e5f75a',
           'cb73cd3d-9eba-4220-9902-0de91566e980'
         ),
         'contract_ref', 'platform/python-sidecar/pipeline/orchestrator/writers/bo_upaya.py:44-51,485'
       ),
       volume_explanation = '9 grahas x 5 ayanamshas = 45 resonance rows per chart (unchanged from '
         || 'migration 760). count_sql now also sums bodha_rm_remedy_prescriptions, capped at 0-3 '
         || 'per resonance by the writer''s own logic (matching this asset''s own M-14 check''s '
         || 'max-3-per-resonance guard) -- so the honest range is 45 (no prescriptions matched '
         || 'anywhere) to 180 (every resonance saturated at 3), not a fixed point. All three '
         || 'production charts currently measure the saturated maximum (180 = 45 + 135), but the '
         || 'writer does not guarantee saturation for every future chart, so this migration asserts '
         || 'the true bound rather than the currently-observed value, correcting migration 760''s '
         || 'formula which described only the pre-#1920 resonances-only scope of count_sql.'
 WHERE asset_id = 'bo_upaya';
