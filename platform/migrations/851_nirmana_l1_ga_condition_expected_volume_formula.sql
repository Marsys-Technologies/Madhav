-- 851_nirmana_l1_ga_condition_expected_volume_formula.sql
--
-- NIRMĀṆA L1 Gaṇita — W3 IMPLEMENT, ninth in the 840-859 range (adjudication #2101, L1
-- continuation 5). Note: 848-850 in this same granted range were found used by L3 branches
-- (cycle 124 discovery, filed as adjudication #2156) -- 851 confirmed genuinely free across
-- origin/main and all open branches at time of use.
--
-- Closes F-C10 (L1_W1_ANALYSIS_BATCH_C.md, MUST, C12/D-126; §N.4; §N.8): ga_condition's
-- `target_floor` (2,880) is a genuine, live-verified achieved count (re-confirmed live this
-- cycle via the asset's own count_sql, chart 482012f1) -- the floor itself is NOT wrong. The
-- finding's real complaint is that `expected_volume_formula` was NULL, leaving the 2,880
-- figure an undocumented arithmetic identity rather than a derived, auditable formula (C12:
-- "derive, never pick"). Populating it with the real, live-verified component breakdown:
--
--   ga_condition_composite                    45
--   graha_avastha_baladi_per_varga          1,305
--   graha_avastha_deeptaadi_per_varga        1,305
--   graha_avastha_jagradadi_per_varga           45
--   graha_avastha_lajjitadi                     45
--   graha_avastha_lajjitadi_per_varga           45
--   graha_avastha_sayanadi                      45
--   graha_avastha_sayanadi_per_varga            45
--   -----------------------------------------------
--   TOTAL                                    2,880
--
-- = 45*6 + 1305*2 = 270 + 2610 = 2880, matching target_floor and the live count_sql result
-- exactly (re-verified live, not assumed from the finding's own slightly different arithmetic
-- grouping "45 + 1,305 + 1,305 + 45×5" -- this migration's grouping is the one actually
-- verified against live category-by-category counts this cycle).
--
-- ga_condition is a fully deterministic structural asset (one row per graha per varga/avastha
-- type, no variable-length data), so an exact arithmetic identity is the CORRECT floor here
-- -- unlike F-B13's target_floor=0 (unfalsifiable) or F-E15's chart-varying scalar (wrong for
-- 2/3 charts), this asset's row count genuinely never varies. The fix is documentation, not
-- re-derivation: making the already-correct number's derivation auditable rather than a bare
-- undocumented constant.

BEGIN;

UPDATE asset_registry
SET expected_volume_formula = '45(ga_condition_composite) + 1305(graha_avastha_baladi_per_varga) + 1305(graha_avastha_deeptaadi_per_varga) + 45(graha_avastha_jagradadi_per_varga) + 45(graha_avastha_lajjitadi) + 45(graha_avastha_lajjitadi_per_varga) + 45(graha_avastha_sayanadi) + 45(graha_avastha_sayanadi_per_varga) = 2880'
WHERE asset_id = 'ga_condition';

COMMIT;
