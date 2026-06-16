-- Migration 284: bg_vastu_directions + bg_vastu_direction_remedials (L0 Brahmagyan reference tables)
-- Astrovastu subsystem Gate-1: static classical Vastu direction–graha associations.
-- Idempotent: CREATE TABLE IF NOT EXISTS + INSERT ON CONFLICT DO NOTHING.
-- Sources: Vastu Shastra (Mayamata Ch.6), Brihat Samhita (classical tradition).

BEGIN;

-- ── Table: bg_vastu_directions ────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS bg_vastu_directions (
    id                  SERIAL PRIMARY KEY,
    direction           TEXT NOT NULL UNIQUE,
    direction_deg       INT,
    ruling_graha        TEXT NOT NULL,
    secondary_graha     TEXT,
    favorable_color     TEXT,
    element             TEXT,
    classical_citation  TEXT NOT NULL
);

-- Seed 8 classical Vastu directions (Mayamata Ch.6)
INSERT INTO bg_vastu_directions
    (direction, direction_deg, ruling_graha, secondary_graha, favorable_color, element, classical_citation)
VALUES
    ('North',     0,   'Mercury', NULL,    'Green',        'Water',  'Vastu Shastra (Mayamata Ch.6)'),
    ('South',     180, 'Mars',    NULL,    'Red',          'Fire',   'Vastu Shastra (Mayamata Ch.6)'),
    ('East',      90,  'Sun',     NULL,    'Orange/Gold',  'Fire',   'Vastu Shastra (Mayamata Ch.6)'),
    ('West',      270, 'Saturn',  NULL,    'Grey/Black',   'Air',    'Vastu Shastra (Mayamata Ch.6)'),
    ('Northeast', 45,  'Jupiter', NULL,    'Yellow',       'Ether',  'Vastu Shastra (Mayamata Ch.6)'),
    ('Southeast', 135, 'Venus',   NULL,    'White/Pink',   'Fire',   'Vastu Shastra (Mayamata Ch.6)'),
    ('Northwest', 315, 'Moon',    NULL,    'White/Silver', 'Air',    'Vastu Shastra (Mayamata Ch.6)'),
    ('Southwest', 225, 'Rahu',    NULL,    NULL,           'Earth',  'Vastu Shastra tradition (Nairitya corner)')
ON CONFLICT (direction) DO NOTHING;

-- ── Table: bg_vastu_direction_remedials ──────────────────────────────────────

CREATE TABLE IF NOT EXISTS bg_vastu_direction_remedials (
    id                  SERIAL PRIMARY KEY,
    direction           TEXT NOT NULL REFERENCES bg_vastu_directions(direction),
    remedy_type         TEXT NOT NULL,
    remedy_description  TEXT NOT NULL,
    classical_citation  TEXT NOT NULL
);

-- Seed 2–3 remedies per direction (~22 rows)
INSERT INTO bg_vastu_direction_remedials
    (direction, remedy_type, remedy_description, classical_citation)
VALUES
    -- North (Mercury/Water)
    ('North', 'color',   'Use green or blue tones in north-facing rooms to strengthen Mercury energy', 'Brihat Samhita Ch.53 (Vastu-vidya)'),
    ('North', 'symbol',  'Place a Kuber yantra or water feature in the north zone to activate prosperity', 'Vastu Shastra tradition'),
    ('North', 'material','Use light metals or glass in north walls to enhance Water element conductivity', 'Mayamata Ch.6'),

    -- South (Mars/Fire)
    ('South', 'color',   'Use red or earthy tones in south zone to honour Mars rulership and protect against loss', 'Brihat Samhita Ch.53'),
    ('South', 'symbol',  'Place a triangular Yantra or Mangal image in south to stabilise aggressive Mars energy', 'Vastu Shastra tradition'),
    ('South', 'space',   'Keep south zone heavier and closed; avoid large windows or open gates in this direction', 'Mayamata Ch.6'),

    -- East (Sun/Fire)
    ('East', 'space',   'Keep east zone open and well-lit; sunrise energy strengthens vitality and authority (Sun domain)', 'Mayamata Ch.6'),
    ('East', 'color',   'Use orange or golden hues in east-facing spaces to amplify solar Agni quality', 'Brihat Samhita Ch.53'),
    ('East', 'symbol',  'Place Surya image or copper vessel in east to invoke solar blessings', 'Vastu Shastra tradition'),

    -- West (Saturn/Air)
    ('West', 'color',   'Use grey, indigo, or black in west zone; Saturn governs discipline and karma here', 'Mayamata Ch.6'),
    ('West', 'symbol',  'Place iron objects or Shani yantra in west to balance Saturn energy constructively', 'Brihat Samhita Ch.53'),
    ('West', 'space',   'West zone may bear heavier structural loads; Saturn prefers weight and stability', 'Vastu Shastra tradition'),

    -- Northeast (Jupiter/Ether)
    ('Northeast', 'space',   'Keep northeast (Ishanya) zone clean, open, and free of heavy objects; Jupiter and Ether require lightness', 'Mayamata Ch.6'),
    ('Northeast', 'color',   'Use yellow or gold in northeast puja or meditation space to amplify Guru (Jupiter) grace', 'Brihat Samhita Ch.53'),
    ('Northeast', 'symbol',  'Install a puja room or sacred space in northeast; this is the divine corner per Vastu tradition', 'Vastu Shastra tradition'),

    -- Southeast (Venus/Fire)
    ('Southeast', 'function','Place kitchen (fire/Agni zone) in southeast; Venus and Fire element converge here', 'Mayamata Ch.6'),
    ('Southeast', 'color',   'Use white, pink, or cream tones in southeast to harmonise Venus energy and prevent conflicts', 'Brihat Samhita Ch.53'),
    ('Southeast', 'symbol',  'Place Shukra yantra or rose quartz in southeast to strengthen relationships and wealth', 'Vastu Shastra tradition'),

    -- Northwest (Moon/Air)
    ('Northwest', 'function','Northwest suits storage rooms, guest rooms, or granaries; Moon governs transitory stays', 'Mayamata Ch.6'),
    ('Northwest', 'color',   'Use white or silver tones in northwest to align with lunar energy and invite calm emotions', 'Brihat Samhita Ch.53'),
    ('Northwest', 'symbol',  'Place a silver bowl of water or Chandra yantra in northwest to stabilise Moon influence', 'Vastu Shastra tradition'),

    -- Southwest (Rahu/Earth)
    ('Southwest', 'space',   'Keep southwest (Nairitya) zone heavy, closed, and structurally solid; Rahu/Earth demands stability', 'Vastu Shastra tradition (Nairitya corner)'),
    ('Southwest', 'color',   'Use earthy tones — brown, terracotta — in southwest to ground Rahu energy and prevent instability', 'Brihat Samhita Ch.53'),
    ('Southwest', 'symbol',  'Avoid toilets or water bodies in southwest; place heavy furniture or master bedroom here to suppress negative Nairitya influence', 'Mayamata Ch.6')
ON CONFLICT DO NOTHING;

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   DROP TABLE IF EXISTS bg_vastu_direction_remedials;
--   DROP TABLE IF EXISTS bg_vastu_directions;
--   COMMIT;
-- =============================================================================
