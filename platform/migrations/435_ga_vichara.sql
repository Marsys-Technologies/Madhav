-- Migration 435: ga_vichara — new L1 asset "judged structure"
-- Doctrine Campaign D-1 / Night-1, Lane 2.
-- Design ref: DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §4 (deltas 1-2), §8 (leverage_index),
-- §11 (ratification_factor). Brief: 00_ARCHITECTURE/llm_consumption_audit/briefs/night1/LANE2_GA_VICHARA.md
--
-- MIGRATION-DIRECTORY FINDING (flagged per Night-1 conductor instructions):
-- platform/scripts/migrate.ts::collectMigrationFiles() reads BOTH
-- platform/migrations/*.sql AND platform/supabase/migrations/*.sql, then merges
-- and sorts the combined list by filename before applying. Both directories are
-- therefore simultaneously "live" for the actual runner (not just one canonical
-- dir) even though the create-migration skill only documents platform/migrations/
-- numbering. Highest number in platform/migrations/ was 367 (Lane 4, this
-- campaign); highest in platform/supabase/migrations/ was 434 (Lane 3, this same
-- campaign) — i.e. two sibling lanes picked numbers independently in two
-- directories in the SAME night, which is exactly the collision risk this
-- comment exists to flag for a reconciliation pass (the two-directory split
-- itself is pre-existing, not introduced here). This file uses 435 — the
-- lowest unused number across BOTH directories — placed in platform/migrations/
-- per the create-migration skill's documented convention.
--
-- SCHEMA-SHAPE FINDING (flagged, not silently resolved): two sibling lanes
-- already merged code that consumes chart_vichara with two DIFFERENT column
-- vocabularies for the same rows:
--   - Lane 4 (platform/python-sidecar/pipeline/orchestrator/writers/bo_laksana.py)
--     queries: subject, domain, ratification_factor (varga_ratification);
--     actor, target, varga, value_text, value_num (valence_pass);
--     subject, domain, value_text, value_num, constituent_facts_array (divergence).
--   - Lane 5 (platform/src/lib/retrieval/registry/layers/L1_ganita/get_vichara.ts)
--     queries: id, chart_id, ayanamsha_id, build_id, vichara_family, subject,
--     domain, varga_id, value_num, value_text, value_jsonb, constituent_fact_ids,
--     formula_version, source_citation, computed_at.
-- Per this lane's anti-scope, Lane 4/5 code is NOT touched. This migration
-- creates the UNION of both vocabularies so both already-merged consumers work
-- unmodified: varga_id AND varga are both populated (same value); constituent_fact_ids
-- AND constituent_facts_array are both populated (same array); actor/target are
-- populated for valence_pass rows (actor also mirrored into subject so Lane 5's
-- generic subject filter still finds valence_pass rows); ratification_factor is
-- a dedicated column mirroring value_num for varga_ratification rows. This is a
-- reconciliation-pending duplication, not a design endorsement — flagged for a
-- follow-up pass to pick ONE vocabulary and migrate both consumers onto it.

BEGIN;

CREATE TABLE IF NOT EXISTS chart_vichara (
  id                      BIGSERIAL PRIMARY KEY,
  chart_id                UUID NOT NULL,
  ayanamsha_id            TEXT NOT NULL,
  build_id                UUID,
  vichara_family          TEXT NOT NULL
    CHECK (vichara_family IN ('valence_pass', 'varga_ratification',
                               'varga_ratification_divergence', 'varga_consistency',
                               'leverage_index')),
  subject                 TEXT NOT NULL,       -- graha/lord/karaka identifier, UPPERCASE (chart_facts.fact_subject convention)
  actor                   TEXT,                -- valence_pass: acting graha (mirrors subject)
  target                  TEXT,                -- valence_pass: target house/lord identifier
  domain                  TEXT,                -- nullable; wealth/career/marriage/health/general
  varga_id                TEXT,                -- nullable; e.g. 'D1','D9' (Lane 5 vocabulary)
  varga                   TEXT,                -- nullable; same value as varga_id (Lane 4 vocabulary)
  value_num               NUMERIC,
  value_text              TEXT,
  value_jsonb             JSONB,
  ratification_factor     NUMERIC,             -- varga_ratification rows only; mirrors value_num; CHECK below
  constituent_fact_ids    TEXT[] DEFAULT ARRAY[]::TEXT[],   -- Lane 5 vocabulary; matches chart_facts.fact_id (TEXT)
  constituent_facts_array TEXT[] DEFAULT ARRAY[]::TEXT[],   -- Lane 4 vocabulary; same contents as constituent_fact_ids
  formula_version         TEXT,
  source_citation         TEXT,
  computed_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT chart_vichara_ratification_factor_range
    CHECK (ratification_factor IS NULL OR (ratification_factor >= 0.6 AND ratification_factor <= 1.4))
);

CREATE INDEX IF NOT EXISTS idx_chart_vichara_chart_ayanamsha
  ON chart_vichara (chart_id, ayanamsha_id);

CREATE INDEX IF NOT EXISTS idx_chart_vichara_family_domain
  ON chart_vichara (chart_id, vichara_family, domain);

CREATE INDEX IF NOT EXISTS idx_chart_vichara_subject
  ON chart_vichara (chart_id, subject);

-- ── L0 constants table (design §11: "registry data, not literals") ─────────

CREATE TABLE IF NOT EXISTS brahma_vichara_constants (
  constant_key  TEXT PRIMARY KEY,
  value_jsonb   JSONB NOT NULL,
  citation      TEXT,
  version       TEXT NOT NULL,
  updated_at    TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO brahma_vichara_constants (constant_key, value_jsonb, citation, version) VALUES
(
  'ratification_step',
  '0.2'::jsonb,
  'DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §11',
  'v1'
),
(
  'ratification_clamp',
  '{"lo": 0.6, "hi": 1.4}'::jsonb,
  'DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §11',
  'v1'
),
(
  'operative_vargas',
  '{
     "wealth":   {"vargas": ["D1","D2","D9","D11"], "provisional": false, "houses": [2,11], "karaka": "Jupiter"},
     "career":   {"vargas": ["D1","D10","D9"],       "provisional": true,  "houses": [10],   "karaka": "Saturn"},
     "marriage": {"vargas": ["D1","D9","D7"],        "provisional": true,  "houses": [7],    "karaka": "Venus"},
     "health":   {"vargas": ["D1","D6","D9"],        "provisional": true,  "houses": [6],    "karaka": "Saturn"},
     "general":  {"vargas": ["D1","D9"],             "provisional": true,  "houses": [1],    "karaka": "Sun"}
   }'::jsonb,
  'DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §11 (wealth design-ratified; others provisional pending native review)',
  'v1'
),
(
  'valence_matrix',
  '{
     "dusthana_lord_wealth_or_lagna":  {"value_text": "strong_malefic", "value_num": -1.0, "citation": "BPHS Ch.31/39 — dusthana (6/8/12) lordship afflicting the wealth axis (2/11) or lagna; CR-54 type specimen (8L Mars -> H2)."},
     "dusthana_lord_other":            {"value_text": "malefic",        "value_num": -0.5, "citation": "BPHS dusthana lordship doctrine (non-anchor extension of the CR-54 anchor cell)."},
     "trikona_lord_benefic_target":    {"value_text": "benefic",        "value_num":  0.5, "citation": "BPHS Ch.34/35 — trikona (1/5/9) lordship is inherently auspicious wherever it lands in kendra/trikona/dhana houses."},
     "trikona_lord_yogakaraka":        {"value_text": "strong_benefic", "value_num":  1.0, "citation": "BPHS yogakaraka doctrine — trikona lord that is ALSO a stored yogakaraka (graha_functional_class_per_ascendant)."},
     "maraka":                         {"value_text": "malefic",        "value_num": -0.5, "citation": "BPHS Ch.44 — maraka (2nd/7th lord) doctrine."},
     "upachaya_lord":                  {"value_text": "benefic",        "value_num":  0.5, "citation": "BPHS upachaya (3/6/10/11) growth-house doctrine — mildly benefic."},
     "kendra_lord_neutral":            {"value_text": "neutral",        "value_num":  0.0, "citation": "ambiguous_default — kendradhipatya dosha tempers kendra (4/7/10, non-trikona) lordship to neutral rather than assigning an unratified sign."},
     "ambiguous_default":              {"value_text": "neutral",        "value_num":  0.0, "citation": "ambiguous_default — no matrix anchor cell matched; B.10 floor (never invent a strong value)."}
   }'::jsonb,
  'DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §4 delta 1 / CR-54 (amended, §I.1)',
  'v1'
),
(
  'dignity_score_map',
  '{"exalted": 1.0, "own": 0.75, "neutral": 0.5, "debilitated": 0.25}'::jsonb,
  'DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §8. NOTE: L1 chart_facts graha_dignity_per_varga only stores {exalted, own, neutral, debilitated} (no mooltrikona/friend/enemy granularity) — the brief''s richer 7-tier scale is not populated because the underlying L1 fact does not carry that distinction (B.10: no new computation to backfill it); known_gap logged per-row in value_jsonb.',
  'v1'
),
(
  'leverage_weights',
  '{"lordship": 1.0, "karakatva": 0.75, "occupancy": 0.5, "yoga_participation": 0.75, "capability_floor": 0.1,
    "runway_base": 1.0, "runway_scale": 0.5, "runway_duration_norm_years": 20, "runway_start_horizon_years": 15,
    "runway_lookforward_years": 30,
    "domain_yoga_keywords": {"wealth": ["DHANA"], "career": ["RAJA"], "marriage": [], "health": [], "general": ["RAJA"]}}'::jsonb,
  'DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §8 (CR-69/CR-60)',
  'v1'
),
(
  'consistency_weights',
  '{"w_sign": 0.5, "w_dignity": 0.5}'::jsonb,
  'DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §4 delta 2',
  'v1'
)
ON CONFLICT (constant_key) DO NOTHING;

-- ── asset_registry entry ────────────────────────────────────────────────────
-- Real column set verified against platform/supabase/migrations/167_asset_registry.sql
-- + 240_ga_yoga.sql (has_substeps added upstream of 240) + 342_asset_registry_writer_flags.sql
-- (has_writer). depends_on is TEXT[], layer is the internal 'ganita' code (not 'L1').

INSERT INTO asset_registry (
    asset_id, layer, sort_order, sanskrit_name, english_name, english_description,
    storage_type, target_table, count_sql, size_sql, target_floor,
    expected_volume_formula, volume_explanation, depends_on, scope, is_active,
    has_substeps, has_writer
) VALUES (
    'ga_vichara',
    'ganita',
    29,
    'Vichāra',
    'Gaṇita — Vichāra (judged structure)',
    'Judgment layer over ga_structural: functional-lordship valence pass, varga-ratification matrix + divergence signals, continuous varga-consistency index, and leverage_index (remedy/intervention-timing rank).',
    'postgres_table',
    'chart_vichara',
    'SELECT COUNT(*) FROM chart_vichara WHERE chart_id = $1',
    'SELECT pg_total_relation_size(''chart_vichara'')',
    0,
    'GRAHAS x DOMAINS x AYANAMSHAS_COUNT (approx; families vary)',
    'Sum of valence_pass + varga_ratification (+ divergence) + varga_consistency + leverage_index rows across 5 ayanamshas',
    ARRAY['ga_structural', 'ga_strength', 'ga_dashas', 'ga_yoga']::text[],
    'per_chart',
    true,
    true,
    true
) ON CONFLICT (asset_id) DO UPDATE SET
    english_name = EXCLUDED.english_name,
    english_description = EXCLUDED.english_description,
    depends_on = EXCLUDED.depends_on,
    count_sql = EXCLUDED.count_sql,
    target_floor = EXCLUDED.target_floor,
    sort_order = EXCLUDED.sort_order,
    is_active = EXCLUDED.is_active,
    has_substeps = EXCLUDED.has_substeps,
    has_writer = EXCLUDED.has_writer;

COMMIT;
