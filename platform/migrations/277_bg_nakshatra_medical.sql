-- 277_bg_nakshatra_medical.sql
-- =============================================================================
-- Medical/Ayurvedic Subsystem Gate-1 — bg_nakshatra_medical L0 table.
--
-- 27 nakshatras → body-part correspondences.
-- Used by ga_medical writer for Moon nakshatra body-part lookup.
-- Source: Ashtanga Hridayam / BPHS.
--
-- FORENSIC: Nakshatra #25 = Purva Bhadrapada → body_part = 'left_side'
-- (native Moon nakshatra per FORENSIC anchor: Moon = Purva Bhadrapada).
--
-- L0 idempotency: ON CONFLICT (nakshatra_name) DO UPDATE.
-- =============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS bg_nakshatra_medical (
    id                  SERIAL PRIMARY KEY,
    nakshatra_name      TEXT NOT NULL UNIQUE,
    nakshatra_number    INT,
    body_part           TEXT NOT NULL,
    classical_citation  TEXT NOT NULL
);

INSERT INTO bg_nakshatra_medical
    (nakshatra_name, nakshatra_number, body_part, classical_citation)
VALUES
    ('Ashwini',            1,  'feet/knees',       'Ashtanga Hridayam / BPHS'),
    ('Bharani',            2,  'head',             'Ashtanga Hridayam / BPHS'),
    ('Krittika',           3,  'eyes/face',        'Ashtanga Hridayam / BPHS'),
    ('Rohini',             4,  'forehead/neck',    'Ashtanga Hridayam / BPHS'),
    ('Mrigashira',         5,  'eyes/eyebrows',    'Ashtanga Hridayam / BPHS'),
    ('Ardra',              6,  'eyes/mind',        'Ashtanga Hridayam / BPHS'),
    ('Punarvasu',          7,  'ears/chest',       'Ashtanga Hridayam / BPHS'),
    ('Pushya',             8,  'face/mouth',       'Ashtanga Hridayam / BPHS'),
    ('Ashlesha',           9,  'ears/skin',        'Ashtanga Hridayam / BPHS'),
    ('Magha',              10, 'nose',             'Ashtanga Hridayam / BPHS'),
    ('Purva Phalguni',     11, 'right_hand',       'Ashtanga Hridayam / BPHS'),
    ('Uttara Phalguni',    12, 'right_side',       'Ashtanga Hridayam / BPHS'),
    ('Hasta',              13, 'fingers/hands',    'Ashtanga Hridayam / BPHS'),
    ('Chitra',             14, 'forehead',         'Ashtanga Hridayam / BPHS'),
    ('Swati',              15, 'chest',            'Ashtanga Hridayam / BPHS'),
    ('Vishakha',           16, 'arms',             'Ashtanga Hridayam / BPHS'),
    ('Anuradha',           17, 'abdomen',          'Ashtanga Hridayam / BPHS'),
    ('Jyeshtha',           18, 'right_side_body',  'Ashtanga Hridayam / BPHS'),
    ('Mula',               19, 'feet/hips',        'Ashtanga Hridayam / BPHS'),
    ('Purva Ashadha',      20, 'thighs',           'Ashtanga Hridayam / BPHS'),
    ('Uttara Ashadha',     21, 'thighs/knees',     'Ashtanga Hridayam / BPHS'),
    ('Shravana',           22, 'ears',             'Ashtanga Hridayam / BPHS'),
    ('Dhanishtha',         23, 'back/knees',       'Ashtanga Hridayam / BPHS'),
    ('Shatabhisha',        24, 'right_thigh',      'Ashtanga Hridayam / BPHS'),
    ('Purva Bhadrapada',   25, 'left_side',        'Ashtanga Hridayam / BPHS'),
    ('Uttara Bhadrapada',  26, 'feet',             'Ashtanga Hridayam / BPHS'),
    ('Revati',             27, 'feet/abdomen',     'Ashtanga Hridayam / BPHS')

ON CONFLICT (nakshatra_name) DO UPDATE SET
    nakshatra_number   = EXCLUDED.nakshatra_number,
    body_part          = EXCLUDED.body_part,
    classical_citation = EXCLUDED.classical_citation;

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   DROP TABLE IF EXISTS bg_nakshatra_medical;
--   COMMIT;
-- =============================================================================
