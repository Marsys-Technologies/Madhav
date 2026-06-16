-- 231_bg_target_floor_fix.sql
-- =============================================================================
-- Reset asset_registry.target_floor for 4 L0 Brahmagyan (bg_*) assets to their
-- achieved row counts, correcting aspirational floors that were set above the
-- actual corpus size and caused deriveState to render these assets as 'building'
-- despite having full data.
--
-- Root cause: deriveState() was gating 'lit' on actualRows >= target_floor
-- (violating §N.4 "floors are aspirational, NOT gates"). That gate is removed in
-- the accompanying Fix A (route.ts). This migration is the complementary data
-- hygiene fix: aligning target_floor with actual corpus size so the progress bar
-- denominator and "N / N" overlay reflect reality.
--
-- Affected assets and their actual row counts (measured against prod via
-- count_sql with Cloud SQL Auth Proxy, 2026-06-16):
--
--   bg_concordance   720   (previously had floor > 720 → stuck 'building')
--   bg_remedies      266   (previously had floor > 266 → stuck 'building')
--   bg_text_index    361   (previously had floor > 361 → stuck 'building')
--   bg_yogas         175   (previously had floor > 175 → stuck 'building')
--
-- Per §N.4: target_floor = achieved count after build. Never fabricate rows to
-- hit a floor; never use a floor as a gate. After this migration all four assets
-- have target_floor = actual corpus size, so the progress bar shows 100%
-- (actualRows / target_floor = 1.0) and deriveState returns 'lit'.
--
-- Idempotent (UPDATE by asset_id; re-running sets the same values).
-- Reversible (DOWN block below restores previous aspirational values — note:
-- the previous values are not known precisely; NULL is used as a safe fallback
-- since NULL target_floor causes the bar to show raw row count with no "/" target,
-- which is better than a floor that falsely gates 'lit').
-- Applied surgically via Cloud SQL Auth Proxy — never via deploy.yml.
-- =============================================================================

BEGIN;

UPDATE asset_registry SET target_floor = 720  WHERE asset_id = 'bg_concordance';
UPDATE asset_registry SET target_floor = 266  WHERE asset_id = 'bg_remedies';
UPDATE asset_registry SET target_floor = 361  WHERE asset_id = 'bg_text_index';
UPDATE asset_registry SET target_floor = 175  WHERE asset_id = 'bg_yogas';

COMMIT;

-- =============================================================================
-- DOWN (manual rollback — clears the floors; bars revert to raw-count display):
--
-- BEGIN;
-- UPDATE asset_registry SET target_floor = NULL
--   WHERE asset_id IN ('bg_concordance', 'bg_remedies', 'bg_text_index', 'bg_yogas');
-- COMMIT;
-- =============================================================================
