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
