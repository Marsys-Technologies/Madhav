-- Migration 206: roman-IAST service asset names
-- The two L0 Brahmagyan service rows (bg_panchanga, bg_ephemeris_engine) were
-- registered in migration 203 with Devanagari sanskrit_name values while every
-- sibling asset uses roman IAST (Graha-sphuṭa, Sāraṇi, Śāstrapāṭha, Gaṇita-yantra…).
-- This normalizes the two services to roman IAST consistent with the house style.
-- ga_pyjhora_engine (migration 205) already uses roman IAST ('Gaṇita-yantra') — no change.
-- Idempotent (matches on asset_id). Reversible down-block restores prior Devanagari.
-- Per: CLAUDECODE_BRIEF_COCKPIT_POLISH_R2_v1_0.md §2

BEGIN;

-- bg_panchanga: 'पञ्चाङ्ग गणना' → 'Pañcāṅga Gaṇanā'
UPDATE asset_registry
SET sanskrit_name = 'Pañcāṅga Gaṇanā'
WHERE asset_id = 'bg_panchanga';

-- bg_ephemeris_engine: 'दृक् एफिमेरिस' → 'Dṛk Sāraṇi'
-- (fully-Sanskrit second word, matching the bg_ephemeris / Graha-sphuṭa convention
--  of roman-Sanskrit table names rather than transliterating the English "ephemeris".)
UPDATE asset_registry
SET sanskrit_name = 'Dṛk Sāraṇi'
WHERE asset_id = 'bg_ephemeris_engine';

COMMIT;

-- ── DOWN ────────────────────────────────────────────────────────────────────
-- BEGIN;
-- UPDATE asset_registry SET sanskrit_name = 'पञ्चाङ्ग गणना' WHERE asset_id = 'bg_panchanga';
-- UPDATE asset_registry SET sanskrit_name = 'दृक् एफिमेरिस' WHERE asset_id = 'bg_ephemeris_engine';
-- COMMIT;
