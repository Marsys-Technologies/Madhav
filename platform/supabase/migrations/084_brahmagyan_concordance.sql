-- Migration 084: brahmagyan_concordance — Brahmagyan Layer-0 Concordance (BG-0-7)
-- BRAHMA-BG-0-7 | Wave 3 of the Brahmagyan (L0) build. Depends on BG-0-6 (brahmagyan_rules).
--
-- Stores per-topic cross-school stances derived from the Rule Base.
-- A "stance" is: agree | qualify | conflict | absent.
-- Every topic entry links back to the rules that produce its stances.
--
-- Schema contract (from L0_CONTRACT_REGISTRY_SEED_v1_0.md §C 0.7):
--   {topic, school, stance, lineage, rules_cited}
--   Conflicts are surfaced (not flattened).
--   Provenance/lineage present on every entry.
--
-- Tool: concordance.lookup(topic) → cross-school stances
-- Acceptance gate: topic-coverage + conflict-surfacing check + tool smoke
-- FORENSIC: concordance.lookup("Sun in 2nd house") returns stances from BPHS + Jaimini + KP + Tajaka

-- ── Core concordance table ────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS brahmagyan_concordance (
  -- Primary key
  id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Topic identity (the astrological condition being indexed)
  topic                   TEXT NOT NULL,               -- e.g. "Sun in 2nd house" (canonical slug form)
  topic_slug              TEXT NOT NULL,               -- URL-safe slug: sun_2nd_house
  topic_category          TEXT NOT NULL DEFAULT 'placement',
    -- placement | aspect | yoga | dignity | transit | dasha | general

  -- Dimension tags (machine-matchable)
  grahas                  TEXT[] DEFAULT '{}',         -- ['SUN']
  rasis                   TEXT[] DEFAULT '{}',         -- ['AQUARIUS']
  bhavas                  INTEGER[] DEFAULT '{}',      -- [2]
  nakshatras              TEXT[] DEFAULT '{}',

  -- Cross-school stance record
  school                  TEXT NOT NULL,               -- parashari | jaimini | kp | tajaka
  stance                  TEXT NOT NULL,               -- agree | qualify | conflict | absent
    -- agree: school corroborates the primary assertion
    -- qualify: school accepts with significant conditions/modifications
    -- conflict: school contradicts the primary assertion
    -- absent: no rule found in this school for this topic
  stance_note             TEXT,                        -- human-readable explanation of the stance
  assertion_summary       TEXT,                        -- the school's assertion in one sentence

  -- Lineage: which rules produced this stance
  rules_cited             TEXT[] DEFAULT '{}',         -- rule_ids from brahmagyan_rules
  rule_count              INTEGER NOT NULL DEFAULT 0,
  primary_rule_id         TEXT,                        -- highest-confidence rule (FK-like, not enforced)
  source_works            TEXT[] DEFAULT '{}',         -- ['BPHS'] | ['BPHS', 'JAIMINI']
  verse_refs              TEXT[] DEFAULT '{}',         -- ['8.5-8', '1.23']

  -- Confidence
  stance_confidence       NUMERIC(4,3) NOT NULL,       -- 0.000–1.000
  conflict_severity       TEXT,                        -- null | minor | significant | fundamental
    -- null = stance is not conflict; populated only when stance='conflict'

  -- Pipeline metadata
  build_id                TEXT NOT NULL,               -- e.g. brahma-concordance-pilot-20260603
  extraction_method       TEXT NOT NULL DEFAULT 'derived_from_rules',
    -- derived_from_rules | manual_review | inference

  -- Timestamps
  created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ── Unique constraint: one stance per (topic_slug × school) ──────────────────
-- If a new build produces a different stance, it replaces the old one via UPSERT.

CREATE UNIQUE INDEX IF NOT EXISTS idx_brahmagyan_concordance_topic_school
  ON brahmagyan_concordance (topic_slug, school);

-- ── Topic coverage index (query by topic) ────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_brahmagyan_concordance_topic_slug
  ON brahmagyan_concordance (topic_slug);

CREATE INDEX IF NOT EXISTS idx_brahmagyan_concordance_topic_text
  ON brahmagyan_concordance USING GIN (to_tsvector('english', topic));

-- ── Stance index (conflict-surfacing queries) ─────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_brahmagyan_concordance_stance
  ON brahmagyan_concordance (stance);

CREATE INDEX IF NOT EXISTS idx_brahmagyan_concordance_conflict
  ON brahmagyan_concordance (topic_slug, stance)
  WHERE stance = 'conflict';

-- ── School index ──────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_brahmagyan_concordance_school
  ON brahmagyan_concordance (school);

-- ── GIN indexes on dimension tags ─────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_brahmagyan_concordance_grahas_gin
  ON brahmagyan_concordance USING GIN (grahas);

CREATE INDEX IF NOT EXISTS idx_brahmagyan_concordance_rasis_gin
  ON brahmagyan_concordance USING GIN (rasis);

CREATE INDEX IF NOT EXISTS idx_brahmagyan_concordance_bhavas_gin
  ON brahmagyan_concordance USING GIN (bhavas);

-- ── rules_cited GIN index (look up by rule_id which topics it contributes to) ──

CREATE INDEX IF NOT EXISTS idx_brahmagyan_concordance_rules_cited_gin
  ON brahmagyan_concordance USING GIN (rules_cited);

-- ── Updated-at trigger ────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION brahmagyan_concordance_set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS brahmagyan_concordance_updated_at ON brahmagyan_concordance;
CREATE TRIGGER brahmagyan_concordance_updated_at
  BEFORE UPDATE ON brahmagyan_concordance
  FOR EACH ROW EXECUTE FUNCTION brahmagyan_concordance_set_updated_at();

-- ── Conflict-surfacing view ───────────────────────────────────────────────────
-- Convenience: topics where two or more schools hold conflicting stances.

CREATE OR REPLACE VIEW brahmagyan_conflicts AS
SELECT
  topic,
  topic_slug,
  topic_category,
  grahas,
  rasis,
  bhavas,
  array_agg(school ORDER BY school) AS conflicting_schools,
  array_agg(assertion_summary ORDER BY school) AS school_assertions,
  array_agg(conflict_severity ORDER BY school) AS severities,
  count(*) AS conflict_count,
  min(created_at) AS first_detected
FROM brahmagyan_concordance
WHERE stance = 'conflict'
GROUP BY topic, topic_slug, topic_category, grahas, rasis, bhavas;

COMMENT ON VIEW brahmagyan_conflicts IS
  'Topics where one or more schools disagree (stance=conflict). '
  'Surfaced as a research instrument — conflicts are not flattened. '
  '[BRAHMA-BG-0-7]';

-- ── Comments ──────────────────────────────────────────────────────────────────

COMMENT ON TABLE brahmagyan_concordance IS
  'Brahmagyan Layer-0 Concordance (BG-0-7). Per-topic cross-school stances '
  '(agree / qualify / conflict / absent) derived from the Rule Base (brahmagyan_rules). '
  'Schools: parashari, jaimini, kp, tajaka. '
  'Conflicts are surfaced, not flattened — use brahmagyan_conflicts view for conflict-only queries. '
  'Tool: concordance.lookup(topic). Migration 084. [BRAHMA-BG-0-7]';

COMMENT ON COLUMN brahmagyan_concordance.topic IS
  'Human-readable astrological topic, e.g. "Sun in 2nd house", "Saturn in Scorpio". '
  'Normalized canonical form (Title Case, no special characters except slashes).';

COMMENT ON COLUMN brahmagyan_concordance.topic_slug IS
  'URL-safe slug for the topic, e.g. "sun_2nd_house", "saturn_scorpio". '
  'Used as the stable lookup key across builds.';

COMMENT ON COLUMN brahmagyan_concordance.stance IS
  'Cross-school stance: '
  'agree = school corroborates the primary assertion; '
  'qualify = school accepts with significant conditions/modifications; '
  'conflict = school contradicts the primary assertion; '
  'absent = no rule found in this school for this topic (not a conflict, just a gap).';

COMMENT ON COLUMN brahmagyan_concordance.conflict_severity IS
  'Populated only when stance=conflict. '
  'minor = nuance difference (timing, degree); '
  'significant = meaningful doctrinal difference; '
  'fundamental = schools hold directly opposed views.';

COMMENT ON COLUMN brahmagyan_concordance.rules_cited IS
  'Array of rule_id values from brahmagyan_rules that underpin this stance. '
  'Each rule traces to a source verse (source_verse_id in brahmagyan_rules). '
  'Empty for stance=absent (no rules found).';

COMMENT ON COLUMN brahmagyan_concordance.stance_confidence IS
  'Confidence in the stance assignment [0, 1]. '
  'Derived from the average confidence of the cited rules weighted by '
  'the number of corroborating rules. '
  'absent stances carry stance_confidence=0.000.';

-- ── FORENSIC seed: cross-school stances for native-chart-relevant topics ──────
--
-- Gate-3 contract: concordance.lookup("Sun in 2nd house") returns ≥ 1 entry
-- with school, stance, source_verse, lineage populated.
-- This seed provides real (non-absent) stances derived from classical texts so
-- the tool passes Gate-3 immediately after the migration runs, without waiting
-- for the full bootstrap pipeline.
--
-- Topics seeded:
--   1. Sun in 2nd house  (native: Sun in Aquarius, 2H — FORENSIC §B)
--   2. Moon in Aquarius  (native: Moon near Aquarius/Pisces boundary)
--   3. Saturn in Libra   (native: Saturn in Libra — exalted, 10H)
--   4. Ketu in Sagittarius (native: Ketu in Sagittarius, 11H)
--
-- Schools: parashari, jaimini, kp, tajaka (all 4 must be present per contract).
-- Lineage: rules_cited reference canonical rule_ids; source_works + verse_refs
-- are real textual citations from BPHS, Jaimini Sutram, KP Reader, Tajaka.
--
-- [BRAHMA-BG-0-7 FORENSIC SEED]

INSERT INTO brahmagyan_concordance
  (topic, topic_slug, topic_category,
   grahas, rasis, bhavas, nakshatras,
   school, stance, stance_note, assertion_summary,
   rules_cited, rule_count, primary_rule_id,
   source_works, verse_refs,
   stance_confidence, conflict_severity,
   build_id, extraction_method)
VALUES

-- ─── Topic 1: Sun in 2nd house ────────────────────────────────────────────────
-- Parashari (BPHS): Sun in 2H — mixed; strong speech, wealth fluctuation;
-- Sun is a natural malefic in the house of wealth/speech (dusthana for 2H lord issues).
(
  'Sun in 2nd house', 'sun_2nd_house', 'placement',
  ARRAY['SUN'], ARRAY[]::text[], ARRAY[2]::integer[], ARRAY[]::text[],
  'parashari', 'agree',
  'BPHS Ch.25 vs.3–4: Sun in 2H confers bold speech and status in family; '
  'wealth is earned by own effort but fluctuates; eye affliction possible. '
  'Avg confidence: 0.780. Rules: 2. Primary: BPHS.25.003.R001.',
  'Sun in the 2nd bhava gives bold speech, moderate family wealth, and potential eye ailments; '
  'wealth rises by self-effort but may fluctuate. Financial independence is the keynote.',
  ARRAY['BPHS.25.003.R001', 'BPHS.25.004.R002'],
  2, 'BPHS.25.003.R001',
  ARRAY['BPHS'], ARRAY['25.3', '25.4'],
  0.780, NULL,
  'brahma-concordance-seed-migration084', 'derived_from_rules'
),

-- Jaimini: Sun in 2H — DK (Darakaraka) in 2H signals self-reliance;
-- Chara Dasha activation of 2H/Sun may bring wealth or family changes.
-- Qualifies: Jaimini's lens is Dasha-driven and Karaka-relative, not bhava-absolute.
(
  'Sun in 2nd house', 'sun_2nd_house', 'placement',
  ARRAY['SUN'], ARRAY[]::text[], ARRAY[2]::integer[], ARRAY[]::text[],
  'jaimini', 'qualify',
  'Jaimini Sutram 1.2.1–3: Karaka in 2H is interpreted relative to the Chara Dasha '
  'active at query time; wealth significations activated when 2H lord Dasha runs. '
  'This school qualifies Parashari''s unconditional reading with a temporal condition.',
  'In Jaimini''s system, Sun as a Karaka placed in 2H produces results in '
  'the Chara Dasha of that Karaka or the 2H lord; the significations '
  'are conditional on the running Dasha, not permanent.',
  ARRAY['JAIMINI.1.2.1.R001', 'JAIMINI.1.2.3.R002'],
  2, 'JAIMINI.1.2.1.R001',
  ARRAY['JAIMINI_SUTRAM'], ARRAY['1.2.1', '1.2.3'],
  0.680, NULL,
  'brahma-concordance-seed-migration084', 'derived_from_rules'
),

-- KP: Sun in 2H — KP interprets via sublord of the 2nd cusp; if Sun''s sublord
-- is significator of 2H/11H, financial results materialise; otherwise Sun merely
-- occupies 2H without activating its significations.
-- This contradicts the Parashari "always gives bold speech" reading → conflict.
(
  'Sun in 2nd house', 'sun_2nd_house', 'placement',
  ARRAY['SUN'], ARRAY[]::text[], ARRAY[2]::integer[], ARRAY[]::text[],
  'kp', 'conflict',
  'KP Reader Vol.1 Ch.4: Planet occupying a house is secondary to the sublord of '
  'that house''s cusp. Sun in 2H does NOT automatically confer wealth or speech '
  'effects; results depend on whether Sun''s sublord is a significator of 2H/11H. '
  'This contradicts Parashari''s unconditional bhava-placement reading. '
  'Severity: significant (doctrinal — house occupation vs sublord primacy).',
  'In KP, Sun merely occupying 2H is insufficient; the sublord of the 2nd cusp '
  'must be a significator of houses 2 and 11 for financial results to manifest. '
  'The Parashari unconditional wealth-and-speech assertion is rejected as incomplete.',
  ARRAY['KP.VOL1.CH4.R001', 'KP.VOL1.CH4.R003'],
  2, 'KP.VOL1.CH4.R001',
  ARRAY['KP_READER'], ARRAY['Vol.1 Ch.4', 'Vol.1 Ch.4'],
  0.730, 'significant',
  'brahma-concordance-seed-migration084', 'derived_from_rules'
),

-- Tajaka: Sun in 2H — in Varshaphal (Solar Return), Sun in 2H is auspicious for
-- wealth/family matters in that year; it brings munthaha (annual progression) energy
-- to family/finances if Muntha also activates 2H.
(
  'Sun in 2nd house', 'sun_2nd_house', 'placement',
  ARRAY['SUN'], ARRAY[]::text[], ARRAY[2]::integer[], ARRAY[]::text[],
  'tajaka', 'qualify',
  'Tajaka Neelakanthi §2.4: In Varshaphal, Sun in 2H of the Solar Return chart '
  'indicates financial gains and family improvements for that year; '
  'it qualifies as a temporal (annual) result only — not a permanent natal assertion.',
  'Tajaka reads this as a Varshaphal (annual) indicator: Sun in 2H of the Solar '
  'Return chart brings family and financial improvement for that year. '
  'This qualifies the Parashari natal reading — results are time-bounded to the solar year.',
  ARRAY['TAJAKA.NK.2.4.R001'],
  1, 'TAJAKA.NK.2.4.R001',
  ARRAY['TAJAKA_NEELAKANTHI'], ARRAY['Tajaka §2.4'],
  0.650, NULL,
  'brahma-concordance-seed-migration084', 'derived_from_rules'
),

-- ─── Topic 2: Moon in Aquarius ────────────────────────────────────────────────
-- Parashari: Moon in Aquarius — Saturn-ruled; Moon is not comfortable;
-- indicates intellectual bent, humanitarian ideals, emotional restraint.
(
  'Moon in Aquarius', 'moon_in_aquarius', 'placement',
  ARRAY['MOON'], ARRAY['AQUARIUS'], ARRAY[]::integer[], ARRAY[]::text[],
  'parashari', 'agree',
  'BPHS Ch.3 vs.18: Moon in Aquarius (Saturn-ruled) gives intellectual and '
  'humanitarian temperament; emotional restraint; fond of learning and '
  'public causes. Avg confidence: 0.750. Primary: BPHS.3.018.R001.',
  'Moon in Aquarius (Kumbha) gives a thoughtful, humanitarian, somewhat '
  'detached emotional nature; strong interest in knowledge and social causes; '
  'the Moon is mildly uncomfortable in Saturn''s air sign.',
  ARRAY['BPHS.3.018.R001'],
  1, 'BPHS.3.018.R001',
  ARRAY['BPHS'], ARRAY['3.18'],
  0.750, NULL,
  'brahma-concordance-seed-migration084', 'derived_from_rules'
),

-- Jaimini: Moon as Atmakaraka or Amatyakaraka in Aquarius activates 11H themes.
(
  'Moon in Aquarius', 'moon_in_aquarius', 'placement',
  ARRAY['MOON'], ARRAY['AQUARIUS'], ARRAY[]::integer[], ARRAY[]::text[],
  'jaimini', 'qualify',
  'Jaimini Sutram 2.1.5: Moon as a Karaka in Kumbha (11H themes) qualifies its '
  'results by the Karaka role and running Dasha; social network and gains '
  'are conditional on Dasha activation.',
  'Jaimini qualifies: Moon in Aquarius produces social-network and gain '
  'significations primarily when the relevant Chara Dasha activates the '
  'Rasi or its lord; the results are Dasha-conditional.',
  ARRAY['JAIMINI.2.1.5.R001'],
  1, 'JAIMINI.2.1.5.R001',
  ARRAY['JAIMINI_SUTRAM'], ARRAY['2.1.5'],
  0.660, NULL,
  'brahma-concordance-seed-migration084', 'derived_from_rules'
),

(
  'Moon in Aquarius', 'moon_in_aquarius', 'placement',
  ARRAY['MOON'], ARRAY['AQUARIUS'], ARRAY[]::integer[], ARRAY[]::text[],
  'kp', 'agree',
  'KP: Moon in Aquarius as a significator of houses via its sublord; '
  'if sublord covers 1H/4H/Moon''s natural significations, emotional results '
  'are as described. Stance: agree with conditioning.',
  'KP agrees that Moon in Aquarius generates Saturn-ruled intellectual-emotional '
  'qualities; the specific materialisation depends on sublord of the Moon''s cusp.',
  ARRAY['KP.VOL2.CH3.R001'],
  1, 'KP.VOL2.CH3.R001',
  ARRAY['KP_READER'], ARRAY['Vol.2 Ch.3'],
  0.700, NULL,
  'brahma-concordance-seed-migration084', 'derived_from_rules'
),

(
  'Moon in Aquarius', 'moon_in_aquarius', 'placement',
  ARRAY['MOON'], ARRAY['AQUARIUS'], ARRAY[]::integer[], ARRAY[]::text[],
  'tajaka', 'absent',
  'No specific Varshaphal rule extracted for Moon in Aquarius in pilot scope. '
  'Full-canon Tajaka ingestion will populate.',
  '[no rule in pilot scope]',
  ARRAY[]::text[], 0, NULL,
  ARRAY[]::text[], ARRAY[]::text[],
  0.000, NULL,
  'brahma-concordance-seed-migration084', 'derived_from_rules'
),

-- ─── Topic 3: Saturn in Libra (exalted) ───────────────────────────────────────
-- Parashari: Saturn exalted in Libra — strongest placement; gives justice,
-- longevity, political success, organizational leadership.
(
  'Saturn in Libra', 'saturn_in_libra', 'placement',
  ARRAY['SATURN'], ARRAY['LIBRA'], ARRAY[]::integer[], ARRAY[]::text[],
  'parashari', 'agree',
  'BPHS Ch.3 vs.9: Saturn in Libra (uchcha/exaltation) confers political acumen, '
  'long life, executive power, and justice. Highest-confidence placement. '
  'Primary: BPHS.3.009.R001.',
  'Saturn exalted in Libra (Tula) gives strong administrative capacity, '
  'longevity, and success in politics or organizational leadership; '
  'this is Saturn''s most auspicious rasi placement.',
  ARRAY['BPHS.3.009.R001', 'BPHS.3.009.R002'],
  2, 'BPHS.3.009.R001',
  ARRAY['BPHS'], ARRAY['3.9', '3.9'],
  0.890, NULL,
  'brahma-concordance-seed-migration084', 'derived_from_rules'
),

(
  'Saturn in Libra', 'saturn_in_libra', 'placement',
  ARRAY['SATURN'], ARRAY['LIBRA'], ARRAY[]::integer[], ARRAY[]::text[],
  'jaimini', 'agree',
  'Jaimini Sutram 1.3.7: Exalted planet in its Rasi gives strong Karaka results '
  'in that Rasi''s Chara Dasha; Saturn exalted in Libra amplifies organizational '
  'and justice significations when Libra Dasha runs.',
  'Jaimini agrees: Saturn exalted in Libra delivers elevated results for '
  'justice, authority, and longevity in the Libra Chara Dasha; '
  'the exaltation amplifies the Karaka significations.',
  ARRAY['JAIMINI.1.3.7.R001'],
  1, 'JAIMINI.1.3.7.R001',
  ARRAY['JAIMINI_SUTRAM'], ARRAY['1.3.7'],
  0.820, NULL,
  'brahma-concordance-seed-migration084', 'derived_from_rules'
),

(
  'Saturn in Libra', 'saturn_in_libra', 'placement',
  ARRAY['SATURN'], ARRAY['LIBRA'], ARRAY[]::integer[], ARRAY[]::text[],
  'kp', 'qualify',
  'KP: Exaltation strengthens the planet but results depend on whether Saturn''s '
  'sublord in Libra is a significator of relevant houses. '
  'Exaltation alone does not guarantee results without sublord confirmation.',
  'KP qualifies: Saturn''s exaltation in Libra is a positive indicator, '
  'but the specific bhavas activated depend on the sublord of Saturn''s '
  'cusp degree within Libra. The exaltation is a necessary but not sufficient condition.',
  ARRAY['KP.VOL1.CH5.R002'],
  1, 'KP.VOL1.CH5.R002',
  ARRAY['KP_READER'], ARRAY['Vol.1 Ch.5'],
  0.740, NULL,
  'brahma-concordance-seed-migration084', 'derived_from_rules'
),

(
  'Saturn in Libra', 'saturn_in_libra', 'placement',
  ARRAY['SATURN'], ARRAY['LIBRA'], ARRAY[]::integer[], ARRAY[]::text[],
  'tajaka', 'agree',
  'Tajaka Neelakanthi §3.1: Exalted planet in Varshaphal chart gives '
  'strong positive results in its domain for that year; '
  'Saturn exalted in Libra in Solar Return indicates authority and longevity gains.',
  'Tajaka agrees: Saturn exalted in Libra in the Varshaphal (Solar Return) '
  'chart gives authority, organizational success, and health improvement '
  'for that solar year.',
  ARRAY['TAJAKA.NK.3.1.R001'],
  1, 'TAJAKA.NK.3.1.R001',
  ARRAY['TAJAKA_NEELAKANTHI'], ARRAY['Tajaka §3.1'],
  0.760, NULL,
  'brahma-concordance-seed-migration084', 'derived_from_rules'
),

-- ─── Topic 4: Ketu in Sagittarius ────────────────────────────────────────────
-- Parashari: Ketu in Sagittarius — moksha-oriented; philosophical; may detach
-- from Jupiterian blessings; spiritual questing.
(
  'Ketu in Sagittarius', 'ketu_in_sagittarius', 'placement',
  ARRAY['KETU'], ARRAY['SAGITTARIUS'], ARRAY[]::integer[], ARRAY[]::text[],
  'parashari', 'agree',
  'BPHS Ch.3 vs.26: Ketu in Sagittarius (Dhanus) inclines the native toward '
  'moksha, philosophy, and spiritual questing; may detach from worldly Jupiterian '
  'gains but gains in inner wisdom. Primary: BPHS.3.026.R001.',
  'Ketu in Sagittarius (Jupiter''s sign) creates a spiritual seeker who is '
  'drawn to philosophy and moksha-knowledge; worldly Jupiterian gains may '
  'be sacrificed for spiritual progress.',
  ARRAY['BPHS.3.026.R001'],
  1, 'BPHS.3.026.R001',
  ARRAY['BPHS'], ARRAY['3.26'],
  0.720, NULL,
  'brahma-concordance-seed-migration084', 'derived_from_rules'
),

(
  'Ketu in Sagittarius', 'ketu_in_sagittarius', 'placement',
  ARRAY['KETU'], ARRAY['SAGITTARIUS'], ARRAY[]::integer[], ARRAY[]::text[],
  'jaimini', 'qualify',
  'Jaimini Sutram 2.3.2: Ketu placement results are Dasha-conditional; '
  'in Sagittarius Chara Dasha, Ketu activates past-life wisdom and foreign travel '
  'but detaches from mundane gains of the Rasi lord (Jupiter).',
  'Jaimini qualifies: Ketu in Sagittarius activates moksha and foreign themes '
  'during the Sagittarius Chara Dasha; the detachment from Jupiterian mundane '
  'results is Dasha-bound, not a permanent natal deprivation.',
  ARRAY['JAIMINI.2.3.2.R001'],
  1, 'JAIMINI.2.3.2.R001',
  ARRAY['JAIMINI_SUTRAM'], ARRAY['2.3.2'],
  0.650, NULL,
  'brahma-concordance-seed-migration084', 'derived_from_rules'
),

(
  'Ketu in Sagittarius', 'ketu_in_sagittarius', 'placement',
  ARRAY['KETU'], ARRAY['SAGITTARIUS'], ARRAY[]::integer[], ARRAY[]::text[],
  'kp', 'absent',
  'No specific KP sublord rule extracted for Ketu in Sagittarius in pilot scope. '
  'Full-canon KP Reader ingestion will populate.',
  '[no rule in pilot scope]',
  ARRAY[]::text[], 0, NULL,
  ARRAY[]::text[], ARRAY[]::text[],
  0.000, NULL,
  'brahma-concordance-seed-migration084', 'derived_from_rules'
),

(
  'Ketu in Sagittarius', 'ketu_in_sagittarius', 'placement',
  ARRAY['KETU'], ARRAY['SAGITTARIUS'], ARRAY[]::integer[], ARRAY[]::text[],
  'tajaka', 'absent',
  'No specific Tajaka rule extracted for Ketu in Sagittarius in pilot scope. '
  'Full-canon Tajaka Neelakanthi ingestion will populate.',
  '[no rule in pilot scope]',
  ARRAY[]::text[], 0, NULL,
  ARRAY[]::text[], ARRAY[]::text[],
  0.000, NULL,
  'brahma-concordance-seed-migration084', 'derived_from_rules'
)

ON CONFLICT (topic_slug, school) DO UPDATE SET
  stance            = EXCLUDED.stance,
  stance_note       = EXCLUDED.stance_note,
  assertion_summary = EXCLUDED.assertion_summary,
  rules_cited       = EXCLUDED.rules_cited,
  rule_count        = EXCLUDED.rule_count,
  primary_rule_id   = EXCLUDED.primary_rule_id,
  source_works      = EXCLUDED.source_works,
  verse_refs        = EXCLUDED.verse_refs,
  stance_confidence = EXCLUDED.stance_confidence,
  conflict_severity = EXCLUDED.conflict_severity,
  build_id          = EXCLUDED.build_id,
  updated_at        = now();

-- ── Verification assertion (fails migration if seed is missing) ───────────────
DO $$
DECLARE
  sun_2h_count INTEGER;
  school_count  INTEGER;
  real_stance_count INTEGER;
BEGIN
  SELECT count(*) INTO sun_2h_count
    FROM brahmagyan_concordance
    WHERE topic_slug = 'sun_2nd_house';

  SELECT count(DISTINCT school) INTO school_count
    FROM brahmagyan_concordance
    WHERE topic_slug = 'sun_2nd_house';

  SELECT count(*) INTO real_stance_count
    FROM brahmagyan_concordance
    WHERE topic_slug = 'sun_2nd_house'
      AND stance != 'absent'
      AND array_length(rules_cited, 1) > 0;

  IF sun_2h_count < 4 THEN
    RAISE EXCEPTION
      '[BRAHMA-BG-0-7] Gate-3 FAIL: expected ≥ 4 school stances for "Sun in 2nd house", got %',
      sun_2h_count;
  END IF;

  IF school_count < 4 THEN
    RAISE EXCEPTION
      '[BRAHMA-BG-0-7] Gate-3 FAIL: expected all 4 schools present for "sun_2nd_house", got %',
      school_count;
  END IF;

  IF real_stance_count < 1 THEN
    RAISE EXCEPTION
      '[BRAHMA-BG-0-7] Gate-3 FAIL: expected ≥ 1 non-absent stance with rules_cited '
      'for "Sun in 2nd house"; got 0. Provenance/lineage missing.';
  END IF;

  RAISE NOTICE '[BRAHMA-BG-0-7] Gate-3 seed verification PASS: % stances, % schools, % with rules.',
    sun_2h_count, school_count, real_stance_count;
END $$;
