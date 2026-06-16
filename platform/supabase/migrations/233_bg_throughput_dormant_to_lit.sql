-- 233_bg_throughput_dormant_to_lit.sql
-- =============================================================================
-- Follow-up to migration 229. Migration 229 targeted state='building' but the
-- 4 bg_ data assets in prod (bg_concordance, bg_remedies, bg_text_index,
-- bg_yogas) were found in state='dormant' (or absent entirely) rather than
-- 'building'. The root cause is the same: their build-run was logged in
-- asset_throughput before the orchestrator could flip to 'lit'.
--
-- Actual row counts confirmed against prod (2026-06-16):
--   bg_concordance   720   (no throughput record; INSERT needed)
--   bg_remedies      266   (throughput state='dormant'; UPDATE needed)
--   bg_text_index    361   (throughput state='dormant'; UPDATE needed)
--   bg_yogas         175   (throughput state='dormant'; UPDATE needed)
--
-- This migration:
--   1. Updates the 3 dormant records → 'lit'.
--   2. Inserts a 'lit' record for bg_concordance which had no throughput row.
-- After this, build_state_stale will be false for all 4 assets and the
-- "build-state stale" badge will no longer fire.
--
-- Idempotent: UPDATE/INSERT have natural guards; re-running sets same values.
-- Scoped to canonical chart_id only.
-- =============================================================================

BEGIN;

-- 1. Promote dormant → lit for assets that have confirmed row data.
UPDATE asset_throughput
SET
  state         = 'lit',
  last_built_at = COALESCE(last_built_at, NOW()),
  last_error    = NULL
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
  AND asset_id IN ('bg_remedies', 'bg_text_index', 'bg_yogas')
  AND state = 'dormant';

-- 2. Insert a lit record for bg_concordance which has no throughput row.
INSERT INTO asset_throughput (chart_id, asset_id, state, last_built_at, last_error)
VALUES (
  '482012f1-710e-4a25-994a-93821f5871aa',
  'bg_concordance',
  'lit',
  NOW(),
  NULL
)
ON CONFLICT (chart_id, asset_id) WHERE chart_id IS NOT NULL DO UPDATE
  SET state = 'lit',
      last_error = NULL;

COMMIT;

-- =============================================================================
-- DOWN (manual rollback — restores prior dormant state):
--
-- BEGIN;
-- UPDATE asset_throughput
-- SET state = 'dormant', last_built_at = NULL
-- WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
--   AND asset_id IN ('bg_remedies', 'bg_text_index', 'bg_yogas');
-- DELETE FROM asset_throughput
-- WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
--   AND asset_id = 'bg_concordance';
-- COMMIT;
-- =============================================================================
