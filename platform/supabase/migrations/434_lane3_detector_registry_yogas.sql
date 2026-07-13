-- Migration 434: Night-1 Lane 3 — detector-registry yoga family (CR-56) +
-- ga_yoga_firings.grounds_jsonb (CR-59 grounds-checked-per-verdict storage).
--
-- Adds brahma_yoga_catalog seed rows for the 6 Lane-3 house-lord/positional
-- detectors (dhana_yoga_house_lords, raja_yoga_kendra_trikona, budha_aditya,
-- sarasvati_yoga, lakshmi_yoga, vipareeta_raja_yoga) so their citations/names
-- flow the existing catalog path. canonical_id is the table's PRIMARY KEY
-- (migration 176) — ON CONFLICT (canonical_id) DO NOTHING makes this
-- idempotent AND non-destructive where a row of that id already exists.
--
-- KNOWN COLLISIONS (documented, not silently resolved — see Lane 3 report):
--   * budha_aditya      — already exists (migration 239/l0_yogas seed) with a
--     working non-detector formation_rule_jsonb that already fires via
--     ga_yoga_writer._evaluate_yoga's "sun_mercury_conjunct" branch. This
--     INSERT is therefore a no-op for that row (ON CONFLICT DO NOTHING) —
--     its formation rule is intentionally left untouched. The NEW mandatory
--     cancellation check for budha_aditya is wired through the EXISTING
--     _BHANGA_EVALUATORS extension point in ga_yoga_writer.py instead (no
--     schema/catalog change needed for that path).
--   * lakshmi_yoga      — already exists (migration 239/l0_yogas seed),
--     currently FLOORED in _evaluate_yoga (R6A2_FLOOR_REASONS: "same
--     {lagna_lord strong} co-requirement blocker") — never fires. This
--     INSERT is a no-op for that row too; the new lakshmi_yoga DETECTOR
--     (own/exalted 9th-lord + strong Venus formulation) runs as an
--     independent registry evaluation in ga_yoga_writer.py and inserts its
--     OWN firing row when it detects a formation — safe because the
--     existing catalog-loop path for lakshmi_yoga never inserts a row today
--     (floored), so there is no UNIQUE-constraint collision at write time.
--   * dhana_yoga_house_lords, raja_yoga_kendra_trikona, sarasvati_yoga,
--     vipareeta_raja_yoga — NEW canonical_ids, distinct from the existing
--     narrower-scope rows (dhana_yoga_2_11/5_9/9_11/lagna_2/2_5_9_11,
--     kendra_trikona_raja_yoga, saraswati, vipareeta_harsha/sarala/vimala).
--     This is a deliberate, DOCUMENTED overlap per the Lane 3 brief's own
--     design (family-level detector rows with mandatory cancellation,
--     layered alongside the pre-existing granular R6A.2 catalog rows) —
--     flagged for conductor/native disposition on whether the granular rows
--     should eventually be retired in favor of the family detectors.
--
-- Additive-only: no ALTERs of existing catalog rows; only new rows (or
-- no-ops) plus one new nullable column on ga_yoga_firings.

BEGIN;

ALTER TABLE ga_yoga_firings
    ADD COLUMN IF NOT EXISTS grounds_jsonb JSONB;

COMMENT ON COLUMN ga_yoga_firings.grounds_jsonb IS
  'Lane 3 / CR-59: grounds-checked-per-verdict ledger — every rule the writer '
  'evaluated for this firing (fired AND not-fired), each with checked=true and '
  'a fired boolean + detail, so any served verdict is traceable to what was '
  'actually checked (not just what fired). Currently populated for '
  'neecha_bhanga_raja_yoga (per-planet, per-varga D1/D9 rule ledger, CR-59/'
  'CR-23). NULL for yogas this writer does not yet populate a ledger for.';

INSERT INTO brahma_yoga_catalog (
    canonical_id, name_sa, name_en, category, formation_rule_jsonb,
    formation_text, significations_jsonb, significations_text,
    cancellation_conditions, classical_citations, school, rare
) VALUES
(
    'dhana_yoga_house_lords', 'Dhana (Gṛhādhipati) Yoga', 'Dhana Yoga (House-Lord Family)',
    'dhana',
    '{"detector": "dhana_yoga_house_lords"}'::jsonb,
    'Any association (conjunction, mutual Parashari aspect, or parivartana) among '
    'the lords of houses 1/2/5/9/11 where the pair includes the 2nd or 11th lord, '
    'and the meeting house is not a dusthana (6/8/12).',
    '{}'::jsonb,
    'Wealth accumulation, resource command; strength/demotion depends on the '
    'constituent lords'' freedom from combustion/uncancelled debility.',
    '{"rule": "lord_combust_or_debilitated_without_nbry_demotes_or_cancels"}'::jsonb,
    '[{"text_id": "bphs", "chapter": "Ch.41 Dhana Yoga adhyaya"}]'::jsonb,
    'parashari', false
),
(
    'raja_yoga_kendra_trikona', 'Kendra-Trikoṇa (Detector) Rāja Yoga', 'Raja Yoga (Kendra-Trikona Detector)',
    'raja',
    '{"detector": "raja_yoga_kendra_trikona"}'::jsonb,
    'Any kendra lord (1/4/7/10) associated (conjunction/mutual aspect/parivartana) '
    'with any trikona lord (1/5/9), with a mandatory affliction check on both lords.',
    '{}'::jsonb,
    'Authority, status, sustained rise — subject to demotion if either lord is '
    'combust or uncancelled-debilitated.',
    '{"rule": "lord_combust_or_debilitated_without_nbry_demotes_or_cancels"}'::jsonb,
    '[{"text_id": "bphs", "chapter": "Ch.39 Raja Yoga adhyaya"}]'::jsonb,
    'parashari', false
),
(
    'sarasvati_yoga', 'Sarasvatī (Detector) Yoga', 'Sarasvati Yoga (Detector)',
    'other',
    '{"detector": "sarasvati_yoga"}'::jsonb,
    'Jupiter, Venus, and Mercury each placed in a kendra, trikona, or the 2nd house, '
    'with Jupiter in its own or exaltation sign. (The classical "or friendly sign" '
    'disjunct on Jupiter''s dignity is not evaluated here — no ratified '
    'planetary-friendship table exists in this writer; honest floor, not fabrication.)',
    '{}'::jsonb,
    'Learning, eloquence, the arts — cancelled if any constituent graha is '
    'debilitated or combust.',
    '{"rule": "any_constituent_debilitated_or_combust_cancels"}'::jsonb,
    '[{"text_id": "bphs", "chapter": "Ch.75 (Nabhasa/compound yoga treatment)"}]'::jsonb,
    'parashari', false
),
(
    'vipareeta_raja_yoga', 'Viparīta Rāja (Detector) Yoga', 'Vipareeta Raja Yoga (Detector)',
    'raja',
    '{"detector": "vipareeta_raja_yoga"}'::jsonb,
    'A dusthana lord (6th/8th/12th) placed in a dusthana (own house included), with '
    'a mandatory dilution check: conjunction/aspect by a non-dusthana lord, or an '
    'exalted-in-dusthana nuance, dilutes (does not silently cancel) the effect.',
    '{}'::jsonb,
    '"Poison cures poison" — reversal fortune from affliction; diluted, not voided, '
    'when a non-dusthana lord associates with the dusthana lord.',
    '{"rule": "conjunct_or_aspected_by_non_dusthana_lord_or_exalted_in_dusthana_dilutes"}'::jsonb,
    '[{"text_id": "phaladeepika", "chapter": "Ch.7 Raja Yoga"}]'::jsonb,
    'parashari', false
),
(
    'budha_aditya', 'Budhāditya (fallback seed)', 'Budha-Aditya Yoga (fallback seed)',
    'other',
    '{"requires": [{"relation": "sun_mercury_conjunct"}, {"condition": "mercury_not_too_combust"}]}'::jsonb,
    'Sun and Mercury conjunct in one house, Mercury not deeply combust.',
    '{}'::jsonb,
    'Intellect, communication.',
    '{"rule": "mercury_combust_cancels"}'::jsonb,
    '[{"text_id": "bphs", "chapter": "Budha-Aditya treatment"}]'::jsonb,
    'parashari', false
),
(
    'lakshmi_yoga', 'Lakṣmī (fallback seed)', 'Lakshmi Yoga (fallback seed)',
    'dhana',
    '{"requires": [{"relation": "9th_lord_own_or_exalted_in_kendra_trikona"}]}'::jsonb,
    '9th lord own/exalted in a kendra/trikona, with Venus strong.',
    '{}'::jsonb,
    'Fortune, prosperity.',
    '{"rule": "venus_debilitated_or_combust_cancels"}'::jsonb,
    '[{"text_id": "bphs", "chapter": "Dhana/Raja Yoga treatment"}]'::jsonb,
    'parashari', false
)
ON CONFLICT (canonical_id) DO NOTHING;

COMMIT;
