-- 843_nirmana_l1_ga_panchanga_target_floor.sql
--
-- NIRMĀṆA L1 Gaṇita — W3 IMPLEMENT, fourth in the 840-859 range (adjudication #2101, L1
-- continuation 5). Closes F-B31 (L1_W1_ANALYSIS_BATCH_B.md): ga_panchanga's `target_floor`
-- was still 221 against a live achieved count of 437 (confirmed live via count_sql re-execution,
-- cycle 105) -- the same stale-floor defect class as F-A9/F-B1/F-D14/F-E1/F-E15 (already
-- re-baselined per cycle 103's investigation), just never itself corrected. The finding's own
-- second half -- a false `expected_volume_formula = 'AYANAMSHAS'` evaluating to 5 against 437
-- rows -- is ALREADY fixed: the registry's `expected_volume_formula` is NULL today, confirmed
-- live; only the floor number itself was left behind.
--
-- Per §N.4 (floors aspirational, not gates): target_floor = achieved count after build, never
-- fabricated to hit a number. 437 is the live, re-measured achieved count for the canonical
-- chart (482012f1) today -- not a new computation, a re-baseline of an already-stale number,
-- same discipline as migrations 293/294/296.

BEGIN;

UPDATE asset_registry SET target_floor = 437 WHERE asset_id = 'ga_panchanga';

COMMIT;
