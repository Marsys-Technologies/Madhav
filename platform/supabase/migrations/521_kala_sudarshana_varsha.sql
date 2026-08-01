-- migration 521: kala_sudarshana_varsha + the `ka_sudarshana_varsha` asset_registry seed row
-- =============================================================================
-- ṢAḌ-DARŚANA campaign · Wave W3 · Lane w3-kota-sudarshana. Registry item 17:
-- Sudarśana-Chakra year-wheel triple-lagna progression.
-- Spec: SHAD_DARSHANA_BRIEF_v2_0.md §1 item 17.
--
-- ── BINDING NAMING RULING (do not revisit) ───────────────────────────────────
-- `bo_sudarshana` (L2 Bodha, migration-era pre-existing, `bodha_msr_signals`
-- table) is a CONFIRMED namesake-only collision: it computes a STATIC
-- per-graha tri-frame house position at build time, no time axis. This asset
-- (`ka_sudarshana_varsha`, L3 Kāla) PROGRESSES the three reference signs
-- (Janma/Chandra/Sūrya Lagna) forward year-by-year across a lifespan — a
-- genuinely different, temporal computation. Named `ka_sudarshana_varsha`,
-- never bare `sudarshana`, so the two remain permanently distinguishable in
-- registries and logs (Conductor ruling, recorded in SHAD_DARSHANA_STATE.md).
--
-- ── SCOPE (disclosed, not an oversight) ──────────────────────────────────────
-- This writer delivers the YEAR-WHEEL PROGRESSION ONLY (house 1 governs ages
-- 1/13/25/..., house 2 governs ages 2/14/26/..., cycling every 12 years). The
-- fuller classical "Sudarshana Chakra Dasha" sub-period structure (10-year
-- primary + yearly secondary sub-periods layered on this wheel) is NOT built
-- here — a materially larger, separate technique, and out of this item's
-- named scope ("the year-wheel triple-lagna progression technique").
--
-- ── IDEMPOTENCY (§N.3) ───────────────────────────────────────────────────────
-- Per-chart delete-then-insert, scoped to (chart_id, ayanamsha_id,
-- varsha_year) — a rebuild replaces the full 120-year wheel, never accretes.
-- =============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS kala_sudarshana_varsha (
  id                        BIGSERIAL PRIMARY KEY,
  chart_id                  UUID NOT NULL,
  ayanamsha_id              TEXT NOT NULL DEFAULT 'lahiri_chitrapaksha',
  varsha_year               SMALLINT NOT NULL CHECK (varsha_year BETWEEN 1 AND 120),
  window_start              DATE NOT NULL,
  window_end                DATE NOT NULL,
  jl_natal_sign_idx         SMALLINT NOT NULL CHECK (jl_natal_sign_idx BETWEEN 0 AND 11),
  cl_natal_sign_idx         SMALLINT NOT NULL CHECK (cl_natal_sign_idx BETWEEN 0 AND 11),
  sl_natal_sign_idx         SMALLINT NOT NULL CHECK (sl_natal_sign_idx BETWEEN 0 AND 11),
  jl_active_sign_idx        SMALLINT NOT NULL CHECK (jl_active_sign_idx BETWEEN 0 AND 11),
  cl_active_sign_idx        SMALLINT NOT NULL CHECK (cl_active_sign_idx BETWEEN 0 AND 11),
  sl_active_sign_idx        SMALLINT NOT NULL CHECK (sl_active_sign_idx BETWEEN 0 AND 11),
  jl_active_sign_name       TEXT NOT NULL,
  cl_active_sign_name       TEXT NOT NULL,
  sl_active_sign_name       TEXT NOT NULL,
  tri_lagna_convergence     BOOLEAN NOT NULL,
  lagna_fact_id             TEXT NOT NULL,
  moon_fact_id              TEXT NOT NULL,
  sun_fact_id               TEXT NOT NULL,
  formula_version           TEXT NOT NULL,
  computed_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT kala_sudarshana_varsha_natural_key
    UNIQUE (chart_id, ayanamsha_id, varsha_year),
  CONSTRAINT kala_sudarshana_varsha_window_order CHECK (window_end >= window_start)
);

CREATE INDEX IF NOT EXISTS idx_kala_sudarshana_varsha_lookup
  ON kala_sudarshana_varsha (chart_id, window_start, window_end);

COMMENT ON TABLE kala_sudarshana_varsha IS
  'ṢAḌ-DARŚANA W3 item 17: Sudarśana-Chakra year-wheel. One row per varsha '
  'year (1..120, full lifespan) per chart, progressing Janma/Chandra/Sūrya '
  'Lagna forward one sign per year of life, cycling every 12 years. '
  'tri_lagna_convergence flags a classically notable year where all three '
  'active signs coincide. Year-wheel progression ONLY — the fuller '
  'Sudarshana Chakra Dasha sub-period structure is out of scope (see '
  'services/ka_sudarshana_varsha/logic.py docstring).';

-- ── asset_registry seed row for `ka_sudarshana_varsha` (Nirmāṇa contract
-- §2.5.1: seed row lands in the SAME PR as the writer) ───────────────────────

INSERT INTO asset_registry (
    asset_id, layer, sort_order,
    sanskrit_name, english_name, english_description,
    storage_type, target_table, count_sql, size_sql,
    target_floor, scope, is_active, has_writer, has_substeps,
    writer_timeout_seconds,
    layer_name, layer_index, catalog_status, asset_kind,
    depends_on
) VALUES (
    'ka_sudarshana_varsha',
    'kala',
    121,
    'Sudarśana-Cakra Varṣa',
    'Sudarśana-Chakra Year-Wheel',
    'ṢAḌ-DARŚANA W3 item 17: the rotating annual house-per-year progression '
    'of the tri-lagna framework (Janma/Chandra/Sūrya Lagna), full 120-year '
    'lifespan. Pure arithmetic over natal chart_facts (ga_positions) — no '
    'ephemeris calls. Named ka_sudarshana_varsha (never bare sudarshana) per '
    'the campaign''s binding ruling distinguishing it from the unrelated L2 '
    'bo_sudarshana static tri-frame signal writer (namesake-only collision).',
    'postgres_table', 'kala_sudarshana_varsha',
    'SELECT COUNT(*) FROM kala_sudarshana_varsha WHERE chart_id=$1',
    'SELECT pg_total_relation_size(''kala_sudarshana_varsha'')',
    0, 'per_chart', true, true, false,
    60,
    'Kāla', 'L3', 'CURRENT', 'data',
    ARRAY['ga_positions']::text[]
) ON CONFLICT (asset_id) DO UPDATE SET
    count_sql               = EXCLUDED.count_sql,
    size_sql                = EXCLUDED.size_sql,
    target_table            = EXCLUDED.target_table,
    has_writer              = EXCLUDED.has_writer,
    has_substeps            = EXCLUDED.has_substeps,
    writer_timeout_seconds  = EXCLUDED.writer_timeout_seconds,
    sort_order              = EXCLUDED.sort_order,
    scope                   = EXCLUDED.scope,
    is_active               = EXCLUDED.is_active,
    sanskrit_name           = EXCLUDED.sanskrit_name,
    english_name            = EXCLUDED.english_name,
    english_description     = EXCLUDED.english_description,
    depends_on              = EXCLUDED.depends_on;

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   DELETE FROM asset_registry WHERE asset_id = 'ka_sudarshana_varsha';
--   DROP TABLE IF EXISTS kala_sudarshana_varsha;
--   COMMIT;
-- =============================================================================
