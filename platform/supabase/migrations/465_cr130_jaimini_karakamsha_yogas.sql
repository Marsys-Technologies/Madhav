-- Migration 465: SARVA-SIDDHI W-4 / CR-130 — Jaimini Karakāṃśa yoga catalog seed.
--
-- WHY THIS EXISTS
-- ===============
-- The 7 Jaimini karakāṃśa planet yogas (sun/moon/mars/jupiter/venus/saturn/rahu)
-- are DEFINED in the L0 code catalog (platform/python-sidecar/brahmagyan/
-- l0_yogas.py, YOGAS_CORE §3.7, canonical_ids jaimini_karakamsha_*), but this
-- DB was seeded by bg_yogas BEFORE those inline rows were added — so
-- brahma_yoga_catalog currently holds ZERO school='jaimini' rows (verified live
-- 2026-07-24). Their absence is the root of CR-130's dark-flag: no catalog row,
-- no firing surface, no coverage. bg_yogas.seed_yogas uses
-- ON CONFLICT (canonical_id) DO NOTHING, so a re-seed would only ever touch a
-- fresh L0 build — the deployed estate needs a surgical, idempotent migration
-- (§N.4 surgical-migrations-only). This migration is that surgical seed.
--
-- The NEW firing DETECTOR (the L1 half of CR-130) lives in ga_yoga_writer.py
-- (_build_karakamsha_firings): D1-rāśi occupation of the karakāṃśa sign OR
-- Jaimini chara-rāśi-dṛṣṭi (sign aspect) onto it, reading the karakāṃśa sign
-- from chart_facts (fact_category='karakamsa_position', KARAKAMSA/sign — written
-- by ga_sensitive_writer, §N.5 L1-authority; the detector never recomputes the
-- Ātmakāraka or its navāṃśa sign). This migration only makes the catalog rows
-- present so the firing rows' yoga_canonical_id resolves to a described,
-- cited catalog entry on the serving surfaces (ganita_yogas_get / firings_get).
--
-- VALUES ARE VERBATIM from l0_yogas.py YOGAS_CORE §3.7 (no drift): if bg_yogas
-- is ever re-run, ON CONFLICT DO NOTHING makes both paths agree.
--
-- canonical_id is the PRIMARY KEY (migration 176). ON CONFLICT (canonical_id)
-- DO NOTHING → idempotent AND non-destructive. Additive-only: no ALTERs.

BEGIN;

INSERT INTO brahma_yoga_catalog (
    canonical_id, name_sa, name_en, category, formation_rule_jsonb,
    formation_text, significations_jsonb, significations_text,
    cancellation_conditions, classical_citations, school, rare
) VALUES
(
    'jaimini_karakamsha_sun', 'Karakāṃśa Sūrya Yoga', 'Jaimini Karakamsha Sun Yoga',
    'raja',
    '{"requires": [{"planet": "sun", "house": ["karakamsha_lagna"], "or_aspect": true}]}'::jsonb,
    'Sun in or aspecting the Karakamsha lagna.',
    '{"gives": ["government_service", "authority", "royal_employment"], "subcategory": "jaimini_raja"}'::jsonb,
    'Government service, employment by royalty or authority.',
    '{}'::jsonb,
    '[{"text_id": "jaimini_sutram"}]'::jsonb,
    'jaimini', false
),
(
    'jaimini_karakamsha_moon', 'Karakāṃśa Candra Yoga', 'Jaimini Karakamsha Moon Yoga',
    'dhana',
    '{"requires": [{"planet": "moon", "house": ["karakamsha_lagna"], "or_aspect": true}]}'::jsonb,
    'Moon in or aspecting the Karakamsha lagna.',
    '{"gives": ["government_work", "trade_in_liquids", "agriculture"], "subcategory": "jaimini_dhana"}'::jsonb,
    'Trading in liquids, agricultural pursuits, employment under authority.',
    '{}'::jsonb,
    '[{"text_id": "jaimini_sutram"}]'::jsonb,
    'jaimini', false
),
(
    'jaimini_karakamsha_mars', 'Karakāṃśa Kuja Yoga', 'Jaimini Karakamsha Mars Yoga',
    'other',
    '{"requires": [{"planet": "mars", "house": ["karakamsha_lagna"], "or_aspect": true}]}'::jsonb,
    'Mars in or aspecting the Karakamsha lagna.',
    '{"gives": ["engineering", "weapons", "fire_related_work", "valor"], "subcategory": "jaimini"}'::jsonb,
    'Works with weapons, fire or metals; valorous.',
    '{}'::jsonb,
    '[{"text_id": "jaimini_sutram"}]'::jsonb,
    'jaimini', false
),
(
    'jaimini_karakamsha_jupiter', 'Karakāṃśa Guru Yoga', 'Jaimini Karakamsha Jupiter Yoga',
    'raja',
    '{"requires": [{"planet": "jupiter", "house": ["karakamsha_lagna"], "or_aspect": true}]}'::jsonb,
    'Jupiter in or aspecting the Karakamsha lagna.',
    '{"gives": ["vedic_learning", "dharma", "eloquence", "royal_favour"], "subcategory": "jaimini_raja"}'::jsonb,
    'Learned in the Vedas, eloquent, pious, favoured by rulers.',
    '{}'::jsonb,
    '[{"text_id": "jaimini_sutram"}]'::jsonb,
    'jaimini', false
),
(
    'jaimini_karakamsha_venus', 'Karakāṃśa Śukra Yoga', 'Jaimini Karakamsha Venus Yoga',
    'dhana',
    '{"requires": [{"planet": "venus", "house": ["karakamsha_lagna"], "or_aspect": true}]}'::jsonb,
    'Venus in or aspecting the Karakamsha lagna.',
    '{"gives": ["luxury", "wealth", "marital_happiness", "arts"], "subcategory": "jaimini_dhana"}'::jsonb,
    'Wealthy, enjoys luxury, marital happiness, skill in arts.',
    '{}'::jsonb,
    '[{"text_id": "jaimini_sutram"}]'::jsonb,
    'jaimini', false
),
(
    'jaimini_karakamsha_saturn', 'Karakāṃśa Śani Yoga', 'Jaimini Karakamsha Saturn Yoga',
    'other',
    '{"requires": [{"planet": "saturn", "house": ["karakamsha_lagna"], "or_aspect": true}]}'::jsonb,
    'Saturn in or aspecting the Karakamsha lagna.',
    '{"gives": ["labour", "iron_works", "service_industry", "austerity"], "subcategory": "jaimini"}'::jsonb,
    'Laborious work, service, iron or machinery trades.',
    '{}'::jsonb,
    '[{"text_id": "jaimini_sutram"}]'::jsonb,
    'jaimini', false
),
(
    'jaimini_karakamsha_rahu', 'Karakāṃśa Rāhu Yoga', 'Jaimini Karakamsha Rahu Yoga',
    'other',
    '{"requires": [{"planet": "rahu", "house": ["karakamsha_lagna"]}]}'::jsonb,
    'Rahu in the Karakamsha lagna.',
    '{"gives": ["technical_skill", "foreign_elements", "deception_or_cunning"], "subcategory": "jaimini"}'::jsonb,
    'Technical, foreign, or unconventional profession; possibly deceptive.',
    '{}'::jsonb,
    '[{"text_id": "jaimini_sutram"}]'::jsonb,
    'jaimini', false
)
ON CONFLICT (canonical_id) DO NOTHING;

COMMIT;
