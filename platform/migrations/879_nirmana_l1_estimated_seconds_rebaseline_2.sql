-- 879_nirmana_l1_estimated_seconds_rebaseline_2.sql
--
-- NIRMĀṆA L1 Gaṇita — W6 close-prep (L1_W6_CLOSE_REPORT_v1_0.md §4's own noted OPEN item,
-- cycle 187). Continues migration 847's exact methodology (EXTRACT(EPOCH FROM
-- (ended_at - started_at)), state='complete' only, live re-query against build_run_assets,
-- not copy-pasted from any prior finding) for the assets migration 847 either never touched
-- or, in two cases, explicitly declared accurate at the time and has since drifted:
--
--   asset               | old estimate | live mean (n runs, complete builds only) | max observed | ratio
--   ga_ayurdaya          |   4s         | 9.3s   (n=13)                            | 19.4s        | 2.33x
--   ga_dashas            | 564s         | 1117.7s (n=56)                           | 4199.3s      | 1.98x
--   ga_panchanga         |   3s         | 10.1s  (n=50)                            | 56.5s        | 3.37x
--   ga_sensitive         | 246s         | 407.3s (n=45)                            | 2109.5s      | 1.66x
--   ga_strength          |  97s         | 132.3s (n=49)                            | 1251.6s      | 1.36x
--   ga_vargas            |  94s         | 255.6s (n=48)                            | 3536.4s      | 2.72x
--   ga_tajaka            |  14s         | 19.2s  (n=52)                            | 53.7s        | 1.37x
--   ga_transit_anchors   |   1s         | 2.3s   (n=47)                            | 12.6s        | 2.30x
--   ga_vastu             |   1s         | 2.1s   (n=50)                            | 13.5s        | 2.10x
--   ga_yoga              |   7s         | 9.5s   (n=51)                            | 41.5s        | 1.36x
--
-- `ga_vargas` and `ga_dashas` are the two notable cases: migration 847's own comment
-- explicitly said both "were confirmed ACCURATE by F-A16 itself and are correctly left
-- untouched" at cycle 110 (94s/564s, matching the registry then) — this migration's live
-- re-query, ~77 cycles of additional build history later, finds both have genuinely DRIFTED
-- since (255.6s/1117.7s now), not that the cycle-110 finding was ever wrong. This is the same
-- lesson §N.4's floors-aspirational doctrine already teaches at the row-count level, now
-- confirmed at the estimate-freshness level too: a live measurement is only as fresh as the
-- moment it was taken, not a permanent fact once measured once.
--
-- The remaining assets not touched here (ga_ayurdaya's siblings `ga_condition`,
-- `ga_medical`, `ga_nakshatra`, `ga_positions`, `ga_prashna`, `ga_sade_sati`,
-- `ga_sensitive_degree`, `ga_structural`, `ga_vichara`) were re-checked live this same query
-- pass and all measure within 1.3x of their current registry value (several within 1%,
-- e.g. `ga_vichara` 307.1s measured vs 307s registry, `ga_sade_sati` 141.9s vs 142s) --
-- correctly left untouched; re-baselining a value that already matches would just be churn.
--
-- Per D-SERVICE (cost truth): this is a UX/scheduling estimate, not a correctness gate --
-- getting it right matters for W4 dispatch planning, not for any build-fatal assertion.

BEGIN;

UPDATE asset_registry SET estimated_seconds = 9    WHERE asset_id = 'ga_ayurdaya';
UPDATE asset_registry SET estimated_seconds = 1118 WHERE asset_id = 'ga_dashas';
UPDATE asset_registry SET estimated_seconds = 10   WHERE asset_id = 'ga_panchanga';
UPDATE asset_registry SET estimated_seconds = 407  WHERE asset_id = 'ga_sensitive';
UPDATE asset_registry SET estimated_seconds = 132  WHERE asset_id = 'ga_strength';
UPDATE asset_registry SET estimated_seconds = 256  WHERE asset_id = 'ga_vargas';
UPDATE asset_registry SET estimated_seconds = 19   WHERE asset_id = 'ga_tajaka';
UPDATE asset_registry SET estimated_seconds = 2    WHERE asset_id = 'ga_transit_anchors';
UPDATE asset_registry SET estimated_seconds = 2    WHERE asset_id = 'ga_vastu';
UPDATE asset_registry SET estimated_seconds = 10   WHERE asset_id = 'ga_yoga';

COMMIT;
