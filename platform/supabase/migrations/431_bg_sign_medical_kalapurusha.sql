-- Migration 431: bg_sign_medical — Kalapurusha sign→body-part reference (WP-2.5 / LCA-16)
-- =============================================================================
-- Context: REMEDIATION_PLAN_v2_0 §5 WP-2.5 / LCA-16 organ-taxonomy gap. Disease-domain
-- questions require a doctrinal sign→body-part map (the Kalapurusha / Cosmic Man) ALONGSIDE
-- the existing graha→organ map (bg_medical_mappings, mig 276) and nakshatra→body-part map
-- (bg_nakshatra_medical, mig 277). Without it no disease question can be answered
-- doctrinally from the rasi axis.
--
-- Source (B.10 — cited classical data, no LLM invention): BPHS Ch.4 Kalapurusha zodiacal
-- body-map (Aries=head … Pisces=feet); element→dosha correspondence from Ashtanga Hridayam
-- (fire→pitta, earth→kapha/vata, air→vata, water→kapha). classical_citation NOT NULL on
-- every row (§N hard gate).
--
-- Seeded inline here for presence-at-migration; the L0 writer bg_medical_mappings
-- (brahmagyan.l0_medical.seed_medical_mappings → SIGN_MEDICAL) re-upserts the identical
-- 12 rows at build via ON CONFLICT DO UPDATE (§N.3 L0 idempotency) so the code seed is the
-- durable source and this table stays in lockstep.
--
-- MEDICAL DISCLAIMER: Jyotish reference table only — NOT a medical diagnostic system.
-- =============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS bg_sign_medical (
    sign_number         INTEGER PRIMARY KEY CHECK (sign_number BETWEEN 1 AND 12),
    sign_name           TEXT    NOT NULL UNIQUE,
    body_part           TEXT    NOT NULL,
    organ_systems       TEXT[],
    element             TEXT    NOT NULL CHECK (element IN ('fire','earth','air','water')),
    dosha               TEXT    NOT NULL,
    classical_citation  TEXT    NOT NULL
);

COMMENT ON TABLE bg_sign_medical IS
  'WP-2.5/LCA-16: Kalapurusha (Cosmic Man) sign→body-part reference map. BPHS Ch.4 body-map '
  '+ Ashtanga Hridayam element→dosha. Third axis of the medical taxonomy alongside '
  'bg_medical_mappings (graha→organ) and bg_nakshatra_medical (nakshatra→body-part). '
  'Re-seeded by brahmagyan.l0_medical.SIGN_MEDICAL. Jyotish reference only, not diagnosis.';

INSERT INTO bg_sign_medical
    (sign_number, sign_name, body_part, organ_systems, element, dosha, classical_citation)
VALUES
    (1,  'Aries',       'head/brain/skull',            ARRAY['brain','skull'],                 'fire',  'pitta', 'BPHS Ch.4 Kalapurusha / Ashtanga Hridayam element→dosha'),
    (2,  'Taurus',      'face/neck/throat',            ARRAY['face','throat','thyroid'],       'earth', 'kapha', 'BPHS Ch.4 Kalapurusha / Ashtanga Hridayam element→dosha'),
    (3,  'Gemini',      'shoulders/arms/hands/lungs',  ARRAY['arms','shoulders','lungs'],      'air',   'vata',  'BPHS Ch.4 Kalapurusha / Ashtanga Hridayam element→dosha'),
    (4,  'Cancer',      'chest/breast/lungs/heart',    ARRAY['chest','breast','lungs'],        'water', 'kapha', 'BPHS Ch.4 Kalapurusha / Ashtanga Hridayam element→dosha'),
    (5,  'Leo',         'stomach/upper-abdomen/heart', ARRAY['heart','stomach','spine'],       'fire',  'pitta', 'BPHS Ch.4 Kalapurusha / Ashtanga Hridayam element→dosha'),
    (6,  'Virgo',       'abdomen/intestines/waist',    ARRAY['intestines','abdomen'],          'earth', 'vata',  'BPHS Ch.4 Kalapurusha / Ashtanga Hridayam element→dosha'),
    (7,  'Libra',       'lower-abdomen/pelvis/kidneys',ARRAY['kidneys','pelvis','bladder'],    'air',   'vata',  'BPHS Ch.4 Kalapurusha / Ashtanga Hridayam element→dosha'),
    (8,  'Scorpio',     'genitals/excretory-organs',   ARRAY['genitals','excretory','rectum'], 'water', 'kapha', 'BPHS Ch.4 Kalapurusha / Ashtanga Hridayam element→dosha'),
    (9,  'Sagittarius', 'hips/thighs',                 ARRAY['hips','thighs','liver'],         'fire',  'pitta', 'BPHS Ch.4 Kalapurusha / Ashtanga Hridayam element→dosha'),
    (10, 'Capricorn',   'knees/joints',                ARRAY['knees','joints','bones'],        'earth', 'vata',  'BPHS Ch.4 Kalapurusha / Ashtanga Hridayam element→dosha'),
    (11, 'Aquarius',    'calves/ankles/circulation',   ARRAY['calves','ankles','circulation'], 'air',   'vata',  'BPHS Ch.4 Kalapurusha / Ashtanga Hridayam element→dosha'),
    (12, 'Pisces',      'feet',                        ARRAY['feet','lymphatic'],              'water', 'kapha', 'BPHS Ch.4 Kalapurusha / Ashtanga Hridayam element→dosha')
ON CONFLICT (sign_number) DO UPDATE SET
    sign_name          = EXCLUDED.sign_name,
    body_part          = EXCLUDED.body_part,
    organ_systems      = EXCLUDED.organ_systems,
    element            = EXCLUDED.element,
    dosha              = EXCLUDED.dosha,
    classical_citation = EXCLUDED.classical_citation;

-- asset_registry sub-registration (shares the bg_medical_mappings writer, like
-- bg_nakshatra_medical — see pipeline/orchestrator/writers/bg_medical_mappings.py).
INSERT INTO asset_registry (
    asset_id, layer, sort_order,
    sanskrit_name, english_name, english_description,
    storage_type, target_table, count_sql, size_sql,
    target_floor, scope, is_active, has_writer,
    layer_name, layer_index, catalog_status
) VALUES (
    'bg_sign_medical', 'brahmagyan', 0,
    'Kālapuruṣa Aṅga', 'Kalapurusha Sign→Body-Part Map',
    'Kalapurusha (Cosmic Man) zodiacal body-map: 12 signs → body-part / organ-systems / '
    'element / dosha (BPHS Ch.4 + Ashtanga Hridayam). Seeded by the bg_medical_mappings writer.',
    'postgres_table', 'bg_sign_medical',
    'SELECT COUNT(*) FROM bg_sign_medical', NULL,
    12, 'global', true, true,
    'Brahmagyan', 0, 'CURRENT'
) ON CONFLICT (asset_id) DO UPDATE SET
    count_sql    = EXCLUDED.count_sql,
    target_table = EXCLUDED.target_table,
    has_writer   = EXCLUDED.has_writer,
    english_description = EXCLUDED.english_description;

-- Invariant: exactly 12 rows, each with a non-empty citation.
DO $$
DECLARE n INTEGER; uncited INTEGER;
BEGIN
    SELECT count(*) INTO n FROM bg_sign_medical;
    SELECT count(*) INTO uncited FROM bg_sign_medical
        WHERE classical_citation IS NULL OR classical_citation = '';
    IF n <> 12 OR uncited <> 0 THEN
        RAISE EXCEPTION 'bg_sign_medical invariant violated: rows=% (expected 12), uncited=% (expected 0)', n, uncited;
    END IF;
END $$;

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   DELETE FROM asset_registry WHERE asset_id = 'bg_sign_medical';
--   DROP TABLE IF EXISTS bg_sign_medical;
--   COMMIT;
-- =============================================================================
