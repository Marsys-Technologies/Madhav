-- Migration 250: L0 Brahmagyan dignity + condition reference tables
-- Creates and seeds 5 reference tables for the ga_condition writer:
--   bg_dignity_reference        — exaltation/debilitation/moolatrikona/own_signs per graha
--   bg_graha_naisargika_friendship — natural friendship per graha pair
--   bg_avastha_schemes          — 5 avastha classification schemes with determination rules
--   bg_motion_state_thresholds  — motion state definitions per graha
--   bg_combustion_orbs          — combustion + deep-combustion orbs per graha
--
-- Source citations:
--   BPHS = Brihat Parashara Hora Shastra
--   JP = Jataka Parijata
--   PD = Phala Deepika
--   UK = Uttara Kalamrita
--   SS = Surya Siddhanta / Saravali
--
-- Idempotency: ON CONFLICT DO NOTHING / ON CONFLICT DO UPDATE (L0 pattern per §N.3)

BEGIN;

-- ─── 1. bg_dignity_reference ─────────────────────────────────────────────────
-- Stores the classical positional dignity thresholds per graha.
-- exaltation_sign / debilitation_sign / moolatrikona_sign and degree ranges,
-- own_signs as text[].

CREATE TABLE IF NOT EXISTS bg_dignity_reference (
    id                  SERIAL PRIMARY KEY,
    graha               TEXT NOT NULL UNIQUE,   -- e.g. 'Sun', 'Moon', 'Mars' …
    exaltation_sign     TEXT,
    exaltation_degree   NUMERIC,                -- exact exaltation degree within sign
    debilitation_sign   TEXT,
    debilitation_degree NUMERIC,                -- exact debilitation degree within sign
    moolatrikona_sign   TEXT,
    moolatrikona_from   NUMERIC,                -- start degree (0-based within sign)
    moolatrikona_to     NUMERIC,                -- end degree (exclusive)
    own_signs           TEXT[],                 -- signs the graha owns
    classical_citation  TEXT,
    notes               TEXT
);

INSERT INTO bg_dignity_reference
    (graha, exaltation_sign, exaltation_degree, debilitation_sign, debilitation_degree,
     moolatrikona_sign, moolatrikona_from, moolatrikona_to, own_signs, classical_citation, notes)
VALUES
    ('Sun',
     'Aries',       10,
     'Libra',       10,
     'Leo',          0, 20,
     ARRAY['Leo'],
     'BPHS Ch.3',
     NULL),

    ('Moon',
     'Taurus',       3,
     'Scorpio',       3,
     'Taurus',        4, 30,
     ARRAY['Cancer'],
     'BPHS Ch.3',
     NULL),

    ('Mars',
     'Capricorn',   28,
     'Cancer',      28,
     'Aries',        0, 12,
     ARRAY['Aries','Scorpio'],
     'BPHS Ch.3',
     NULL),

    ('Mercury',
     'Virgo',       15,
     'Pisces',      15,
     'Virgo',       16, 20,
     ARRAY['Gemini','Virgo'],
     'BPHS Ch.3',
     NULL),

    ('Jupiter',
     'Cancer',       5,
     'Capricorn',    5,
     'Sagittarius',  0, 10,
     ARRAY['Sagittarius','Pisces'],
     'BPHS Ch.3',
     NULL),

    ('Venus',
     'Pisces',      27,
     'Virgo',       27,
     'Libra',        0, 15,
     ARRAY['Taurus','Libra'],
     'BPHS Ch.3',
     NULL),

    ('Saturn',
     'Libra',       20,
     'Aries',       20,
     'Aquarius',     0, 20,
     ARRAY['Capricorn','Aquarius'],
     'BPHS Ch.3',
     NULL),

    ('Rahu',
     'Gemini',      NULL,
     'Sagittarius', NULL,
     NULL,          NULL, NULL,
     ARRAY[]::TEXT[],
     'BPHS Ch.3; tradition varies between Gemini/Taurus exaltation',
     'Some authorities place Rahu exaltation in Taurus; Gemini followed here per Parashara majority'),

    ('Ketu',
     'Sagittarius', NULL,
     'Gemini',      NULL,
     NULL,          NULL, NULL,
     ARRAY[]::TEXT[],
     'BPHS Ch.3; tradition varies',
     'Some authorities place Ketu exaltation in Scorpio; Sagittarius followed as reverse of Rahu')
ON CONFLICT (graha) DO UPDATE SET
    exaltation_sign     = EXCLUDED.exaltation_sign,
    exaltation_degree   = EXCLUDED.exaltation_degree,
    debilitation_sign   = EXCLUDED.debilitation_sign,
    debilitation_degree = EXCLUDED.debilitation_degree,
    moolatrikona_sign   = EXCLUDED.moolatrikona_sign,
    moolatrikona_from   = EXCLUDED.moolatrikona_from,
    moolatrikona_to     = EXCLUDED.moolatrikona_to,
    own_signs           = EXCLUDED.own_signs,
    classical_citation  = EXCLUDED.classical_citation,
    notes               = EXCLUDED.notes;


-- ─── 2. bg_graha_naisargika_friendship ───────────────────────────────────────
-- Natural friendship table. One row per (graha, other_graha) pair.
-- relation: 'great_friend' | 'friend' | 'neutral' | 'enemy' | 'great_enemy'
-- Note: great_friend / great_enemy are used in panchadha_maitri (tatkalika
-- upgrades); the naisargika table itself uses friend/neutral/enemy.

CREATE TABLE IF NOT EXISTS bg_graha_naisargika_friendship (
    id                  SERIAL PRIMARY KEY,
    graha               TEXT NOT NULL,
    other_graha         TEXT NOT NULL,
    relation            TEXT NOT NULL CHECK (relation IN ('friend','neutral','enemy')),
    classical_citation  TEXT,
    UNIQUE (graha, other_graha)
);

INSERT INTO bg_graha_naisargika_friendship (graha, other_graha, relation, classical_citation)
VALUES
    -- Sun's relations (BPHS Ch.27)
    ('Sun', 'Moon',    'friend',  'BPHS Ch.27'),
    ('Sun', 'Mars',    'friend',  'BPHS Ch.27'),
    ('Sun', 'Jupiter', 'friend',  'BPHS Ch.27'),
    ('Sun', 'Mercury', 'neutral', 'BPHS Ch.27'),
    ('Sun', 'Venus',   'enemy',   'BPHS Ch.27'),
    ('Sun', 'Saturn',  'enemy',   'BPHS Ch.27'),
    ('Sun', 'Rahu',    'enemy',   'BPHS Ch.27'),
    ('Sun', 'Ketu',    'neutral', 'BPHS Ch.27'),

    -- Moon's relations (BPHS Ch.27)
    ('Moon', 'Sun',     'friend',  'BPHS Ch.27'),
    ('Moon', 'Mercury', 'friend',  'BPHS Ch.27'),
    ('Moon', 'Mars',    'neutral', 'BPHS Ch.27'),
    ('Moon', 'Jupiter', 'neutral', 'BPHS Ch.27'),
    ('Moon', 'Venus',   'neutral', 'BPHS Ch.27'),
    ('Moon', 'Saturn',  'neutral', 'BPHS Ch.27'),
    ('Moon', 'Rahu',    'enemy',   'BPHS Ch.27'),
    ('Moon', 'Ketu',    'neutral', 'BPHS Ch.27'),

    -- Mars's relations (BPHS Ch.27)
    ('Mars', 'Sun',     'friend',  'BPHS Ch.27'),
    ('Mars', 'Moon',    'friend',  'BPHS Ch.27'),
    ('Mars', 'Jupiter', 'friend',  'BPHS Ch.27'),
    ('Mars', 'Venus',   'neutral', 'BPHS Ch.27'),
    ('Mars', 'Saturn',  'neutral', 'BPHS Ch.27'),
    ('Mars', 'Mercury', 'enemy',   'BPHS Ch.27'),
    ('Mars', 'Rahu',    'neutral', 'BPHS Ch.27'),
    ('Mars', 'Ketu',    'friend',  'BPHS Ch.27'),

    -- Mercury's relations (BPHS Ch.27)
    ('Mercury', 'Sun',     'friend',  'BPHS Ch.27'),
    ('Mercury', 'Venus',   'friend',  'BPHS Ch.27'),
    ('Mercury', 'Mars',    'neutral', 'BPHS Ch.27'),
    ('Mercury', 'Jupiter', 'neutral', 'BPHS Ch.27'),
    ('Mercury', 'Saturn',  'neutral', 'BPHS Ch.27'),
    ('Mercury', 'Moon',    'enemy',   'BPHS Ch.27'),
    ('Mercury', 'Rahu',    'friend',  'BPHS Ch.27'),
    ('Mercury', 'Ketu',    'neutral', 'BPHS Ch.27'),

    -- Jupiter's relations (BPHS Ch.27)
    ('Jupiter', 'Sun',     'friend',  'BPHS Ch.27'),
    ('Jupiter', 'Moon',    'friend',  'BPHS Ch.27'),
    ('Jupiter', 'Mars',    'friend',  'BPHS Ch.27'),
    ('Jupiter', 'Saturn',  'neutral', 'BPHS Ch.27'),
    ('Jupiter', 'Mercury', 'enemy',   'BPHS Ch.27'),
    ('Jupiter', 'Venus',   'enemy',   'BPHS Ch.27'),
    ('Jupiter', 'Rahu',    'neutral', 'BPHS Ch.27'),
    ('Jupiter', 'Ketu',    'neutral', 'BPHS Ch.27'),

    -- Venus's relations (BPHS Ch.27)
    ('Venus', 'Mercury', 'friend',  'BPHS Ch.27'),
    ('Venus', 'Saturn',  'friend',  'BPHS Ch.27'),
    ('Venus', 'Mars',    'neutral', 'BPHS Ch.27'),
    ('Venus', 'Jupiter', 'neutral', 'BPHS Ch.27'),
    ('Venus', 'Sun',     'enemy',   'BPHS Ch.27'),
    ('Venus', 'Moon',    'enemy',   'BPHS Ch.27'),
    ('Venus', 'Rahu',    'friend',  'BPHS Ch.27'),
    ('Venus', 'Ketu',    'friend',  'BPHS Ch.27'),

    -- Saturn's relations (BPHS Ch.27)
    ('Saturn', 'Mercury', 'friend',  'BPHS Ch.27'),
    ('Saturn', 'Venus',   'friend',  'BPHS Ch.27'),
    ('Saturn', 'Jupiter', 'neutral', 'BPHS Ch.27'),
    ('Saturn', 'Sun',     'enemy',   'BPHS Ch.27'),
    ('Saturn', 'Moon',    'enemy',   'BPHS Ch.27'),
    ('Saturn', 'Mars',    'enemy',   'BPHS Ch.27'),
    ('Saturn', 'Rahu',    'friend',  'BPHS Ch.27'),
    ('Saturn', 'Ketu',    'friend',  'BPHS Ch.27'),

    -- Rahu's relations (classical synthesis)
    ('Rahu', 'Venus',   'friend',  'Classical_Rahu_Maitri'),
    ('Rahu', 'Saturn',  'friend',  'Classical_Rahu_Maitri'),
    ('Rahu', 'Mercury', 'friend',  'Classical_Rahu_Maitri'),
    ('Rahu', 'Sun',     'enemy',   'Classical_Rahu_Maitri'),
    ('Rahu', 'Moon',    'enemy',   'Classical_Rahu_Maitri'),
    ('Rahu', 'Mars',    'neutral', 'Classical_Rahu_Maitri'),
    ('Rahu', 'Jupiter', 'neutral', 'Classical_Rahu_Maitri'),
    ('Rahu', 'Ketu',    'enemy',   'Classical_Rahu_Maitri'),

    -- Ketu's relations (classical synthesis)
    ('Ketu', 'Mars',    'friend',  'Classical_Ketu_Maitri'),
    ('Ketu', 'Venus',   'friend',  'Classical_Ketu_Maitri'),
    ('Ketu', 'Saturn',  'friend',  'Classical_Ketu_Maitri'),
    ('Ketu', 'Sun',     'neutral', 'Classical_Ketu_Maitri'),
    ('Ketu', 'Moon',    'neutral', 'Classical_Ketu_Maitri'),
    ('Ketu', 'Mercury', 'neutral', 'Classical_Ketu_Maitri'),
    ('Ketu', 'Jupiter', 'neutral', 'Classical_Ketu_Maitri'),
    ('Ketu', 'Rahu',    'enemy',   'Classical_Ketu_Maitri')
ON CONFLICT (graha, other_graha) DO UPDATE SET
    relation           = EXCLUDED.relation,
    classical_citation = EXCLUDED.classical_citation;


-- ─── 3. bg_avastha_schemes ───────────────────────────────────────────────────
-- Five classical avastha classification schemes.
-- One row per (scheme_name, state_name). determination_rule is a JSONB
-- descriptor of how to derive the state at runtime.

CREATE TABLE IF NOT EXISTS bg_avastha_schemes (
    id                  SERIAL PRIMARY KEY,
    scheme_name         TEXT NOT NULL,   -- 'baladi','jagradadi','deeptaadi','lajjitaadi','sayanadi'
    state_name          TEXT NOT NULL,
    state_order         INT  NOT NULL,   -- rank within scheme (1 = best/first)
    determination_rule  JSONB NOT NULL,
    classical_citation  TEXT,
    notes               TEXT,
    UNIQUE (scheme_name, state_name)
);

-- Baladi (5 states by degree in sign — Jataka Parijata)
INSERT INTO bg_avastha_schemes (scheme_name, state_name, state_order, determination_rule, classical_citation, notes)
VALUES
    ('baladi', 'bala',    1,
     '{"type":"degree_in_sign","range_from":0,"range_to":6}',
     'JP Ch.7', 'Infant (0–6°): weak, impressionable'),
    ('baladi', 'kumara',  2,
     '{"type":"degree_in_sign","range_from":6,"range_to":12}',
     'JP Ch.7', 'Youth (6–12°): growing strength'),
    ('baladi', 'yuva',    3,
     '{"type":"degree_in_sign","range_from":12,"range_to":18}',
     'JP Ch.7', 'Prime (12–18°): peak vitality'),
    ('baladi', 'vriddha', 4,
     '{"type":"degree_in_sign","range_from":18,"range_to":24}',
     'JP Ch.7', 'Elder (18–24°): declining potency'),
    ('baladi', 'mrita',   5,
     '{"type":"degree_in_sign","range_from":24,"range_to":30}',
     'JP Ch.7', 'Dead (24–30°): minimal efficacy')
ON CONFLICT (scheme_name, state_name) DO UPDATE SET
    state_order        = EXCLUDED.state_order,
    determination_rule = EXCLUDED.determination_rule,
    classical_citation = EXCLUDED.classical_citation,
    notes              = EXCLUDED.notes;

-- Jagradadi (3 states — BPHS)
INSERT INTO bg_avastha_schemes (scheme_name, state_name, state_order, determination_rule, classical_citation, notes)
VALUES
    ('jagradadi', 'jagrata',  1,
     '{"type":"sign_dignity","dignity_map":{"exalted":"jagrata","moolatrikona":"jagrata","own":"jagrata"}}',
     'BPHS Ch.45', 'Awake: full expression — own/exaltation/moolatrikona'),
    ('jagradadi', 'svapna',   2,
     '{"type":"sign_dignity","dignity_map":{"great_friend_sign":"svapna","friend_sign":"svapna"}}',
     'BPHS Ch.45', 'Dreaming: partial expression — friendly sign'),
    ('jagradadi', 'sushupti', 3,
     '{"type":"sign_dignity","dignity_map":{"neutral_sign":"sushupti","enemy_sign":"sushupti","great_enemy_sign":"sushupti","debilitated":"sushupti"}}',
     'BPHS Ch.45', 'Deep sleep: subdued expression — neutral/enemy/debilitation')
ON CONFLICT (scheme_name, state_name) DO UPDATE SET
    state_order        = EXCLUDED.state_order,
    determination_rule = EXCLUDED.determination_rule,
    classical_citation = EXCLUDED.classical_citation,
    notes              = EXCLUDED.notes;

-- Deeptaadi (9 states — Phala Deepika)
INSERT INTO bg_avastha_schemes (scheme_name, state_name, state_order, determination_rule, classical_citation, notes)
VALUES
    ('deeptaadi', 'deepta',  1,
     '{"type":"sign_dignity_combustion_retrograde","condition":"exalted_or_own"}',
     'PD Ch.4', 'Bright: exalted or own sign — highest functional output'),
    ('deeptaadi', 'swastha', 2,
     '{"type":"sign_dignity_combustion_retrograde","condition":"friend_sign"}',
     'PD Ch.4', 'Comfortable: friendly sign'),
    ('deeptaadi', 'mudita',  3,
     '{"type":"sign_dignity_combustion_retrograde","condition":"friend_navamsa"}',
     'PD Ch.4', 'Joyful: own or friendly navamsa sign'),
    ('deeptaadi', 'shanta',  4,
     '{"type":"sign_dignity_combustion_retrograde","condition":"neutral_sign"}',
     'PD Ch.4', 'Peaceful: neutral sign'),
    ('deeptaadi', 'shakta',  5,
     '{"type":"sign_dignity_combustion_retrograde","condition":"conjunct_benefic"}',
     'PD Ch.4', 'Powerful: conjunct natural benefic'),
    ('deeptaadi', 'dina',    6,
     '{"type":"sign_dignity_combustion_retrograde","condition":"enemy_sign"}',
     'PD Ch.4', 'Dejected: enemy sign'),
    ('deeptaadi', 'peedit',  7,
     '{"type":"sign_dignity_combustion_retrograde","condition":"combust_or_conjunct_malefic"}',
     'PD Ch.4', 'Tormented: combust or conjunct malefic'),
    ('deeptaadi', 'khala',   8,
     '{"type":"sign_dignity_combustion_retrograde","condition":"debilitated"}',
     'PD Ch.4', 'Wicked: debilitation sign'),
    ('deeptaadi', 'vikala',  9,
     '{"type":"sign_dignity_combustion_retrograde","condition":"retrograde_in_enemy"}',
     'PD Ch.4', 'Disabled: retrograde in enemy sign')
ON CONFLICT (scheme_name, state_name) DO UPDATE SET
    state_order        = EXCLUDED.state_order,
    determination_rule = EXCLUDED.determination_rule,
    classical_citation = EXCLUDED.classical_citation,
    notes              = EXCLUDED.notes;

-- Lajjitaadi (6 states — Uttara Kalamrita)
INSERT INTO bg_avastha_schemes (scheme_name, state_name, state_order, determination_rule, classical_citation, notes)
VALUES
    ('lajjitaadi', 'lajjita',   1,
     '{"type":"house_conjunctions","requires_chart_context":true,"condition":"in_5th_with_malefic"}',
     'UK Ch.4', 'Ashamed: in 5th house with malefic conjunction'),
    ('lajjitaadi', 'garvita',   2,
     '{"type":"house_conjunctions","requires_chart_context":true,"condition":"own_or_exaltation_sign"}',
     'UK Ch.4', 'Proud: own or exaltation sign'),
    ('lajjitaadi', 'kshudhita', 3,
     '{"type":"house_conjunctions","requires_chart_context":true,"condition":"enemy_sign_or_conjunct_enemy"}',
     'UK Ch.4', 'Hungry: enemy sign or conjunct enemy planet'),
    ('lajjitaadi', 'trishita',  4,
     '{"type":"house_conjunctions","requires_chart_context":true,"condition":"conjunct_saturn_no_benefic"}',
     'UK Ch.4', 'Thirsty: conjunct Saturn with no benefic relief'),
    ('lajjitaadi', 'mudita',    5,
     '{"type":"house_conjunctions","requires_chart_context":true,"condition":"conjunct_friend_in_own_sign"}',
     'UK Ch.4', 'Delighted: conjunct/aspected by natural friend in own sign'),
    ('lajjitaadi', 'kshobhita', 6,
     '{"type":"house_conjunctions","requires_chart_context":true,"condition":"conjunct_sun_or_aspected_malefic"}',
     'UK Ch.4', 'Agitated: conjunct Sun or aspected by malefic')
ON CONFLICT (scheme_name, state_name) DO UPDATE SET
    state_order        = EXCLUDED.state_order,
    determination_rule = EXCLUDED.determination_rule,
    classical_citation = EXCLUDED.classical_citation,
    notes              = EXCLUDED.notes;

-- Sayanadi (12 states — Phala Deepika / Jataka Parijata; simplified posture scheme)
INSERT INTO bg_avastha_schemes (scheme_name, state_name, state_order, determination_rule, classical_citation, notes)
VALUES
    ('sayanadi', 'sayana',       1,
     '{"type":"planet_count_in_sign","note":"12-state posture; count of planets in sign determines posture index"}',
     'PD Ch.4; JP Ch.7', 'Sleeping'),
    ('sayanadi', 'upavesana',    2,
     '{"type":"planet_count_in_sign","note":"12-state posture scheme"}',
     'PD Ch.4; JP Ch.7', 'Sitting'),
    ('sayanadi', 'netrapani',    3,
     '{"type":"planet_count_in_sign","note":"12-state posture scheme"}',
     'PD Ch.4; JP Ch.7', 'Eyes in hand (protective)'),
    ('sayanadi', 'prakasana',    4,
     '{"type":"planet_count_in_sign","note":"12-state posture scheme"}',
     'PD Ch.4; JP Ch.7', 'Illuminating'),
    ('sayanadi', 'gamana',       5,
     '{"type":"planet_count_in_sign","note":"12-state posture scheme"}',
     'PD Ch.4; JP Ch.7', 'Moving/going'),
    ('sayanadi', 'agamana',      6,
     '{"type":"planet_count_in_sign","note":"12-state posture scheme"}',
     'PD Ch.4; JP Ch.7', 'Arriving'),
    ('sayanadi', 'sabha',        7,
     '{"type":"planet_count_in_sign","note":"12-state posture scheme"}',
     'PD Ch.4; JP Ch.7', 'In assembly'),
    ('sayanadi', 'agama',        8,
     '{"type":"planet_count_in_sign","note":"12-state posture scheme"}',
     'PD Ch.4; JP Ch.7', 'Approach'),
    ('sayanadi', 'bhojanaprapta',9,
     '{"type":"planet_count_in_sign","note":"12-state posture scheme"}',
     'PD Ch.4; JP Ch.7', 'Receiving food (prosperity)'),
    ('sayanadi', 'kautuka',      10,
     '{"type":"planet_count_in_sign","note":"12-state posture scheme"}',
     'PD Ch.4; JP Ch.7', 'Curious/sporting'),
    ('sayanadi', 'nidraksita',   11,
     '{"type":"planet_count_in_sign","note":"12-state posture scheme"}',
     'PD Ch.4; JP Ch.7', 'Deep sleep'),
    ('sayanadi', 'deeptamsa',    12,
     '{"type":"planet_count_in_sign","note":"12-state posture scheme"}',
     'PD Ch.4; JP Ch.7', 'Bright portion (peak)')
ON CONFLICT (scheme_name, state_name) DO UPDATE SET
    state_order        = EXCLUDED.state_order,
    determination_rule = EXCLUDED.determination_rule,
    classical_citation = EXCLUDED.classical_citation,
    notes              = EXCLUDED.notes;


-- ─── 4. bg_motion_state_thresholds ───────────────────────────────────────────
-- Per-graha speed thresholds that determine motion state labels.
-- motion_state: 'vakra' (retrograde), 'anuvakra' (slow/station), 'manda' (slow),
--               'sama' (mean/normal), 'atichara' (fast).
-- Rahu and Ketu are always vakra (mean retrograde motion ≈ –0.053°/day).

CREATE TABLE IF NOT EXISTS bg_motion_state_thresholds (
    id                  SERIAL PRIMARY KEY,
    graha               TEXT NOT NULL,
    motion_state        TEXT NOT NULL CHECK (motion_state IN ('vakra','anuvakra','manda','sama','atichara')),
    speed_threshold_low  NUMERIC,   -- speed < this (or speed range low)
    speed_threshold_high NUMERIC,   -- speed > this (or speed range high); NULL = open-ended
    threshold_type      TEXT NOT NULL CHECK (threshold_type IN ('below','above','range','always')),
    typical_speed_dps   NUMERIC,    -- representative mean speed in deg/day
    classical_citation  TEXT,
    notes               TEXT,
    UNIQUE (graha, motion_state)
);

INSERT INTO bg_motion_state_thresholds
    (graha, motion_state, speed_threshold_low, speed_threshold_high, threshold_type,
     typical_speed_dps, classical_citation, notes)
VALUES
    -- Sun: never retrograde; atichara at > 1.02°/day
    ('Sun', 'sama',      NULL, NULL,  'always', 0.9856, 'SS / Saravali', 'Sun mean motion'),
    ('Sun', 'atichara',  1.02, NULL,  'above',  NULL,   'SS / Saravali', 'Sun fast (perihelion season)'),

    -- Moon: very fast; atichara > 15°/day
    ('Moon', 'sama',     NULL, NULL,  'always', 13.176, 'SS / Saravali', 'Moon mean motion'),
    ('Moon', 'atichara', 15.0, NULL,  'above',  NULL,   'SS / Saravali', 'Moon fast'),

    -- Mars
    ('Mars', 'vakra',    NULL,  0,    'below',  NULL,   'SS / Saravali', 'Retrograde: speed < 0'),
    ('Mars', 'anuvakra', 0,     0.1,  'range',  NULL,   'SS / Saravali', 'Station / slow (0–0.1°/day)'),
    ('Mars', 'manda',    0.1,   0.5,  'range',  NULL,   'SS / Saravali', 'Slow (0.1–0.5°/day)'),
    ('Mars', 'sama',     0.5,   0.8,  'range',  0.524,  'SS / Saravali', 'Normal range'),
    ('Mars', 'atichara', 0.8,   NULL, 'above',  NULL,   'SS / Saravali', 'Fast'),

    -- Mercury
    ('Mercury', 'vakra',    NULL,  0,   'below',  NULL,   'SS / Saravali', 'Retrograde'),
    ('Mercury', 'anuvakra', 0,     0.1, 'range',  NULL,   'SS / Saravali', 'Station / slow'),
    ('Mercury', 'sama',     0.1,   2.5, 'range',  1.383,  'SS / Saravali', 'Normal range'),
    ('Mercury', 'atichara', 2.5,   NULL,'above',  NULL,   'SS / Saravali', 'Fast'),

    -- Jupiter
    ('Jupiter', 'vakra',    NULL,  0,    'below',  NULL,  'SS / Saravali', 'Retrograde'),
    ('Jupiter', 'anuvakra', 0,     0.05, 'range',  NULL,  'SS / Saravali', 'Station / slow'),
    ('Jupiter', 'sama',     0.05,  0.15, 'range',  0.083, 'SS / Saravali', 'Normal range'),
    ('Jupiter', 'atichara', 0.15,  NULL, 'above',  NULL,  'SS / Saravali', 'Fast'),

    -- Venus
    ('Venus', 'vakra',    NULL,  0,    'below',  NULL,  'SS / Saravali', 'Retrograde'),
    ('Venus', 'anuvakra', 0,     0.05, 'range',  NULL,  'SS / Saravali', 'Station / slow'),
    ('Venus', 'sama',     0.05,  1.3,  'range',  1.202, 'SS / Saravali', 'Normal range'),
    ('Venus', 'atichara', 1.3,   NULL, 'above',  NULL,  'SS / Saravali', 'Fast'),

    -- Saturn
    ('Saturn', 'vakra',    NULL,  0,    'below',  NULL,  'SS / Saravali', 'Retrograde'),
    ('Saturn', 'anuvakra', 0,     0.02, 'range',  NULL,  'SS / Saravali', 'Station / slow'),
    ('Saturn', 'sama',     0.02,  0.13, 'range',  0.034, 'SS / Saravali', 'Normal range'),
    ('Saturn', 'atichara', 0.13,  NULL, 'above',  NULL,  'SS / Saravali', 'Fast'),

    -- Rahu: always retrograde mean motion
    ('Rahu', 'vakra', NULL, NULL, 'always', -0.053, 'SS / Saravali',
     'Rahu mean node is always retrograde; speed ≈ –0.053°/day'),

    -- Ketu: always retrograde mean motion (opposite Rahu)
    ('Ketu', 'vakra', NULL, NULL, 'always', -0.053, 'SS / Saravali',
     'Ketu mean node is always retrograde; speed ≈ –0.053°/day')
ON CONFLICT (graha, motion_state) DO UPDATE SET
    speed_threshold_low  = EXCLUDED.speed_threshold_low,
    speed_threshold_high = EXCLUDED.speed_threshold_high,
    threshold_type       = EXCLUDED.threshold_type,
    typical_speed_dps    = EXCLUDED.typical_speed_dps,
    classical_citation   = EXCLUDED.classical_citation,
    notes                = EXCLUDED.notes;


-- ─── 5. bg_combustion_orbs ───────────────────────────────────────────────────
-- Combustion orbs per graha (degrees from Sun at which combustion begins / deepens).
-- Sun itself is never combust — no row for Sun.

CREATE TABLE IF NOT EXISTS bg_combustion_orbs (
    id                  SERIAL PRIMARY KEY,
    graha               TEXT NOT NULL UNIQUE,
    orb_degrees         NUMERIC NOT NULL,       -- outer orb: planet enters combustion
    deep_orb_degrees    NUMERIC NOT NULL,       -- inner orb: deep combustion (more severe)
    retrograde_note     TEXT,                   -- note if retrograde tightens the orb
    classical_citation  TEXT
);

INSERT INTO bg_combustion_orbs (graha, orb_degrees, deep_orb_degrees, retrograde_note, classical_citation)
VALUES
    ('Moon',    12, 10, NULL,
     'Saravali Ch.6 / BPHS Ch.3'),
    ('Mars',    17, 15, NULL,
     'Saravali Ch.6 / BPHS Ch.3'),
    ('Mercury', 14, 12, 'Retrograde Mercury not considered combust by some authorities (Saravali)',
     'Saravali Ch.6 / BPHS Ch.3'),
    ('Jupiter', 11,  9, NULL,
     'Saravali Ch.6 / BPHS Ch.3'),
    ('Venus',   10,  8, 'Retrograde Venus (Vipra-chara) immune from combustion per some authorities',
     'Saravali Ch.6 / BPHS Ch.3'),
    ('Saturn',  15, 12, NULL,
     'Saravali Ch.6 / BPHS Ch.3'),
    ('Rahu',     9,  7, 'Nodes combust per some traditions; excluded by others',
     'Classical_Combustion; tradition varies'),
    ('Ketu',     9,  7, 'Nodes combust per some traditions; excluded by others',
     'Classical_Combustion; tradition varies')
ON CONFLICT (graha) DO UPDATE SET
    orb_degrees        = EXCLUDED.orb_degrees,
    deep_orb_degrees   = EXCLUDED.deep_orb_degrees,
    retrograde_note    = EXCLUDED.retrograde_note,
    classical_citation = EXCLUDED.classical_citation;


COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   DROP TABLE IF EXISTS bg_combustion_orbs;
--   DROP TABLE IF EXISTS bg_motion_state_thresholds;
--   DROP TABLE IF EXISTS bg_avastha_schemes;
--   DROP TABLE IF EXISTS bg_graha_naisargika_friendship;
--   DROP TABLE IF EXISTS bg_dignity_reference;
--   COMMIT;
-- =============================================================================
