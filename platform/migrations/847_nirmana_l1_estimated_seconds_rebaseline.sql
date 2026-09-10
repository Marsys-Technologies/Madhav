-- 847_nirmana_l1_estimated_seconds_rebaseline.sql
--
-- NIRMĀṆA L1 Gaṇita — W3 IMPLEMENT, eighth in the 840-859 range (adjudication #2101, L1
-- continuation 5). Closes F-A16 / F-B22 / F-C12 / F-D12 (L1_W1_ANALYSIS_BATCH_A/B/C/D.md):
-- five assets' `estimated_seconds` were declared, never re-measured against the ACTUAL
-- `build_run_assets` history since the findings were originally written (2026-08-06/08/10) --
-- confirmed live, cycle 110, all five still carrying stale numbers:
--
--   asset          | old estimate | live mean (n runs, complete builds only) | max observed
--   ga_positions    |  5s          | 17.0s  (n=54)                            | 165.1s
--   ga_nakshatra    | 16s          | 58.8s  (n=48)                             | 395.1s
--   ga_condition    | 30s          | 71.4s  (n=51)                             | 297.0s
--   ga_sade_sati    | 65s          | 141.9s (n=51)                             | 783.0s
--   ga_vichara      | 30s          | 307.1s (n=18)                             | 1272.2s
--
-- `estimated_seconds` re-measured here is the LIVE mean, re-queried fresh from
-- `build_run_assets` (EXTRACT(EPOCH FROM (ended_at - started_at)), state='complete' only) --
-- not copy-pasted from the original findings' own numbers, which themselves predate ~2 months
-- of additional build history. ga_positions' live mean (17.0s, n=54) matches F-A16's own quoted
-- "mean 17s over 54 runs" exactly, confirming the re-measurement methodology agrees with the
-- original finding's own approach. `ga_vargas` (94s) and `ga_dashas` (564s) were confirmed
-- ACCURATE by F-A16 itself and are correctly left untouched here.
--
-- Per D-SERVICE (cost truth): this is a UX/scheduling estimate, not a correctness gate --
-- getting it right matters for W4 dispatch planning, not for any build-fatal assertion.

BEGIN;

UPDATE asset_registry SET estimated_seconds = 17  WHERE asset_id = 'ga_positions';
UPDATE asset_registry SET estimated_seconds = 59  WHERE asset_id = 'ga_nakshatra';
UPDATE asset_registry SET estimated_seconds = 71  WHERE asset_id = 'ga_condition';
UPDATE asset_registry SET estimated_seconds = 142 WHERE asset_id = 'ga_sade_sati';
UPDATE asset_registry SET estimated_seconds = 307 WHERE asset_id = 'ga_vichara';

COMMIT;
