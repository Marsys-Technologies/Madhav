-- Migration 421: JL-009 close — bereavement base-rate edit + ontology version bump 1.0 -> 1.1
-- Created: 2026-07-07
--
-- Context: JL-009 (event base-rate priors) was RATIFIED-AS-DRAFTED (OPEN) pending a native
-- glance before the base_rate factor first bites at P5B (ph_nimitta posterior = base_rate x lifts).
-- Native/Acarya-Pratinidhi ruling 2026-07-07 (BA_PHASE4_RUNWAY_PLAN R1.1):
--   (1) EDIT bereavement age-band weights -> 0.10 / 0.15 / 0.30 / 0.35 / 0.40 (rising with
--       elder-cohort mortality). Previously 0.05 / 0.15 / 0.30 / 0.30 / 0.30.
--   (2..4) structural directive (ph_nimitta row-normalize at lookup + unit test), kept 60+
--       tails, confirmed separation 26-40 peak — recorded in BA_JUDGMENT_LEDGER, not schema.
-- All 22 classes are now native-ratified: this bumps the whole ontology to version 1.1 so
-- `SELECT DISTINCT version` returns a single coherent post-ratification value.
-- Reversible: ontology upsert + prior_version bump; no formula_version change (per JL-009).

BEGIN;

-- (1) bereavement age-band edit
UPDATE brahma_event_ontology
SET base_rate_by_age = '{
  "band_0_12":   0.10,
  "band_13_25":  0.15,
  "band_26_40":  0.30,
  "band_41_60":  0.35,
  "band_60_plus": 0.40
}'::jsonb
WHERE event_class_id = 'bereavement';

-- (2) ontology-wide version bump: all 22 classes ratified as v1.1
UPDATE brahma_event_ontology
SET version = '1.1'
WHERE version = '1.0';

COMMIT;

-- DOWN:
-- UPDATE brahma_event_ontology SET base_rate_by_age = '{"band_0_12":0.05,"band_13_25":0.15,"band_26_40":0.30,"band_41_60":0.30,"band_60_plus":0.30}'::jsonb WHERE event_class_id = 'bereavement';
-- UPDATE brahma_event_ontology SET version = '1.0' WHERE version = '1.1';
