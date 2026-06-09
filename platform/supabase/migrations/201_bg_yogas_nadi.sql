-- Migration 201: bg_yogas target_floor update — Nadi expansion 2026-06-09
-- Before: 175 · After: 175 · Delta: +0
-- Note: writer ran idempotently — all 175 existing rows conflict-skipped.
-- Nadi texts (bhrigu_nandi_nadi, nadi_navamsa_patel) did not yield new yoga entries
-- beyond the existing 81 inline + 94 corpus-extracted set.

UPDATE asset_registry
SET
    target_floor = 175,
    volume_explanation = 'Rows in brahma_yoga_catalog: 81 inline core yogas + 94 corpus-verse extracted yoga definitions. Unchanged at 175 after Nadi expansion — all nadi yoga references already captured in the existing extracted set (ON CONFLICT DO NOTHING, 0 net new insertions).'
WHERE asset_id = 'bg_yogas';
