-- Migration 387: brahma_class_priors table + bg_class_priors registry (BA-P3A Step 1)
-- Source authority: BEYOND_ACHARYA_W1_JUDGMENT_SEED_PACKAGE_v1_0.md §2 + §3 + §4 (graha×domain).
-- Stores the 4 prior axes read by composite_ranker.ts at query time.
--
-- Row encoding:
--   Class-axis:     (prior_version, signal_type_class, '*', '*', '*',  class_prior)
--   Subsystem-axis: (prior_version, '*', '*', source_subsystem, '*',   class_prior)
--   Tradition-axis: (prior_version, '*', '*', '*', signal_tradition,   class_prior)
--   Varga-axis:     (prior_version, 'varga', D<n>, '*', '*',           class_prior, varga_weights=domain overlays)
--   Graha×domain:   (prior_version, 'graha_domain', <graha>, <domain>, '*', class_prior)
--
-- Idempotency: L0 = ON CONFLICT DO UPDATE (global, not per-chart).

BEGIN;

-- ── DDL ──────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS brahma_class_priors (
    prior_version       TEXT        NOT NULL,
    signal_type_class   TEXT        NOT NULL,
    fact_kind           TEXT        NOT NULL,
    source_subsystem    TEXT        NOT NULL,
    signal_tradition    TEXT        NOT NULL,
    class_prior         NUMERIC     NOT NULL CHECK (class_prior > 0),
    varga_weights       JSONB,
    contested           BOOLEAN     NOT NULL DEFAULT false,
    citation            TEXT,
    ratified_by         TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT brahma_class_priors_pk
      PRIMARY KEY (prior_version, signal_type_class, fact_kind, source_subsystem, signal_tradition)
);

COMMENT ON TABLE brahma_class_priors IS
  'BA-P3A: Ranked salience class-prior weights (versioned). '
  'Axes: signal_type_class × source_subsystem × signal_tradition × varga × graha×domain. '
  'Priors v1.0 seeded from BEYOND_ACHARYA_W1_JUDGMENT_SEED_PACKAGE_v1_0.md §2-§4. '
  'Composite formula: class_prior = w(class) × w(subsystem) × w(tradition); varga overlay applied at query time.';

-- ── §2.1 — signal_type_class weights (11 classes) ───────────────────────────

INSERT INTO brahma_class_priors
  (prior_version, signal_type_class, fact_kind, source_subsystem, signal_tradition, class_prior, contested, citation, ratified_by)
VALUES
  ('1.0', 'configuration',   '*', '*', '*', 1.40, false, 'BPHS yoga/phala chapters — yogas are the headline structures', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0', 'yoga',            '*', '*', '*', 1.40, false, 'Alias for configuration; same classical authority',             'W1_SEED_PACKAGE_v1_0'),
  ('1.0', 'relationship',    '*', '*', '*', 1.20, false, 'Parivartana/argala/aspects: chart wiring; BPHS bhava chapters', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0', 'position',        '*', '*', '*', 1.10, false, 'Atomic backbone — graha in sign/house/dignity; BPHS',          'W1_SEED_PACKAGE_v1_0'),
  ('1.0', 'dasha_period',    '*', '*', '*', 1.15, false, 'Timing is half of Jyotish; period lord condition is first-class', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0', 'time_window',     '*', '*', '*', 0.95, false, 'Derived timing; slightly below period itself',                  'W1_SEED_PACKAGE_v1_0'),
  ('1.0', 'birth_moment',    '*', '*', '*', 1.05, false, 'Foundational panchanga; BPHS tithi/vara/nakshatra chapters',    'W1_SEED_PACKAGE_v1_0'),
  ('1.0', 'annual',          '*', '*', '*', 0.85, false, 'Varshaphala/tajika — powerful but tradition-scoped',            'W1_SEED_PACKAGE_v1_0'),
  ('1.0', 'medical',         '*', '*', '*', 0.90, false, 'Domain-specific; high within health, humble elsewhere',         'W1_SEED_PACKAGE_v1_0'),
  ('1.0', 'vastu',           '*', '*', '*', 0.70, false, 'Environmental/remedial; genuinely peripheral to natal judgment','W1_SEED_PACKAGE_v1_0'),
  ('1.0', 'prashna',         '*', '*', '*', 1.00, false, 'Only fires on prashna charts; gated by chart_type',             'W1_SEED_PACKAGE_v1_0'),
  ('1.0', 'absence',         '*', '*', '*', 0.80, false, 'Absent yoga is real evidence; weaker than a present one',       'W1_SEED_PACKAGE_v1_0'),
  ('1.0', 'composite_state', '*', '*', '*', 1.20, false, 'Multi-system structural composite; equivalent to relationship',  'W1_SEED_PACKAGE_v1_0'),
  ('1.0', 'karaka_alignment','*', '*', '*', 1.05, false, 'Karaka congruence; between position and structural level',      'W1_SEED_PACKAGE_v1_0'),
  ('1.0', 'parivartana',     '*', '*', '*', 1.20, false, 'Exchange of signs — equivalent to relationship class',          'W1_SEED_PACKAGE_v1_0'),
  ('1.0', 'varga_pattern',   '*', '*', '*', 0.95, false, 'Vargottama/varga structure; above birth_moment, below position','W1_SEED_PACKAGE_v1_0'),
  ('1.0', 'magnitude',       '*', '*', '*', 1.00, false, 'Bala/strength scores; modulates delivery; baseline',            'W1_SEED_PACKAGE_v1_0')
ON CONFLICT (prior_version, signal_type_class, fact_kind, source_subsystem, signal_tradition)
DO UPDATE SET class_prior = EXCLUDED.class_prior, citation = EXCLUDED.citation, ratified_by = EXCLUDED.ratified_by;

-- ── §2.2 — source_subsystem weights (12 values) ─────────────────────────────

INSERT INTO brahma_class_priors
  (prior_version, signal_type_class, fact_kind, source_subsystem, signal_tradition, class_prior, citation, ratified_by)
VALUES
  ('1.0', '*', '*', 'structural',           '*', 1.00, 'Baseline structural provenance', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0', '*', '*', 'dasha',                '*', 1.10, 'Dasha-sourced: timing premium',  'W1_SEED_PACKAGE_v1_0'),
  ('1.0', '*', '*', 'yoga',                 '*', 1.15, 'Yoga-sourced: formation premium','W1_SEED_PACKAGE_v1_0'),
  ('1.0', '*', '*', 'strength_ashtakavarga','*', 0.95, 'AV bindus; useful but supplementary', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0', '*', '*', 'nakshatra',            '*', 1.05, 'Nakshatra-sourced: lunar layer',  'W1_SEED_PACKAGE_v1_0'),
  ('1.0', '*', '*', 'sensitive',            '*', 1.00, 'Sensitive points: parity with structural', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0', '*', '*', 'varga',               '*', 1.00, 'Varga-sourced: varga-grain weight does real work', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0', '*', '*', 'tajaka',              '*', 0.85, 'Tajaka/varshaphala: tradition-scoped',             'W1_SEED_PACKAGE_v1_0'),
  ('1.0', '*', '*', 'sade_sati',           '*', 1.05, 'Sade Sati: significant transit pattern',           'W1_SEED_PACKAGE_v1_0'),
  ('1.0', '*', '*', 'panchanga',           '*', 0.90, 'Panchanga-sourced: birth-moment quality',          'W1_SEED_PACKAGE_v1_0'),
  ('1.0', '*', '*', 'medical',             '*', 0.90, 'Medical subsystem: domain-gated relevance',        'W1_SEED_PACKAGE_v1_0'),
  ('1.0', '*', '*', 'vastu',               '*', 0.70, 'Vastu: environmental; peripheral to natal',        'W1_SEED_PACKAGE_v1_0')
ON CONFLICT (prior_version, signal_type_class, fact_kind, source_subsystem, signal_tradition)
DO UPDATE SET class_prior = EXCLUDED.class_prior, citation = EXCLUDED.citation, ratified_by = EXCLUDED.ratified_by;

-- ── §2.3 — signal_tradition weights (6 schools) ─────────────────────────────

INSERT INTO brahma_class_priors
  (prior_version, signal_type_class, fact_kind, source_subsystem, signal_tradition, class_prior, citation, ratified_by)
VALUES
  ('1.0', '*', '*', '*', 'parashari', 1.00, 'BPHS spine — canonical Parashara tradition', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0', '*', '*', '*', 'jaimini',   0.95, 'Jaimini Sutram — strong but method-specific', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0', '*', '*', '*', 'kp',        0.90, 'KP Reader system', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0', '*', '*', '*', 'tajika',    0.85, 'Tajika/Persian-Arabic system',                 'W1_SEED_PACKAGE_v1_0'),
  ('1.0', '*', '*', '*', 'nadi',      0.80, 'Bhrigu-Nandi/Nadi-Navamsa — powerful but method-sensitive', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0', '*', '*', '*', 'lal_kitab', 0.70, 'Lal Kitab — folk tradition; lowest classical authority',      'W1_SEED_PACKAGE_v1_0')
ON CONFLICT (prior_version, signal_type_class, fact_kind, source_subsystem, signal_tradition)
DO UPDATE SET class_prior = EXCLUDED.class_prior, citation = EXCLUDED.citation, ratified_by = EXCLUDED.ratified_by;

-- ── §3.1 + §3.2 — Varga base weights + domain overlays ──────────────────────
-- fact_kind encodes the varga key (D1, D9, etc.)
-- varga_weights JSONB: {domain: multiplier} where multiplier overrides base at query time.
-- D1 base=1.00; overlay career×1.5, health×1.5, relationship×1.5, character×1.5 (BPHS).

INSERT INTO brahma_class_priors
  (prior_version, signal_type_class, fact_kind, source_subsystem, signal_tradition, class_prior, varga_weights, citation, ratified_by)
VALUES
  -- Shodasavarga (16 classical Parashara vargas) — Vimshopaka source: BPHS vimshopaka-bala chapter
  ('1.0','varga','D1', '*','*', 1.00,
    '{"career":1.5,"health":1.5,"relationship":1.5,"character":1.5}',
    'BPHS Vimshopaka: D1=3.5/max; D1-overlay career/health/relat./char.', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','varga','D2', '*','*', 0.45,
    '{"wealth":1.5}',
    'BPHS Vimshopaka: D2=1.0; Hora=wealth', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','varga','D3', '*','*', 0.45, NULL,
    'BPHS Vimshopaka: D3=1.0; Drekkana; no specific domain overlay', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','varga','D4', '*','*', 0.30,
    '{"residence":1.5,"family":1.5}',
    'BPHS Vimshopaka: D4=0.5; Chaturthamsha=property/fortune; family/residence overlay', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','varga','D5', '*','*', 0.18, NULL, 'Supplementary varga (not in Shodasavarga); floor weight', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','varga','D6', '*','*', 0.18, NULL, 'Supplementary varga; floor weight', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','varga','D7', '*','*', 0.30,
    '{"progeny":1.5}',
    'BPHS Vimshopaka: D7=0.5; Saptamsha=children', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','varga','D8', '*','*', 0.18, NULL, 'Supplementary varga; floor weight', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','varga','D9', '*','*', 0.90,
    '{"relationship":1.5,"progeny":1.5,"education":1.5,"character":1.5}',
    'BPHS Vimshopaka: D9=3.0; Navamsha=spouse/dharma — highest after D1', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','varga','D10','*','*', 0.55,
    '{"career":1.5}',
    'D10 lifted: 0.5→0.55 (BPHS base) + career overlay; modern practice weights Dashamsha for profession', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','varga','D11','*','*', 0.18, NULL, 'Supplementary varga; floor weight', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','varga','D12','*','*', 0.32,
    '{"family":1.5}',
    'BPHS Vimshopaka: D12=0.5; Dvadashamsha=parents/lineage', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','varga','D14','*','*', 0.18, NULL, 'Supplementary varga; floor weight', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','varga','D15','*','*', 0.18, NULL, 'Supplementary varga; floor weight', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','varga','D16','*','*', 0.60,
    '{"character":1.5}',
    'BPHS Vimshopaka: D16=2.0; Shodashamsha=comforts/temperament', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','varga','D20','*','*', 0.35,
    '{"spirituality":1.5}',
    'BPHS Vimshopaka: D20=0.5; Vimshamsha=worship/upasana', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','varga','D21','*','*', 0.18, NULL, 'Supplementary varga; floor weight', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','varga','D24','*','*', 0.30,
    '{"education":1.5}',
    'BPHS Vimshopaka: D24=0.5; Siddhamsha=learning/education', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','varga','D27','*','*', 0.30, NULL, 'BPHS Vimshopaka: D27=0.5; Bhamsha', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','varga','D30','*','*', 0.45,
    '{"health":1.5}',
    'BPHS Vimshopaka: D30=1.0; Trimshamsha=evils/afflictions/health', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','varga','D32','*','*', 0.18, NULL, 'Supplementary varga; floor weight', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','varga','D33','*','*', 0.18, NULL, 'Supplementary varga; floor weight', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','varga','D40','*','*', 0.28, NULL, 'BPHS Vimshopaka: D40=0.5; Khavedamsha', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','varga','D45','*','*', 0.28, NULL, 'BPHS Vimshopaka: D45=0.5; Akshavedamsha', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','varga','D50','*','*', 0.18, NULL, 'Supplementary varga; floor weight', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','varga','D54','*','*', 0.18, NULL, 'Supplementary varga; floor weight', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','varga','D60','*','*', 0.95,
    '{"spirituality":1.5}',
    'BPHS Vimshopaka: D60=4.0 (Parashara: foremost); spirituality overlay; time-sensitive', 'W1_SEED_PACKAGE_v1_0'),
  -- Nadi vargas
  ('1.0','varga','D108', '*','*', 0.12, NULL, 'Nadi varga; present-queryable; floor weight only', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','varga','D150', '*','*', 0.12, NULL, 'Nadi varga; floor weight', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','varga','D2700','*','*', 0.12, NULL, 'Nadi varga; floor weight', 'W1_SEED_PACKAGE_v1_0')
ON CONFLICT (prior_version, signal_type_class, fact_kind, source_subsystem, signal_tradition)
DO UPDATE SET class_prior = EXCLUDED.class_prior, varga_weights = EXCLUDED.varga_weights,
              citation = EXCLUDED.citation, ratified_by = EXCLUDED.ratified_by;

-- ── §4 — Graha × Domain affinity matrix ─────────────────────────────────────
-- signal_type_class='graha_domain', fact_kind=<graha>, source_subsystem=<domain>, signal_tradition='*'
-- class_prior = the graha×domain affinity multiplier.
-- Source: BPHS karaka chapter + Jaimini chara-karaka + standard bhava-karaka assignments.

INSERT INTO brahma_class_priors
  (prior_version, signal_type_class, fact_kind, source_subsystem, signal_tradition, class_prior, citation, ratified_by)
VALUES
  -- Sun affinities
  ('1.0','graha_domain','SU','career',       '*', 1.40, 'BPHS: Sun=10th-house natural significator, king/authority karaka', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','SU','wealth',        '*', 1.00, 'BPHS: Sun=dhana only indirectly', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','SU','relationship',  '*', 0.80, 'Sun is separative for 7th-house matters', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','SU','progeny',       '*', 0.90, 'Sun=3rd/5th only weakly', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','SU','health',        '*', 1.10, 'Sun=vitality/longevity (with 1st lord)', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','SU','education',     '*', 1.00, 'Sun=education moderately', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','SU','family',        '*', 1.10, 'Sun=father karaka (BPHS)', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','SU','residence',     '*', 0.90, 'Sun=residence weakly', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','SU','travel',        '*', 0.90, 'Sun=travel weakly', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','SU','spirituality',  '*', 1.00, 'Sun=dharma moderately', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','SU','character',     '*', 1.10, 'Sun=self/soul/atma', 'W1_SEED_PACKAGE_v1_0'),
  -- Moon affinities
  ('1.0','graha_domain','MO','career',        '*', 1.00, 'Moon=career neutrally', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','MO','wealth',        '*', 1.00, 'Moon=wealth neutrally', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','MO','relationship',  '*', 1.10, 'Moon=emotional bond, 7th affinity', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','MO','progeny',       '*', 1.00, 'Moon=progeny moderately', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','MO','health',        '*', 1.10, 'Moon=mind-body, fluids', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','MO','education',     '*', 1.00, 'Moon=education moderately', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','MO','family',        '*', 1.30, 'Moon=mother karaka (BPHS, strongest)', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','MO','residence',     '*', 1.00, 'Moon=residence moderately', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','MO','travel',        '*', 1.00, 'Moon=travel moderately', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','MO','spirituality',  '*', 1.00, 'Moon=spirituality moderately', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','MO','character',     '*', 1.40, 'Moon=mind/temperament karaka — strongest character significator', 'W1_SEED_PACKAGE_v1_0'),
  -- Mars affinities
  ('1.0','graha_domain','MA','career',        '*', 1.20, 'Mars=military/technical career, 10th signification', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','MA','wealth',        '*', 1.00, 'Mars=wealth neutrally', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','MA','relationship',  '*', 1.00, 'Mars=energy in relationship; Manglik watch', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','MA','progeny',       '*', 0.90, 'Mars=progeny weakly', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','MA','health',        '*', 1.20, 'Mars=surgery/accident/blood (BPHS 6/8 lords)', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','MA','education',     '*', 0.90, 'Mars=technical skill not broad education', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','MA','family',        '*', 1.00, 'Mars=siblings (3rd house)', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','MA','residence',     '*', 1.40, 'Mars=bhumi-karaka (land/property) strongest', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','MA','travel',        '*', 1.00, 'Mars=travel moderately', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','MA','spirituality',  '*', 0.90, 'Mars=spiritual weakly', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','MA','character',     '*', 1.10, 'Mars=courage/aggression aspect of character', 'W1_SEED_PACKAGE_v1_0'),
  -- Mercury affinities
  ('1.0','graha_domain','ME','career',        '*', 1.20, 'Mercury=commerce/communication career', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','ME','wealth',        '*', 1.20, 'Mercury=commerce/trade wealth (BPHS)', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','ME','relationship',  '*', 1.00, 'Mercury=relationship neutrally (contracts)', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','ME','progeny',       '*', 1.00, 'Mercury=intellect/progeny moderately', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','ME','health',        '*', 1.00, 'Mercury=nervous system moderately', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','ME','education',     '*', 1.40, 'Mercury=vidya-karaka — education karaka (Jaimini)', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','ME','family',        '*', 1.00, 'Mercury=family neutrally', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','ME','residence',     '*', 0.90, 'Mercury=residence weakly', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','ME','travel',        '*', 1.10, 'Mercury=short journeys/3rd house', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','ME','spirituality',  '*', 1.00, 'Mercury=spirituality moderately', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','ME','character',     '*', 1.20, 'Mercury=intellect/discrimination aspect of character', 'W1_SEED_PACKAGE_v1_0'),
  -- Jupiter affinities
  ('1.0','graha_domain','JU','career',        '*', 1.10, 'Jupiter=authority/guru/law career', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','JU','wealth',        '*', 1.30, 'Jupiter=dhana-karaka (BPHS wealth significator)', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','JU','relationship',  '*', 1.10, 'Jupiter=vivaha significator (Jaimini DK)', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','JU','progeny',       '*', 1.50, 'Jupiter=putra-karaka — STRONGEST progeny significator', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','JU','health',        '*', 1.00, 'Jupiter=health moderately (liver/fat)', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','JU','education',     '*', 1.30, 'Jupiter=higher learning/guru/jnana-karaka', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','JU','family',        '*', 1.10, 'Jupiter=pitri/family broadly', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','JU','residence',     '*', 1.00, 'Jupiter=residence moderately', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','JU','travel',        '*', 1.00, 'Jupiter=long-distance pilgrimage travel', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','JU','spirituality',  '*', 1.40, 'Jupiter=dharma-karaka; jnana/moksha significator', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','JU','character',     '*', 1.10, 'Jupiter=wisdom/expansion aspect of character', 'W1_SEED_PACKAGE_v1_0'),
  -- Venus affinities
  ('1.0','graha_domain','VE','career',        '*', 1.00, 'Venus=arts/beauty career moderately', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','VE','wealth',        '*', 1.20, 'Venus=luxury/material wealth (BPHS)', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','VE','relationship',  '*', 1.50, 'Venus=kalatra-karaka — STRONGEST spouse/partner significator', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','VE','progeny',       '*', 1.20, 'Venus=arts/creative progeny', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','VE','health',        '*', 1.00, 'Venus=health moderately (reproductive)', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','VE','education',     '*', 1.00, 'Venus=arts education moderately', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','VE','family',        '*', 1.00, 'Venus=family moderately', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','VE','residence',     '*', 1.20, 'Venus=vehicles/comforts/home luxury (4th signification)', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','VE','travel',        '*', 1.00, 'Venus=travel moderately', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','VE','spirituality',  '*', 0.90, 'Venus=spirituality weakly (worldly attachment)', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','VE','character',     '*', 1.10, 'Venus=refinement/aesthetics aspect of character', 'W1_SEED_PACKAGE_v1_0'),
  -- Saturn affinities
  ('1.0','graha_domain','SA','career',        '*', 1.40, 'Saturn=karma-karaka — STRONGEST career significator (10th house)', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','SA','wealth',        '*', 1.00, 'Saturn=wealth neutrally (delays gains)', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','SA','relationship',  '*', 0.90, 'Saturn=relationship with difficulty/delay', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','SA','progeny',       '*', 0.80, 'Saturn=progeny weakly (reduces/delays)', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','SA','health',        '*', 1.20, 'Saturn=chronic illness/ayushkaraka (longevity)', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','SA','education',     '*', 0.90, 'Saturn=technical mastery but slow learning', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','SA','family',        '*', 0.90, 'Saturn=family with difficulty/loss', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','SA','residence',     '*', 1.20, 'Saturn=labor/land/property maintenance', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','SA','travel',        '*', 1.00, 'Saturn=travel moderately', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','SA','spirituality',  '*', 1.10, 'Saturn=vairagya/renunciation aspect', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','SA','character',     '*', 1.00, 'Saturn=discipline/endurance aspect of character', 'W1_SEED_PACKAGE_v1_0'),
  -- Rahu affinities
  ('1.0','graha_domain','RA','career',        '*', 1.10, 'Rahu=unconventional/technical career', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','RA','wealth',        '*', 1.10, 'Rahu=speculation/sudden wealth', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','RA','relationship',  '*', 0.90, 'Rahu=unconventional/cross-cultural relationship', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','RA','progeny',       '*', 0.80, 'Rahu=progeny weakly', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','RA','health',        '*', 1.00, 'Rahu=mysterious ailments moderately', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','RA','education',     '*', 1.00, 'Rahu=education moderately', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','RA','family',        '*', 0.80, 'Rahu=family disruption', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','RA','residence',     '*', 1.00, 'Rahu=residence moderately', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','RA','travel',        '*', 1.40, 'Rahu=foreign lands/distant travel (BPHS 12th/9th)', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','RA','spirituality',  '*', 1.10, 'Rahu=maya; unconventional spiritual path', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','RA','character',     '*', 1.00, 'Rahu=character moderately', 'W1_SEED_PACKAGE_v1_0'),
  -- Ketu affinities
  ('1.0','graha_domain','KE','career',        '*', 0.90, 'Ketu=career disruption/technical but scattered', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','KE','wealth',        '*', 0.90, 'Ketu=wealth with loss/renunciation', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','KE','relationship',  '*', 0.80, 'Ketu=relationship weakly (isolation tendency)', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','KE','progeny',       '*', 0.80, 'Ketu=progeny weakly (reduces)', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','KE','health',        '*', 1.10, 'Ketu=occult ailments/mysterious health factors', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','KE','education',     '*', 1.00, 'Ketu=education moderately (esoteric)', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','KE','family',        '*', 0.90, 'Ketu=family weakly', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','KE','residence',     '*', 0.90, 'Ketu=residence weakly', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','KE','travel',        '*', 1.10, 'Ketu=pilgrimage/spiritual travel', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','KE','spirituality',  '*', 1.50, 'Ketu=moksha-karaka — STRONGEST spiritual significator', 'W1_SEED_PACKAGE_v1_0'),
  ('1.0','graha_domain','KE','character',     '*', 1.10, 'Ketu=detachment/past-karma aspect of character', 'W1_SEED_PACKAGE_v1_0')
ON CONFLICT (prior_version, signal_type_class, fact_kind, source_subsystem, signal_tradition)
DO UPDATE SET class_prior = EXCLUDED.class_prior, varga_weights = EXCLUDED.varga_weights,
              citation = EXCLUDED.citation, ratified_by = EXCLUDED.ratified_by;

-- ── asset_registry row ───────────────────────────────────────────────────────

INSERT INTO asset_registry (
    asset_id, layer, sort_order,
    sanskrit_name, english_name, english_description,
    storage_type, target_table, count_sql, size_sql,
    target_floor, scope, is_active,
    layer_name, layer_index, catalog_status
)
VALUES (
    'bg_class_priors',
    'brahmagyan',
    16,
    'Pūrva-pakṣa-mānāḥ',
    'Class Priors',
    'Ranked salience class-prior weights for composite query-time ranking. '
    '4 axes: signal_type_class × source_subsystem × signal_tradition × varga × graha×domain. '
    'Seeded from W1 judgment package v1.0; versioned; L5-calibratable.',
    'postgres_table',
    'brahma_class_priors',
    'SELECT COUNT(*) FROM brahma_class_priors',
    'SELECT pg_total_relation_size(''brahma_class_priors'')',
    NULL,
    'global',
    true,
    'Brahmagyan',
    'L0',
    'CURRENT'
)
ON CONFLICT (asset_id) DO UPDATE SET
    english_name        = EXCLUDED.english_name,
    english_description = EXCLUDED.english_description,
    count_sql           = EXCLUDED.count_sql,
    layer_name          = EXCLUDED.layer_name,
    layer_index         = EXCLUDED.layer_index,
    catalog_status      = EXCLUDED.catalog_status;

UPDATE asset_registry SET has_writer = true WHERE asset_id = 'bg_class_priors';

COMMIT;
