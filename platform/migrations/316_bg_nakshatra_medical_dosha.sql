-- 316_bg_nakshatra_medical_dosha.sql
-- =============================================================================
-- Adds `dosha` column to bg_nakshatra_medical for Tier 2 nakshatra × dosha
-- grid (27 nakshatras × 3-dosha classification).
--
-- Source authority: Ashtanga Hridayam (Vagbhata) / Hora Sara (Prithuyasas) /
--   BPHS Ch.3 — classical Jyotisha-Ayurveda nakshatra–dosha correspondences.
--
-- The column is nullable at migration time; seed data (l0_medical.py Tier 2)
-- populates it immediately via the bg_medical_mappings writer ON CONFLICT DO
-- UPDATE. After the first build run all 27 rows will have a non-null dosha.
--
-- L0 idempotency: ADD COLUMN IF NOT EXISTS — safe to run repeatedly.
-- =============================================================================

BEGIN;

ALTER TABLE bg_nakshatra_medical
    ADD COLUMN IF NOT EXISTS dosha TEXT;

COMMENT ON COLUMN bg_nakshatra_medical.dosha IS
    'Primary ruling dosha per classical Jyotisha-Ayurveda '
    '(vata / pitta / kapha). '
    'Source: Ashtanga Hridayam / Hora Sara / BPHS Ch.3. '
    'Populated by bg_medical_mappings writer (l0_medical.py Tier 2).';

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   ALTER TABLE bg_nakshatra_medical DROP COLUMN IF EXISTS dosha;
--   COMMIT;
-- =============================================================================
