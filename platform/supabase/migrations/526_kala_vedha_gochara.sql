-- migration 526: kala_vedha_gochara + the `ka_vedha_gochara` asset_registry seed row
-- =============================================================================
-- ṢAḌ-DARŚANA campaign · Wave W3 · Lane w3-moorti-vedha. Registry item 5:
-- Vedha application + REAL Sarvatobhadra grid (closes defect R-19).
-- Spec: SHAD_DARSHANA_BRIEF_v2_0.md §1 item 5.
--
-- Migration number: originally authored as 523 (next-allocatable per the
-- guard at that moment: 521 [w3-kota-sudarshana, merged PR #999] + 1 = 522,
-- claimed by this lane's own 522_kala_moorti_nirnaya.sql immediately prior,
-- so 523 for this file). RENUMBERED 523 -> 526 before this PR was opened —
-- see 525_kala_moorti_nirnaya.sql's header for the full account of the
-- three concurrent sibling-lane collisions this discovered and moved clear
-- of (522/523/524 all independently claimed elsewhere in the same window).
--
-- ── TWO DISTINCT VEDHA MECHANISMS, ONE TABLE, DISTINGUISHED BY `vedha_kind` ──
-- (§N.6 — never flatten differently-sourced rows into one undifferentiated
-- list). See services/ka_vedha_gochara/logic.py module docstring for the
-- full technical + citation detail on both:
--   'house_vedha'    — BPHS Ch.29 / Phaladeepika Ch.26 house-level Gochara
--                       vedha, from bg_transit_rules (migration 266, REAL,
--                       populated, cited). uncited_extension = false always.
--   'sarvatobhadra'  — the R-19 item. See the HONEST DISCLOSURE below.
--
-- ── R-19 HONEST DISCLOSURE (read this before assuming "grid" means a
-- populated 9x9 lookup table) ────────────────────────────────────────────────
-- This migration does NOT populate `l1_sarvatobhadra_positions` /
-- `l1_sarvatobhadra_vedha` (migration `_archive/140_sarvatobhadra_chakra.sql`)
-- with a primary-cited classical grid. Both a live check of the ingested
-- classical-text corpus (00_ARCHITECTURE/SOURCE_DATA/classical_texts/ — BPHS,
-- Jaimini Sutram, KP, KP_Reader only; no Muhurta Chintamani / Jyotish Sara
-- Sangraha text) and a search of this repository (confirmed: no INSERT into
-- either table anywhere) found no primary or responsibly-transcribable
-- secondary source for the SBC's specific 9x9 grid geometry this session —
-- unlike ka_kota_chakra's ring table, the SBC's grid layout genuinely varies
-- across regional Jyotish traditions, so no single specific grid_row/
-- grid_col assignment or 14-pair list could be committed here without
-- fabricating a "the" classical table where none could be verified (LAW
-- ZERO: honest-empty beats fabricated-full; B.10; DATA-HONESTY RAIL).
--
-- What THIS migration DOES ship: `sarvatobhadra` rows served by
-- `ka_vedha_gochara`, computed via the EXISTING, already-disclosed
-- algorithmic opposition approximation
-- (services/gochara_grammar/sarvatobhadra.py::opposite_nakshatra_id) wired
-- into a live per-chart computation for the FIRST TIME (previously an
-- internal primitive only, never a standalone served artifact). Every such
-- row carries `uncited_extension=true` and a `detail.r19_disclosure` field
-- repeating this exact disclosure. Filed as an ADJUDICATION-PENDING
-- corpus-ingestion gap — should `l1_sarvatobhadra_vedha` ever be populated
-- with a native-approved, source-verified table,
-- sarvatobhadra.py::_vedha_pairs_from_db becomes the primary path
-- automatically with zero change to this writer.
--
-- ── IDEMPOTENCY (§N.3) ───────────────────────────────────────────────────────
-- Per-chart delete-then-insert, scoped to (chart_id, ayanamsha_id,
-- vedha_kind, graha, window_start) as the natural key.
-- =============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS kala_vedha_gochara (
  id                        BIGSERIAL PRIMARY KEY,
  chart_id                  UUID NOT NULL,
  ayanamsha_id              TEXT NOT NULL DEFAULT 'lahiri_chitrapaksha',
  vedha_kind                TEXT NOT NULL CHECK (vedha_kind IN ('house_vedha', 'sarvatobhadra')),
  graha                     TEXT NOT NULL,
  window_start              DATE NOT NULL,
  window_end                DATE NOT NULL,
  start_truncated           BOOLEAN NOT NULL,
  end_truncated             BOOLEAN NOT NULL,
  janma_reference_fact_id   TEXT NOT NULL,
  classical_citation        TEXT NOT NULL,
  uncited_extension         BOOLEAN NOT NULL,
  -- Kind-specific fields, mirrors bg_sky_events' own `detail` precedent
  -- (migration 473) rather than a wide table of mostly-NULL columns:
  --   house_vedha:   {primary_house, primary_sign_idx, primary_sign_name,
  --                    vedha_house, vedha_sign_idx, vedha_sign_name, phala,
  --                    obstruction_active, obstructing_graha,
  --                    obstruction_window_start, obstruction_window_end}
  --   sarvatobhadra: {target_nakshatra_idx, target_nakshatra_name,
  --                    vedha_nakshatra_idx, vedha_nakshatra_name,
  --                    vedha_pair_source, cancellation_effect, r19_disclosure}
  detail                    JSONB NOT NULL DEFAULT '{}'::jsonb,
  formula_version           TEXT NOT NULL,
  computed_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT kala_vedha_gochara_natural_key
    UNIQUE (chart_id, ayanamsha_id, vedha_kind, graha, window_start),
  CONSTRAINT kala_vedha_gochara_window_order CHECK (window_end >= window_start)
);

CREATE INDEX IF NOT EXISTS idx_kala_vedha_gochara_lookup
  ON kala_vedha_gochara (chart_id, vedha_kind, graha, window_start, window_end);
CREATE INDEX IF NOT EXISTS idx_kala_vedha_gochara_detail_gin
  ON kala_vedha_gochara USING GIN (detail);

COMMENT ON TABLE kala_vedha_gochara IS
  'ṢAḌ-DARŚANA W3 item 5 (closes R-19): Vedha application + Sarvatobhadra. '
  'Two DISTINCT classical vedha (obstruction) mechanisms distinguished by '
  'vedha_kind — house_vedha (BPHS Ch.29/Phaladeepika Ch.26, REAL cited '
  'bg_transit_rules data, uncited_extension=false) and sarvatobhadra (the '
  'existing algorithmic opposition approximation, uncited_extension=true — '
  'see services/ka_vedha_gochara/logic.py module docstring for the full '
  'R-19 honesty disclosure: the primary-cited 9x9 grid tables remain '
  'unpopulated — no responsibly-transcribable source was found this '
  'session, disclosed rather than fabricated).';

COMMENT ON COLUMN kala_vedha_gochara.vedha_kind IS
  'house_vedha (house-level, from natal Moon, REAL cited rules) or '
  'sarvatobhadra (nakshatra-level, R-19, algorithmic approximation — see '
  'table comment). Never conflated into one undifferentiated row shape.';

COMMENT ON COLUMN kala_vedha_gochara.uncited_extension IS
  'false for house_vedha (bg_transit_rules is a real, cited, populated '
  'reference table); true for sarvatobhadra (the vedha-nakshatra pairing is '
  'still an algorithmic approximation, not a primary-cited classical grid '
  '— see table comment / R-19 disclosure).';

-- ── asset_registry seed row for `ka_vedha_gochara` (Nirmāṇa contract
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
    'ka_vedha_gochara',
    'kala',
    123,
    'Vedha-Gocara',
    'Vedha Application (Transit Obstruction)',
    'ṢAḌ-DARŚANA W3 item 5 (closes R-19): two classical vedha (obstruction) '
    'mechanisms applied to a chart''s currently-active and forward transits '
    '— house_vedha (BPHS Ch.29/Phaladeepika Ch.26, from bg_transit_rules, '
    'REAL cited data) and sarvatobhadra (nakshatra-level, an honestly '
    'disclosed algorithmic approximation pending corpus ingestion — see '
    'services/ka_vedha_gochara/logic.py). Reads natal Moon longitude from '
    'chart_facts (ga_positions) and transiting positions from '
    'ephemeris_daily (bg_ephemeris).',
    'postgres_table', 'kala_vedha_gochara',
    'SELECT COUNT(*) FROM kala_vedha_gochara WHERE chart_id=$1',
    'SELECT pg_total_relation_size(''kala_vedha_gochara'')',
    0, 'per_chart', true, true, false,
    120,
    'Kāla', 'L3', 'CURRENT', 'data',
    ARRAY['ga_positions', 'bg_ephemeris', 'bg_transit_rules']::text[]
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
--   DELETE FROM asset_registry WHERE asset_id = 'ka_vedha_gochara';
--   DROP TABLE IF EXISTS kala_vedha_gochara;
--   COMMIT;
-- =============================================================================
