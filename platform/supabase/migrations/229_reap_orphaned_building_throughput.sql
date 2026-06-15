-- Migration 229: reap 4 orphaned 'building' asset_throughput records (L0 bg_ assets)
--
-- bg_concordance, bg_remedies, bg_text_index, bg_yogas were confirmed full
-- (rows present, error:null) by /api/cockpit/stats live diagnosis (2026-06-12).
-- Their build-run was interrupted before the orchestrator could flip state →
-- lit, leaving them stuck in 'building'. The display-layer fix (deriveState
-- count_sql-wins-over-building) resolves the bar immediately; this migration
-- corrects the underlying record so watchdog and future runs start clean.
--
-- Scoped to canonical chart only (482012f1-710e-4a25-994a-93821f5871aa).
-- The WHERE state = 'building' guard makes this idempotent.

UPDATE asset_throughput
SET
  state       = 'lit',
  last_built_at = COALESCE(last_built_at, NOW()),
  last_error  = NULL
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
  AND asset_id IN ('bg_concordance', 'bg_remedies', 'bg_text_index', 'bg_yogas')
  AND state = 'building';
