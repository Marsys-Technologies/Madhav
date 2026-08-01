-- migration 531: kala_tithi_pravesha + the `ka_tithi_pravesha` asset_registry seed row
-- (renumbered from 530 -> 531: 530 raced with `shad-darshana/w4-lane-r-yajna-setu`'s
-- `530_bg_muhurta_lattice_panchangika_families.sql`, an independent unmerged lane —
-- migration-collision rail, both branches re-verified live max at the same moment)
-- =============================================================================
-- ṢAḌ-DARŚANA campaign · Wave W3 · Lane w3-tithi-pravesha. Registry item 13:
-- Tithi-Praveśa (lunar-return annual chart).
-- Spec: SHAD_DARSHANA_BRIEF_v2_0.md §1 item 13 (one-line registry entry; no
-- deeper spec doc — design derived from established Jyotiṣa doctrine per the
-- item's own name, matching the codebase's closest precedent, `ga_tajaka`
-- Vārṣaphala/solar-return machinery, see services/ka_tithi_pravesha/logic.py
-- module docstring for the full derivation).
--
-- ── THE TECHNIQUE (disclosed derivation, not fabricated — B.10) ──────────────
-- Tithi-Praveśa is the lunar-return counterpart to Tājika Vārṣaphala (the
-- solar-return annual chart already built by `ga_tajaka`, L1): the praveśa
-- ("entry") year begins at the instant the transiting Moon returns to its
-- EXACT natal sidereal longitude nearest each solar-birthday anniversary, and
-- the annual chart is cast for that instant (same "annual-return chart"
-- pattern as `ga_tajaka`, anchored on the Moon instead of the Sun — see
-- CLAUDECODE task brief item 13 and KALA_TRANSFORMATION_HANDOFF_v1_0.md's own
-- glossary entry: "Tithi-Praveśa (annual lunar-return chart)"). Natal Moon
-- longitude is read VERBATIM from chart_facts (§N.5 — L1 is the authority,
-- never re-derived independently).
--
-- ── SCOPE (disclosed, not an oversight) ──────────────────────────────────────
-- This writer delivers the RETURN-INSTANT + ANNUAL-CHART CAST ONLY (Praveśa
-- Lagna + full graha positions at the lunar-return instant) — the fuller
-- Tājika-specific apparatus (Muntha, Vārṣeśa candidate scoring, the five
-- Tajik yogas) is Vārṣaphala-specific machinery already built by `ga_tajaka`
-- and is NOT re-derived here; no codebase-attested classical source treats
-- that apparatus as part of Tithi-Praveśa specifically. `classical_source_
-- citation` is honestly `not_in_corpus` — no primary-source chapter/verse for
-- Tithi-Praveśa is ingested in this corpus; an ingestion work item is filed,
-- not fabricated (§N.7 item 6 / B.3).
--
-- ── IDEMPOTENCY (§N.3) ───────────────────────────────────────────────────────
-- Per-chart delete-then-insert, scoped to (chart_id, ayanamsha_id,
-- pravesha_year) — a rebuild replaces the full 120-year window, never accretes.
-- =============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS kala_tithi_pravesha (
  id                        BIGSERIAL PRIMARY KEY,
  chart_id                  UUID NOT NULL,
  ayanamsha_id              TEXT NOT NULL DEFAULT 'lahiri_chitrapaksha',
  pravesha_year             SMALLINT NOT NULL CHECK (pravesha_year BETWEEN 1 AND 120),
  window_start              TIMESTAMPTZ NOT NULL,
  window_end                TIMESTAMPTZ NOT NULL,
  start_converged           BOOLEAN NOT NULL,
  end_converged             BOOLEAN NOT NULL,
  pravesha_lagna_sign_idx   SMALLINT CHECK (pravesha_lagna_sign_idx BETWEEN 0 AND 11),
  pravesha_lagna_sign_name  TEXT,
  pravesha_lagna_degree     DOUBLE PRECISION,
  graha_positions_jsonb     JSONB NOT NULL,
  natal_moon_longitude_deg  DOUBLE PRECISION NOT NULL,
  moon_fact_id              TEXT NOT NULL,
  ephemeris_audit_jsonb     JSONB NOT NULL,
  verification_pass_status  TEXT NOT NULL CHECK (verification_pass_status IN ('two_pass_verified', 'divergent_flagged')),
  classical_source_citation TEXT NOT NULL,
  formula_version           TEXT NOT NULL,
  computed_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT kala_tithi_pravesha_natural_key
    UNIQUE (chart_id, ayanamsha_id, pravesha_year),
  CONSTRAINT kala_tithi_pravesha_window_order CHECK (window_end > window_start),
  CONSTRAINT kala_tithi_pravesha_lagna_consistency
    CHECK (
      (pravesha_lagna_sign_idx IS NULL AND pravesha_lagna_sign_name IS NULL)
      OR (pravesha_lagna_sign_idx IS NOT NULL AND pravesha_lagna_sign_name IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_kala_tithi_pravesha_lookup
  ON kala_tithi_pravesha (chart_id, window_start, window_end);

COMMENT ON TABLE kala_tithi_pravesha IS
  'ṢAḌ-DARŚANA W3 item 13: Tithi-Praveśa (lunar-return annual chart), the '
  'Moon-anchored counterpart to Tājika Vārṣaphala (ga_tajaka, solar-return). '
  'One row per praveśa year (1..120, full lifespan) per chart: the instant '
  'the transiting Moon returns to its exact natal sidereal longitude nearest '
  'that solar-birthday anniversary, plus the annual chart (Praveśa Lagna + '
  'graha positions) cast for that instant. Return-instant + chart-cast ONLY '
  '— the Tājika-specific Muntha/Vārṣeśa/yoga apparatus is Vārṣaphala-only and '
  'out of scope here (see services/ka_tithi_pravesha/logic.py docstring).';

-- ── asset_registry seed row for `ka_tithi_pravesha` (Nirmāṇa contract
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
    'ka_tithi_pravesha',
    'kala',
    124,
    'Tithi-Praveśa',
    'Tithi-Praveśa (Lunar-Return Annual Chart)',
    'ṢAḌ-DARŚANA W3 item 13: the lunar-return counterpart to Tājika Vārṣaphala '
    '(ga_tajaka) — the annual chart cast for the instant the transiting Moon '
    'returns to its exact natal sidereal longitude nearest each solar-birthday '
    'anniversary, full 120-year lifespan. Real Swiss-Ephemeris-backed root-find '
    '(pyjhora_adapter, the same engine ga_tajaka uses) + full annual-chart cast '
    '(Praveśa Lagna + graha positions). Natal Moon longitude read verbatim from '
    'chart_facts (ga_positions), never re-derived.',
    'postgres_table', 'kala_tithi_pravesha',
    'SELECT COUNT(*) FROM kala_tithi_pravesha WHERE chart_id=$1',
    'SELECT pg_total_relation_size(''kala_tithi_pravesha'')',
    0, 'per_chart', true, true, false,
    120,
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
--   DELETE FROM asset_registry WHERE asset_id = 'ka_tithi_pravesha';
--   DROP TABLE IF EXISTS kala_tithi_pravesha;
--   COMMIT;
-- =============================================================================
