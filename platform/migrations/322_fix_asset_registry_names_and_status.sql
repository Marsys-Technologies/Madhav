-- Migration 322: Fix asset_registry english_name drift and catalog_status for built L1 assets
-- Created: 2026-06-19
--
-- Root cause:
--   Migration 240 (ga_yoga) inserted english_name='Yoga Firings (ga_yoga)' — bracketed id suffix.
--   Migration 268 (ga_transit_anchors) inserted english_name='Transit Natal Anchors (ga_transit_anchors)'.
--   Migration 294 deferred ga_yoga + ga_prashna status fixes (Gate-3: tables existed but 0 rows at that time).
--   Both assets are now lit (ga_yoga: 5 rows; ga_prashna: activated PR #301) — Gate-3 cleared.
--
-- Seed (platform/scripts/seed/asset_registry_seed.ts) already carries clean values for all three rows.
-- This migration brings prod DB into parity with the seed.
--
-- DO NOT touch bo_*/ka_*/ph_*/mi_* DRAFT rows — those are legitimately unbuilt layers.
--
-- Rollback (down):
--   UPDATE asset_registry SET english_name = 'Yoga Firings (ga_yoga)' WHERE asset_id = 'ga_yoga';
--   UPDATE asset_registry SET english_name = 'Transit Natal Anchors (ga_transit_anchors)' WHERE asset_id = 'ga_transit_anchors';
--   UPDATE asset_registry SET catalog_status = 'DRAFT' WHERE asset_id IN ('ga_yoga', 'ga_prashna');

BEGIN;

-- FIX 1: Strip bracketed id suffix from english_name (seed-parity fix)
UPDATE asset_registry
SET english_name = 'Yoga Firings'
WHERE asset_id = 'ga_yoga'
  AND english_name = 'Yoga Firings (ga_yoga)';

UPDATE asset_registry
SET english_name = 'Transit Natal Anchors'
WHERE asset_id = 'ga_transit_anchors'
  AND english_name = 'Transit Natal Anchors (ga_transit_anchors)';

-- FIX 2: Promote mis-DRAFT'd built L1 assets to CURRENT
--   ga_yoga   : 5 rows in ga_yoga_firings (1 yoga × 5 ayanamshas, chart 482012f1) — Gate-3 cleared.
--   ga_prashna: activated PR #301; 0 natal rows is by-design (horary only) — CURRENT is correct.
UPDATE asset_registry
SET catalog_status = 'CURRENT'
WHERE asset_id IN ('ga_yoga', 'ga_prashna')
  AND catalog_status = 'DRAFT';

COMMIT;
