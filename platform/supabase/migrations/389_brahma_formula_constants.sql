-- Migration 389: brahma_formula_constants (bg_formula_constants) — BA-P3A Step 1
-- Source authority: BEYOND_ACHARYA_W1_JUDGMENT_SEED_PACKAGE_v1_0.md §7 (constants ratification sheet).
-- Classes: CLASSICAL (cite, encode exactly, never tune) | NATIVE_JUDGMENT (versioned, L5-calibratable)
--          | ENGINEERING (document) | CONFLATION_BUG (document, fix at source — do NOT seed)
-- Idempotency: L0 = ON CONFLICT DO UPDATE.

BEGIN;

-- ── DDL ──────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS brahma_formula_constants (
    constant_id             TEXT        PRIMARY KEY,
    value_jsonb             JSONB       NOT NULL,
    class                   TEXT        NOT NULL CHECK (class IN ('classical','native_judgment','engineering','conflation_bug')),
    consumer_assets         TEXT[]      NOT NULL DEFAULT '{}',
    citation_or_ratification TEXT       NOT NULL,
    calibratable            BOOLEAN     NOT NULL DEFAULT false,
    bounds                  JSONB,
    version                 TEXT        NOT NULL DEFAULT '1.0',
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE brahma_formula_constants IS
  'BA-P3A: Formula constants registry. '
  'CLASSICAL: cite-and-encode; never tune. NATIVE_JUDGMENT: ratified, versioned, L5-calibratable within bounds. '
  'ENGINEERING: document only. CONFLATION_BUG: document; fix at source, never seed. '
  'Seeded from W1 seed package §7. consumer_assets[] lists which layer assets READ this constant.';

-- ── §7 SEED ──────────────────────────────────────────────────────────────────

INSERT INTO brahma_formula_constants
  (constant_id, value_jsonb, class, consumer_assets, citation_or_ratification, calibratable, bounds, version)
VALUES

  -- CLASSICAL: Combustion orbs (per-graha, direct + retrograde variants)
  -- Already correct in bg_combustion_orbs; this entry centralizes them for cross-consumer reads.
  ('combustion_orbs',
    '{"Moon":{"direct":12,"retrograde":12},"Mars":{"direct":17,"retrograde":15},"Mercury":{"direct":14,"retrograde":12},"Jupiter":{"direct":11,"retrograde":9},"Venus":{"direct":10,"retrograde":8},"Saturn":{"direct":15,"retrograde":12},"Rahu":{"direct":9,"retrograde":7},"Ketu":{"direct":9,"retrograde":7}}',
    'classical',
    ARRAY['ga_condition','ka_vighnakara','ph_sodhana'],
    'Sārāvalī ch.6 / BPHS ch.3 (combustion-degrees per graha). Moon=12 classical; Mars=17/15 d/r; Merc=14/12; Jup=11/9; Ven=10/8; Sat=15/12; Rahu/Ketu=9/7. Already in bg_combustion_orbs; ka_vighnakara must read from here rather than flat 6° (BA_MASTER C12).',
    false,
    NULL,
    '1.0'),

  -- NATIVE_JUDGMENT: Obstruction severity thresholds
  ('obstruction_severity_thresholds',
    '{"severe":0.70,"moderate":0.40,"mild":0.15}',
    'native_judgment',
    ARRAY['ka_vighnakara','ph_sodhana'],
    'W1_SEED_PACKAGE_v1_0 §7: ratified at 0.70/0.40/0.15 (severe/moderate/mild); aligned to house-strength convention.',
    true,
    '{"severe":[0.60,0.80],"moderate":[0.30,0.50],"mild":[0.10,0.25]}',
    '1.0'),

  -- NATIVE_JUDGMENT: LEL magnitude tiers (5 levels; align to phala_anchors.magnitude)
  ('magnitude_tiers',
    '{"life_altering":0.90,"major":0.70,"significant":0.50,"moderate":0.30,"trivial":0.10}',
    'native_judgment',
    ARRAY['ph_nimitta','ph_pramana','mi_outcome'],
    'W1_SEED_PACKAGE_v1_0 §7: ratified at 5-tier scale; aligns LEL magnitude labels to numeric floors. phala_anchors.magnitude enum source.',
    true,
    '{"life_altering":[0.80,0.95],"major":[0.60,0.80],"significant":[0.40,0.60],"moderate":[0.20,0.40],"trivial":[0.05,0.20]}',
    '1.0'),

  -- NATIVE_JUDGMENT: Dignity scores (0.0–1.0 scale for composite ranking)
  ('dignity_scores',
    '{"exalted":1.00,"moolatrikona":0.90,"own":0.80,"great_friend_sign":0.65,"friend_sign":0.55,"neutral_sign":0.45,"enemy_sign":0.30,"great_enemy_sign":0.20,"debilitated":0.10}',
    'native_judgment',
    ARRAY['ga_condition','composite_ranker'],
    'W1_SEED_PACKAGE_v1_0 §7: ratified dignity scale. Foundation: Shadbala dignity component (BPHS), normalized to 0–1. Already in ga_condition_writer.py DIGNITY_SCORES; this entry is canonical.',
    true,
    '{"all_bounds":"±0.05 per tier"}',
    '1.0'),

  -- NATIVE_JUDGMENT: House (bhava) weights for structural role
  ('house_weights',
    '{"1":1.15,"2":0.85,"3":1.00,"4":1.15,"5":1.20,"6":0.85,"7":1.15,"8":0.85,"9":1.20,"10":1.15,"11":1.00,"12":0.85,"note":"1 counts as both kendra and trikona"}',
    'native_judgment',
    ARRAY['ga_condition','composite_ranker'],
    'W1_SEED_PACKAGE_v1_0 §7: kendra(1,4,7,10)=1.15; trikona(1,5,9)=1.20 (1 counts as both); upachaya(3,6,11)=1.00; 2/8/12=0.85; 6/8/12 contextual (dusthana). Based on BPHS bhava-bala.',
    true,
    '{"all_bounds":"±0.10 per house class"}',
    '1.0'),

  -- NATIVE_JUDGMENT: Attention-budget split (head/dissent/tail percentage)
  ('attention_budget',
    '{"head_pct":70,"dissent_pct":20,"tail_pct":10,"description":"head=top-ranking signals for primary response; dissent=conflicting signals for honest acknowledgment; tail=weak signals for context"}',
    'native_judgment',
    ARRAY['assess_career','assess_relationship','assess_wealth','assess_health'],
    'W1_SEED_PACKAGE_v1_0 §7: ratified 70/20/10 (head/dissent/tail). Per-query-class tunable within [50-80]/[10-30]/[5-20]. Govern Doctrine §1.4 attention allocation.',
    true,
    '{"head_pct":[50,80],"dissent_pct":[10,30],"tail_pct":[5,20]}',
    '1.0'),

  -- NATIVE_JUDGMENT: Dasha score flag threshold (ka_sangam)
  ('dasha_score_flag_threshold',
    '{"threshold":0.30,"description":"ka_sangam convergence windows with dasha_score > 0.30 are flagged as active temporal windows"}',
    'native_judgment',
    ARRAY['ka_sangam'],
    'W1_SEED_PACKAGE_v1_0 §7: ratified at 0.30; move from inline code to registry.',
    true,
    '{"threshold":[0.20,0.40]}',
    '1.0'),

  -- NATIVE_JUDGMENT: mi_sambandha channel priors (Dirichlet base)
  ('mi_sambandha_channel_priors',
    '{"career":{"signal":0.40,"dasha":0.35,"transit":0.25},"relationship":{"signal":0.35,"dasha":0.40,"transit":0.25},"health":{"signal":0.40,"dasha":0.30,"transit":0.30},"wealth":{"signal":0.35,"dasha":0.35,"transit":0.30},"spirituality":{"signal":0.35,"dasha":0.35,"transit":0.30},"general":{"signal":0.40,"dasha":0.30,"transit":0.30}}',
    'native_judgment',
    ARRAY['mi_sambandha'],
    'W1_SEED_PACKAGE_v1_0 §7: Dirichlet base priors per domain for mi_sambandha channel attribution. L5 triangulation updates empirically.',
    true,
    '{"note":"Dirichlet alpha; each domain sum must = 1.00"}',
    '1.0'),

  -- NATIVE_JUDGMENT: mi_gunanaka divergence cap
  ('mi_gunanaka_divergence_cap',
    '{"cap":3.0,"description":"Maximum ratio between highest and lowest channel weight before normalization in mi_gunanaka"}',
    'native_judgment',
    ARRAY['mi_gunanaka'],
    'W1_SEED_PACKAGE_v1_0 §7: cap=3.0 (MIMAMSA_V2); prevents extreme outlier weights from dominating. Range [2,4].',
    true,
    '{"cap":[2.0,4.0]}',
    '1.0'),

  -- ENGINEERING: Holdout partition (MD5 mod 10)
  ('holdout_partition',
    '{"fraction":0.20,"method":"MD5(chart_id)::bigint % 10 >= 8","description":"20% holdout for calibration; chart_ids with MD5 mod 10 >= 8 are held out"}',
    'engineering',
    ARRAY['mi_outcome','mi_ledger'],
    'ENGINEERING: holdout partition is a data-split decision, not a classical constant. Keep=0.20 (20%). Method: MD5 hash of chart_id modulo 10.',
    false,
    NULL,
    '1.0'),

  -- CONFLATION_BUG: ka_sangam confidence=convergence (DOCUMENT ONLY; fix at source W4A)
  ('_bug_ka_sangam_confidence_conflation',
    '{"bug":"ka_sangam stores confidence as convergence score (0-1) but this field is not a prediction confidence — it is a dasha/transit alignment strength. These are different quantities.","fix":"W4A: separate convergence_strength from prediction_confidence in ka_sangam output","status":"OPEN"}',
    'conflation_bug',
    ARRAY[]::TEXT[],
    'W1_SEED_PACKAGE_v1_0 §7 BA_MASTER C10: CONFLATION-BUG — fix at source in W4A. Do NOT seed as a constant.',
    false,
    NULL,
    '1.0')

ON CONFLICT (constant_id)
DO UPDATE SET
    value_jsonb              = EXCLUDED.value_jsonb,
    class                    = EXCLUDED.class,
    consumer_assets          = EXCLUDED.consumer_assets,
    citation_or_ratification = EXCLUDED.citation_or_ratification,
    calibratable             = EXCLUDED.calibratable,
    bounds                   = EXCLUDED.bounds;

-- ── asset_registry row for bg_formula_constants ──────────────────────────────

INSERT INTO asset_registry (
    asset_id, layer, sort_order,
    sanskrit_name, english_name, english_description,
    storage_type, target_table, count_sql, size_sql,
    target_floor, scope, is_active,
    layer_name, layer_index, catalog_status
)
VALUES (
    'bg_formula_constants',
    'brahmagyan',
    18,
    'Sūtra-māna-kośaḥ',
    'Formula Constants',
    'Canonical formula constants registry — combustion orbs, obstruction thresholds, '
    'magnitude tiers, dignity scores, house weights, attention budget, and engineering constants. '
    'Classes: CLASSICAL (cite, never tune) | NATIVE_JUDGMENT (versioned, L5-calibratable) | ENGINEERING | CONFLATION_BUG.',
    'postgres_table',
    'brahma_formula_constants',
    'SELECT COUNT(*) FROM brahma_formula_constants WHERE class != ''conflation_bug''',
    'SELECT pg_total_relation_size(''brahma_formula_constants'')',
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

UPDATE asset_registry SET has_writer = true WHERE asset_id = 'bg_formula_constants';

COMMIT;
