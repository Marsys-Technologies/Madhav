-- 276_bg_medical_mappings.sql
-- =============================================================================
-- Medical/Ayurvedic Subsystem Gate-1 — bg_medical_mappings L0 table.
--
-- 9 grahas (Sun through Ketu) → Ayurvedic dosha, dhatu, organ systems,
-- body parts, and disease tendency per BPHS Ch.18, Ashtanga Hridayam,
-- Charaka Samhita.
--
-- L0 idempotency: ON CONFLICT (graha) DO UPDATE.
-- classical_citation is NOT NULL — hard requirement on every row (§N hard gate).
--
-- MEDICAL DISCLAIMER: This is a Jyotish reference table only.
-- ga_medical rows built from this reference carry indication_tier='jyotish_indication'
-- and not_diagnosis=TRUE — this is NOT a medical diagnostic system.
-- =============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS bg_medical_mappings (
    id                  SERIAL PRIMARY KEY,
    graha               TEXT NOT NULL UNIQUE,
    dosha               TEXT[],
    dhatu               TEXT[],
    organ_systems       TEXT[],
    body_part           TEXT[],
    disease_tendency    TEXT[],
    classical_citation  TEXT NOT NULL
);

INSERT INTO bg_medical_mappings
    (graha, dosha, dhatu, organ_systems, body_part, disease_tendency, classical_citation)
VALUES
    ('Sun',
     ARRAY['pitta'],
     ARRAY['asthi'],
     ARRAY['heart','eyes'],
     ARRAY['right_eye','spine','heart'],
     ARRAY['heart_disease','eye_problems','bone_disorders'],
     'BPHS Ch.18 / Ashtanga Hridayam'),

    ('Moon',
     ARRAY['kapha','vata'],
     ARRAY['rasa'],
     ARRAY['mind','lungs','stomach'],
     ARRAY['left_eye','breast','uterus'],
     ARRAY['mental_disorders','respiratory','digestive'],
     'BPHS Ch.18 / Charaka Samhita'),

    ('Mars',
     ARRAY['pitta'],
     ARRAY['rakta','mamsa'],
     ARRAY['marrow','red_blood_cells'],
     ARRAY['right_ear','bile','genitals'],
     ARRAY['blood_disorders','inflammation','accidents'],
     'BPHS Ch.18 / Ashtanga Hridayam'),

    ('Mercury',
     ARRAY['tridosha'],
     ARRAY['skin','nervous_tissue'],
     ARRAY['nervous_system','skin'],
     ARRAY['tongue','hands','arms'],
     ARRAY['nervous_disorders','skin_diseases','speech_disorders'],
     'BPHS Ch.18 / Charaka Samhita'),

    ('Jupiter',
     ARRAY['kapha'],
     ARRAY['meda','majja'],
     ARRAY['liver','pancreas'],
     ARRAY['thighs','liver','ears'],
     ARRAY['obesity','liver_disorders','diabetes'],
     'BPHS Ch.18 / Ashtanga Hridayam'),

    ('Venus',
     ARRAY['kapha','vata'],
     ARRAY['shukra','rasa'],
     ARRAY['reproductive','kidneys'],
     ARRAY['face','neck','genitals'],
     ARRAY['reproductive_disorders','venereal','kidney_stones'],
     'BPHS Ch.18 / Charaka Samhita'),

    ('Saturn',
     ARRAY['vata'],
     ARRAY['asthi','nervous'],
     ARRAY['large_intestine','spleen'],
     ARRAY['teeth','bones','joints','legs'],
     ARRAY['chronic_diseases','arthritis','paralysis','vayu_disorders'],
     'BPHS Ch.18 / Ashtanga Hridayam'),

    ('Rahu',
     ARRAY['vata'],
     ARRAY['skin'],
     ARRAY['nervous_system'],
     ARRAY['skin','limbs'],
     ARRAY['mysterious_diseases','cancer_indications','poisons','skin'],
     'BPHS Ch.18 (Rahu disease indications)'),

    ('Ketu',
     ARRAY['pitta','vata'],
     ARRAY['marrow'],
     ARRAY['intestines'],
     ARRAY['abdomen','anus'],
     ARRAY['intestinal_worms','abdominal_disorders','moksha_related'],
     'BPHS Ch.18 (Ketu disease indications)')

ON CONFLICT (graha) DO UPDATE SET
    dosha              = EXCLUDED.dosha,
    dhatu              = EXCLUDED.dhatu,
    organ_systems      = EXCLUDED.organ_systems,
    body_part          = EXCLUDED.body_part,
    disease_tendency   = EXCLUDED.disease_tendency,
    classical_citation = EXCLUDED.classical_citation;

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   DROP TABLE IF EXISTS bg_medical_mappings;
--   COMMIT;
-- =============================================================================
