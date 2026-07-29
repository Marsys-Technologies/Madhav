-- Migration 472: bg_synthetic_cohort — synthetic reference cohort (ṢAḌ-DARŚANA item 22)
-- =============================================================================
-- Context: SHAD_DARSHANA_BRIEF_v2_0.md §2 file map ("bg_cohort.py — synthetic reference
-- cohort (global; L0 idempotency = upsert)") + §1 item 22 ("Synthetic reference cohort
-- (~10⁴⁺) + matched sub-cohort (E7.3)"). This migration creates ONLY the table + its
-- asset_registry row; the ~10,000 synthetic rows themselves are computed and written by
-- the bg_cohort writer (pipeline/orchestrator/writers/bg_cohort.py) at build time, NOT
-- inline here — unlike small static reference tables (e.g. migration 431's
-- bg_sign_medical), this table's content is a large deterministic pyswisseph computation,
-- not a hand-curated classical corpus, so it belongs in the writer, not the migration.
--
-- What this table is FOR: a statistical base-rate population of synthetic (NOT real)
-- birth charts' graha + Lagna sidereal positions (Lahiri ayanamsha), used by a LATER wave
-- (W2, item 15 "Rarity axis from cohort" + KALA_SUPREME_ELEVATION_v1_0.md §12.3's matched
-- sub-cohort) to answer "how often does configuration X happen across a broad population."
-- This migration and its writer build ONLY the cohort table — no rarity scoring, no
-- matched sub-cohort, no consumer of this table ships here (explicitly out of scope per
-- the ṢAḌ-DARŚANA brief's bg_cohort task boundary).
--
-- Sampling methodology (documented in full in bg_cohort.py's module docstring — summary
-- here for anyone reading the schema without the writer open): N=10,000 synthetic birth
-- instants, uniform-random over 1900-01-01..2099-12-31 (200y — enough Jupiter/Saturn/
-- Rahu-Ketu cycles to populate all signs/nakshatras with usable density) with a FIXED RNG
-- seed for reproducibility; birth lat uniform [-60,+60] (verified zero Placidus-house
-- failures in this band; ±90 breaks down near the polar circles), lon uniform
-- [-180,+180]; Lahiri ayanamsha only (the project's primary/canonical ayanamsha). ZERO
-- LLM use — pure pyswisseph + seeded stdlib `random`, a deterministic transform per
-- CLAUDE.md §N.4. A failed per-row Ascendant computation is stored as an honest JSONB
-- null (never a fabricated stub) per CLAUDE.md §N.7.
--
-- Idempotency (§N.3 — L0 = global reference, safe to upsert): ON CONFLICT (synthetic_id)
-- DO NOTHING in the writer — the fixed seed makes every rebuild recompute byte-identical
-- rows, so PRIMARY KEY on synthetic_id + DO NOTHING is correct and sufficient (mirrors
-- bg_ephemeris's convention exactly).
--
-- Nirmāṇa build-tracker contract (brief §2.5): this is one of the four new `bg_*` assets
-- (bg_cohort, bg_sky_calendar, bg_muhurta_lattice, bg_parihara_rules) that build ONLY via
-- an explicit super-admin L0 trigger — never auto-pulled into a per-chart build. A
-- per-chart build whose L0 upstream (this table) is dormant correctly shows any future
-- dependent as blocked, per §2.5.2.
-- =============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS bg_synthetic_cohort (
    id                    BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    synthetic_id          INTEGER     NOT NULL,
    birth_datetime_utc    TIMESTAMPTZ NOT NULL,
    birth_lat             NUMERIC(7,4) NOT NULL CHECK (birth_lat BETWEEN -90 AND 90),
    birth_lon             NUMERIC(7,4) NOT NULL CHECK (birth_lon BETWEEN -180 AND 180),
    ayanamsha_key         TEXT        NOT NULL DEFAULT 'lahiri',
    -- positions: {"Sun": {sidereal_longitude, sign_id, sign, nakshatra_id, nakshatra,
    --             nakshatra_pada, is_retrograde}, "Moon": {...}, ..., "Lagna": {...}}
    -- 10 keys: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu, Lagna.
    positions             JSONB       NOT NULL,
    sampling_method       TEXT        NOT NULL,
    source_citation       TEXT        NOT NULL,
    build_id              UUID,
    computed_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT bg_synthetic_cohort_synthetic_id_key UNIQUE (synthetic_id)
);

CREATE INDEX IF NOT EXISTS idx_bg_synthetic_cohort_positions_gin
    ON bg_synthetic_cohort USING GIN (positions);

COMMENT ON TABLE bg_synthetic_cohort IS
  'ṢAḌ-DARŚANA item 22: synthetic (NOT real-person) reference cohort of ~10,000 birth '
  'charts'' Lahiri-sidereal graha+Lagna positions (sign/nakshatra grain only, no '
  'divisional charts, no dashas) — a statistical base-rate population for later rarity/ '
  'matched-sub-cohort scoring (W2). Populated by pipeline/orchestrator/writers/'
  'bg_cohort.py; sampling methodology documented in that writer''s module docstring.';

COMMENT ON COLUMN bg_synthetic_cohort.synthetic_id IS
  'Deterministic sequence 1..N from the fixed-seed sampler — the natural key for '
  'ON CONFLICT DO NOTHING upsert idempotency (§N.3).';
COMMENT ON COLUMN bg_synthetic_cohort.positions IS
  'JSONB map of 10 grahas/Lagna → {sidereal_longitude, sign_id, sign, nakshatra_id, '
  'nakshatra, nakshatra_pada, is_retrograde}. Lahiri ayanamsha only.';

-- asset_registry row (Nirmāṇa build-tracker contract, brief §2.5.1 — seed row lands in
-- the SAME PR as the writer). scope='global' (L0, not per-chart); count_sql counts ALL
-- rows (no chart_id — this is not a chart-scoped asset).
INSERT INTO asset_registry (
    asset_id, layer, sort_order,
    sanskrit_name, english_name, english_description,
    storage_type, target_table, count_sql, size_sql,
    target_floor, expected_volume_formula, expected_volume_inputs, volume_explanation,
    depends_on, scope, is_active, has_writer,
    layer_name, layer_index, catalog_status, asset_kind
) VALUES (
    'bg_cohort', 'brahmagyan', 20,
    'Pratirūpa Samūha', 'Synthetic Reference Cohort',
    'Synthetic (not real-person) reference population of ~10,000 birth charts'' '
    'Lahiri-sidereal graha + Lagna positions (sign/nakshatra grain) — the statistical '
    'base-rate population later waves compare a real chart against for rarity scoring. '
    'ṢAḌ-DARŚANA campaign item 22.',
    'postgres_table', 'bg_synthetic_cohort',
    'SELECT COUNT(*) FROM bg_synthetic_cohort', 'SELECT pg_total_relation_size(''bg_synthetic_cohort'')',
    10000, 'COHORT_SIZE', '{"COHORT_SIZE": 10000}'::jsonb,
    '10,000 synthetic birth charts, uniform-random over 1900-2099, fixed RNG seed. '
    'See bg_cohort.py module docstring for full sampling methodology.',
    ARRAY[]::text[], 'global', true, true,
    'Brahmagyan', 'L0', 'CURRENT', 'data'
) ON CONFLICT (asset_id) DO UPDATE SET
    count_sql            = EXCLUDED.count_sql,
    target_table         = EXCLUDED.target_table,
    has_writer            = EXCLUDED.has_writer,
    english_description   = EXCLUDED.english_description,
    target_floor          = EXCLUDED.target_floor,
    expected_volume_formula = EXCLUDED.expected_volume_formula,
    expected_volume_inputs  = EXCLUDED.expected_volume_inputs,
    volume_explanation      = EXCLUDED.volume_explanation;

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   DELETE FROM asset_registry WHERE asset_id = 'bg_cohort';
--   DROP TABLE IF EXISTS bg_synthetic_cohort;
--   COMMIT;
-- =============================================================================
