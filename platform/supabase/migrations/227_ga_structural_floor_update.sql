-- 227_ga_structural_floor_update.sql
-- =============================================================================
-- Update asset_registry.target_floor for ga_structural to reflect the
-- post-completeness-amendment canonical row count.
--
-- Context: The GA8 completeness amendment (branch feature/ga8-all30-vargas)
-- extended ga_structural_writer.py from 16 Shodasha to all 30 vargas and added
-- eight new relationship category families:
--
--   • Rahu/Ketu in all existing per-varga loops (dignity, aspects, conjunctions,
--     vargottama, dispositor chains) — ALL_GRAHAS replaces CLASSICAL_GRAHAS
--   • kala_sarpa_per_varga — Kala Sarpa / Kala Amrita detection (1 row per varga)
--   • lord_in_house_per_varga — house-lord matrix (12 rows per varga)
--   • lord_aspects_lord_per_varga — house-lord cross-aspects
--   • aspect_jaimini_per_varga — Jaimini rasi drishti (108 rows per varga)
--   • aspect_received_by_special_point — GA5 special point participants
--   • conjunction_special_point — special point conjunctions
--   • karaka_web_per_varga — Jaimini karaka inter-relationships
--   • graha_yuddha — graha war detection (winner/loser/orb)
--   • combustion_relationship / retrograde_aspect_modification
--
-- The count_sql already covers these via the '%_per_varga' LIKE clause
-- (added in migration 220 + PR #273). The floor was last set to 6,075 by
-- migration 220 and then to 53,953 during an intermediate build session.
--
-- New canonical count measured against prod on 2026-06-15 for the native chart
-- 482012f1-710e-4a25-994a-93821f5871aa after the full completeness build
-- (including the fix to build_ga_structural that added the missing combustion/
-- yuddha/special-point hooks — commit 81cd8436):
--
--     ga_structural   74,644   (per chart_id, via count_sql)
--
-- Note: combustion_relationship (0), retrograde_aspect_modification (0),
-- graha_yuddha (0), aspect_received_by_special_point (0),
-- conjunction_special_point (0), karaka_web_per_varga (0) are all zero for
-- the native chart for astronomically correct reasons (no combustion within
-- orbs, all planets direct, no same-sign pairs within 1°, GA5 data not yet
-- populated in this run). The floor reflects actual output, not a fabricated
-- ceiling.
--
-- Idempotent (UPDATE by asset_id). Reversible (DOWN block below).
-- Applied surgically via Cloud SQL Auth Proxy — never via deploy.yml.
-- =============================================================================

BEGIN;

UPDATE asset_registry
SET
    target_floor = 74644,
    volume_explanation = 'target_floor = 74,644 = achieved canonical count for chart 482012f1 (2026-06-15, post GA8-completeness amendment). Extends 16→30 vargas + 8 new relationship category families (kala_sarpa, lord_in_house, lord_aspects_lord, aspect_jaimini, karaka_web, graha_yuddha, combustion/retrograde). count_sql covers all via the fact_category LIKE ''%_per_varga'' clause.'
WHERE asset_id = 'ga_structural';

COMMIT;

-- =============================================================================
-- DOWN (manual rollback — restores the intermediate session value):
--
-- BEGIN;
-- UPDATE asset_registry SET target_floor = 53953
--   WHERE asset_id = 'ga_structural';
-- COMMIT;
-- =============================================================================
