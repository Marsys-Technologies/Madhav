-- 846_nirmana_l1_ga_vichara_target_floor.sql
--
-- NIRMĀṆA L1 Gaṇita — W3 IMPLEMENT, seventh in the 840-859 range (adjudication #2101, L1
-- continuation 5). Closes the residual half of F-D10 (L1_W1_ANALYSIS_BATCH_D.md): the finding's
-- own derived model (5 × (1595 + 35 + 9 + 9) + 9 = 8,249, confirmed live against
-- `chart_vichara`'s exact count_sql today) was already applied to `target_floor` at some point
-- -- but landed as 8,240, nine short of the derivation's own number. `target_floor` passing the
-- achieved-count gate (8,249 >= 8,240) hid the drift; it never surfaced as a build failure,
-- only as a stale registry number.
--
-- Per §N.4 (floors aspirational, not gates): target_floor = achieved count after build. 8,249 is
-- the live, re-measured achieved count today (re-verified via `chart_vichara`'s own count_sql,
-- not re-derived from scratch) -- a nine-row correction to an already-close number, same
-- discipline as migrations 843/845.

BEGIN;

UPDATE asset_registry SET target_floor = 8249 WHERE asset_id = 'ga_vichara';

COMMIT;
