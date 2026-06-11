-- 220_ga_target_floors.sql
-- =============================================================================
-- Set asset_registry.target_floor for the eight active Gaṇita (L1) assets so the
-- cockpit progress bars fill. Until now target_floor was NULL for every ga_*
-- asset, and the cockpit AssetProgressBar computes:
--
--     pct = (actualRows !== null && targetVolume > 0)
--             ? min(100, round(actualRows / targetVolume * 100)) : 0
--     numericText = (actualRows !== null && targetVolume)
--             ? `${actualRows} / ${targetVolume}` : `${actualRows}`
--
-- With a NULL target_floor the denominator is missing → pct falls to 0 → the bar
-- renders empty (0% fill) even though the asset is fully built, and the numeric
-- overlay shows only the row count with no "/ N" target. Setting target_floor to
-- the achieved canonical count makes a fully-built asset read 100% with
-- "N / N" text.
--
-- Floors = achieved canonical count, NOT an aspirational ceiling and NOT a gate.
-- Per the ratified principle: never fabricate a target, never let a floor block a
-- build. These values are the live per-chart canonical counts measured against
-- prod on 2026-06-11 for the native chart 482012f1-710e-4a25-994a-93821f5871aa
-- (canonical L1 build), by running each asset's own registered count_sql:
--
--     ga_positions      50
--     ga_vargas         21,635
--     ga_dashas         536,471
--     ga_strength       2,184
--     ga_sensitive      8,055
--     ga_panchanga      221
--     ga_sade_sati      11,019
--     ga_structural     6,075
--
-- ga_tajaka (is_active=false, no writer output) and ga_pyjhora_engine
-- (asset_type=service, no count_sql) are intentionally left NULL.
--
-- Step 5 (this migration): three of the legacy expected_volume_formula strings
-- under-described the real volume by an order of magnitude or more because they
-- predate later design changes. Their volume_explanation is updated to record the
-- real basis (target_floor = achieved canonical count). The expected_volume_formula
-- field is documentation only (cockpit registry page); it is not computed against,
-- so the bar math is unaffected by these annotations.
--
--   ga_dashas    — legacy formula (9+81+729)*AYANAMSHAS ≈ 4,095 predates the
--                  4-level Sukshma + KP-sublevel dasha tree (real 536,471).
--   ga_panchanga — legacy "one row per ayanamsha" predates the enriched natal
--                  panchanga fact family (real 221).
--   ga_sade_sati — legacy "one row per ayanamsha" predates the full cycle /
--                  phase-quarter / dhaiya / shani-period fact family (real 11,019).
--
-- Idempotent (UPDATE by asset_id; re-running sets the same values). Reversible
-- (DOWN block sets target_floor back to NULL). Applied surgically via the Cloud
-- SQL Auth Proxy — never via deploy.yml or the bulk seed runner.
-- =============================================================================

BEGIN;

-- ── target_floor = achieved canonical count (chart 482012f1, 2026-06-11) ──────
UPDATE asset_registry SET target_floor = 50     WHERE asset_id = 'ga_positions';
UPDATE asset_registry SET target_floor = 21635  WHERE asset_id = 'ga_vargas';
UPDATE asset_registry SET target_floor = 536471 WHERE asset_id = 'ga_dashas';
UPDATE asset_registry SET target_floor = 2184   WHERE asset_id = 'ga_strength';
UPDATE asset_registry SET target_floor = 8055   WHERE asset_id = 'ga_sensitive';
UPDATE asset_registry SET target_floor = 221    WHERE asset_id = 'ga_panchanga';
UPDATE asset_registry SET target_floor = 11019  WHERE asset_id = 'ga_sade_sati';
UPDATE asset_registry SET target_floor = 6075   WHERE asset_id = 'ga_structural';

-- ── Step 5: correct the three legacy volume_explanations that contradict the
--    real count by ≥ an order of magnitude. target_floor is now the source of
--    truth for the bar; these strings document the achieved-count basis. ───────
UPDATE asset_registry
SET volume_explanation = 'target_floor = 536,471 = achieved canonical count for chart 482012f1 (2026-06-11). The legacy formula (9+81+729)*AYANAMSHAS ≈ 4,095 predates the 4-level Sukshma + KP-sublevel Vimshottari tree and under-counts by ~130×.'
WHERE asset_id = 'ga_dashas';

UPDATE asset_registry
SET volume_explanation = 'target_floor = 221 = achieved canonical count for chart 482012f1 (2026-06-11). The legacy "one panchanga row per ayanamsha" formula predates the enriched natal panchanga fact family (panchanga_* categories in chart_facts).'
WHERE asset_id = 'ga_panchanga';

UPDATE asset_registry
SET volume_explanation = 'target_floor = 11,019 = achieved canonical count for chart 482012f1 (2026-06-11). The legacy "one row per ayanamsha" formula predates the full Sade Sati fact family (cycle / phase / phase_quarter / dhaiya / kantaka / ashtama / janma-shani periods + overlays).'
WHERE asset_id = 'ga_sade_sati';

COMMIT;

-- =============================================================================
-- DOWN (manual rollback — clears the floors set above; the volume_explanation
-- text changes are documentation-only and may be left in place):
--
-- BEGIN;
-- UPDATE asset_registry SET target_floor = NULL
--   WHERE asset_id IN (
--     'ga_positions', 'ga_vargas', 'ga_dashas', 'ga_strength',
--     'ga_sensitive', 'ga_panchanga', 'ga_sade_sati', 'ga_structural'
--   );
-- COMMIT;
-- =============================================================================
