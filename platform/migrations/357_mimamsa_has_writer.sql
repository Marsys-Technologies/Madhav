-- Migration 357: mark all 10 L5 Mīmāṃsā data writers as has_writer=true
--
-- Follows the same pattern as 343_ka_tulana_has_writer.sql.
-- Services (mi_seva, mi_abhilekha) are intentionally excluded — they have
-- no build-time writer and must NOT appear in click-Build plans.
--
-- Without this, the plan route (WHERE has_writer = true) returns 0 L5 assets
-- and clicking Build for the mimamsa layer is a silent no-op.

UPDATE asset_registry
  SET has_writer = true
  WHERE asset_id IN (
    'mi_jivanaghatana',
    'mi_kula',
    'mi_bhavisya',
    'mi_pramana',
    'mi_gunanaka',
    'mi_adhilepa',
    'mi_pariksha',
    'mi_sambandha',
    'mi_darshana',
    'mi_vistara'
  );
