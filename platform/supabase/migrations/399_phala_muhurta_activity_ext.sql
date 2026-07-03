-- Migration 399: phala_muhurta — activity-aware election EXT (BA-P5B Step 2)
-- Adds tarabala/chandrabala, significators, fructification_anchor, follow_up_hook
-- to phala_muhurta (previously M1-M4 only; now enriched per brahma_activity_ontology).
--
-- tarabala_chandrabala_jsonb: structural tarabala/chandrabala scores + natal Moon nakshatra.
--   Build-time: 0.5 stubs (transit Moon unknown). Serve-time enrichment updates these.
-- significators_met_jsonb: which brahma_activity_ontology significator conditions are met.
-- fructification_anchor: timing anchor text from activity ontology (e.g. 'tara+candra-bala').
-- follow_up_hook_jsonb: consumed by P7B prashna follow-up scheduler.

BEGIN;

ALTER TABLE phala_muhurta
    ADD COLUMN IF NOT EXISTS tarabala_chandrabala_jsonb  JSONB,
    ADD COLUMN IF NOT EXISTS significators_met_jsonb     JSONB,
    ADD COLUMN IF NOT EXISTS fructification_anchor       TEXT,
    ADD COLUMN IF NOT EXISTS follow_up_hook_jsonb        JSONB;

COMMENT ON COLUMN phala_muhurta.tarabala_chandrabala_jsonb IS
  'BA-P5B: {tarabala_score, chandrabala_score, natal_moon_nakshatra_idx, note}. '
  'tarabala: Moon''s tara strength (natal × transit nakshatra cycle). '
  'chandrabala: Moon''s rasi strength (Moon count from natal Moon rasi). '
  'Build-time: 0.5 structural defaults; serve-time enrichment supplies transit Moon.';

COMMENT ON COLUMN phala_muhurta.significators_met_jsonb IS
  'BA-P5B: brahma_activity_ontology.significators check. '
  '{strengthen_grahas, personalization_graha_match, note}. '
  'Structural check only at build time — serve-time adds live ephemeris check.';

COMMENT ON COLUMN phala_muhurta.fructification_anchor IS
  'BA-P5B: timing_anchor from brahma_activity_ontology.fructification_rules. '
  'Plain-text classical timing rule (e.g. "strong lagna+10th at election"). '
  'Displayed in muhurta election result.';

COMMENT ON COLUMN phala_muhurta.follow_up_hook_jsonb IS
  'BA-P5B: follow-up hook for P7B prashna follow-up scheduler. '
  '{action, requires, natal_moon_nakshatra_idx, action_class, fructification_anchor, consumed_by}. '
  'The scheduler reads this to trigger a tarabala/chandrabala enrichment call at election time.';

COMMIT;
