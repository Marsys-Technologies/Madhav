-- Migration 529: bg_sarvatobhadra_grid — school-tagged SBC grid, versioned L0 (ADJUDICATION-11)
-- =============================================================================
-- ṢAḌ-DARŚANA campaign · ANTARYĀMIN supplemental ruling ADJUDICATION-11
-- (00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/
--  SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md), issued after the w3-moorti-vedha
-- lane's PR #1009 disclosure, closing item 5 / defect R-19 CLOSED-PARTIAL-BY-DESIGN.
--
-- ── WHY THIS TABLE IS DELIBERATELY EMPTY ──────────────────────────────────────
-- ADJUDICATION-11 Part 1 AFFIRMS the lane's refusal to transcribe a Sarvatobhadra
-- Chakra grid from memory: unlike Kota-Chakra (ADJUDICATION-9 — one consistent
-- secondary description, transcribed as tier-(iii)), the SBC's 9x9 grid geometry
-- genuinely VARIES BY TRADITION (corpus findings: 8 `sarvatobhadra` hits, all
-- noise except one passing [MEDIUM] mention citing it exists but not its
-- geometry; neither Jyotish Sara Sangraha nor Narada Samhita is held). Selecting
-- ONE grid as "the" classical grid would be an interpretive, school-selecting
-- act — seating it as an L0 base fact is exactly the B.1 layer violation
-- (structural_prior-masquerading-as-fact) this campaign's DATA-HONESTY RAIL
-- exists to prevent. ADJUDICATION-11 Part 2 rules the ADJUDICATION-8 school-tag
-- machinery instead: this table is registered EMPTY — an empty school-keyed
-- table honestly states that grid variants exist and none is held, rather than
-- silently picking one. Grid-variant SELECTION (which school_tag a chart's
-- readings should prefer) is a `kala_paddhati_profile` matter (factor_family=
-- 'sarvatobhadra_grid'), same as the ADJUDICATION-8 Agnivasa precedent — that
-- profile table is a DIFFERENT item's (37) scope and is not built by this
-- migration.
--
-- ── ACTIVATION PATH (zero code change) ────────────────────────────────────────
-- `ka_vedha_gochara`'s writer tries a query against THIS table FIRST (see
-- services/ka_vedha_gochara/writer.py::_fetch_school_tagged_vedha_pair); with
-- zero rows present it returns None and the writer falls through to
-- `l1_sarvatobhadra_vedha` (migration 140, also empty) and finally the
-- disclosed algorithmic opposition approximation. A future native-approved,
-- source-verified school's grid activates the moment rows land here under a
-- `school_tag`, with NO writer code change required.
--
-- ── SCHEMA (generic cell representation, per ADJUDICATION-11's own spec) ──────
-- cell_kind='nakshatra_position': one row per nakshatra placed in the school's
--   9x9 grid (cell_index = grid cell number 1..81 or similar; cell_value =
--   nakshatra name or index, school-defined).
-- cell_kind='vedha_pair': one row per vedha (obstruction) relationship
--   (cell_index = source nakshatra 1-based id; cell_value = paired nakshatra
--   1-based id, as text). This is the shape `ka_vedha_gochara`'s writer reads.
--
-- ── VERSIONING (§N.3 / §B.8) ───────────────────────────────────────────────────
-- `table_version` zero-padded per the ne_vNN/kota_chakra_rings_vNN precedent.
-- A revision (or a first real school's data) lands as a NEW version by INSERT,
-- never an in-place edit.
--
-- ── IDEMPOTENCY ────────────────────────────────────────────────────────────────
-- L0 = ON CONFLICT DO NOTHING semantics via the natural key below (global,
-- not per-chart, §N.3). No rows are inserted by this migration.
-- =============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS bg_sarvatobhadra_grid (
  id                BIGSERIAL PRIMARY KEY,
  school_tag        TEXT        NOT NULL,
  cell_index        INT         NOT NULL,
  cell_kind         TEXT        NOT NULL CHECK (cell_kind IN ('nakshatra_position', 'vedha_pair')),
  cell_value        TEXT        NOT NULL,
  source_text_id    TEXT,
  source_citation   TEXT,
  table_version     TEXT        NOT NULL,
  native_confirmed  BOOLEAN     NOT NULL DEFAULT FALSE,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT bg_sarvatobhadra_grid_natural_key
    UNIQUE (school_tag, cell_kind, cell_index, table_version)
);

CREATE INDEX IF NOT EXISTS idx_bg_sarvatobhadra_grid_lookup
  ON bg_sarvatobhadra_grid (cell_kind, cell_index, school_tag);

COMMENT ON TABLE bg_sarvatobhadra_grid IS
  'ADJUDICATION-11 Part 2: school-tagged Sarvatobhadra Chakra grid, versioned '
  'L0 global reference — DELIBERATELY EMPTY. An empty school-keyed table '
  'honestly states that SBC grid variants exist across Jyotish traditions and '
  'none is currently held/selected, rather than seating one tradition''s grid '
  'as an unqualified L0 fact (a B.1 layer violation). Grid-variant SELECTION '
  'per chart is a kala_paddhati_profile (factor_family=''sarvatobhadra_grid'') '
  'matter, item 37''s scope, not built here. Consumed (read-first) by '
  'ka_vedha_gochara (L3 Kāla, item 5) — a populated row activates '
  'automatically with zero writer-code change; see '
  'services/ka_vedha_gochara/writer.py.';

COMMENT ON COLUMN bg_sarvatobhadra_grid.school_tag IS
  'The named tradition/school this row''s grid belongs to (e.g. a specific '
  'text/lineage identifier) — never a bare "default"; the whole point of this '
  'table is that no single default may be assumed.';

COMMENT ON COLUMN bg_sarvatobhadra_grid.native_confirmed IS
  'Mirrors the ADJUDICATION-8 kala_paddhati_profile convention: FALSE until '
  'the native (or an equivalent authorized ruling) confirms which school_tag '
  'is operative for a given chart. Defaults FALSE; no row in this migration '
  'sets it TRUE (there are no rows).';

-- ── asset_registry seed row for `bg_sarvatobhadra_grid` (Nirmāṇa contract
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
    'bg_sarvatobhadra_grid',
    'brahmagyan',
    73,
    'Sarvatobhadra-Cakra Sāraṇī',
    'Sarvatobhadra Chakra Grid (School-Tagged)',
    'ADJUDICATION-11: school-tagged Sarvatobhadra Chakra grid reference table, '
    'registered DELIBERATELY EMPTY. SBC grid geometry varies by Jyotish '
    'tradition and no single school has been source-verified; an empty '
    'school-keyed table honestly states that variants exist rather than '
    'seating one as an unqualified fact. A populated school_tag activates '
    'ka_vedha_gochara''s DB-sourced-grid-first path with zero code change.',
    'postgres_table', 'bg_sarvatobhadra_grid',
    'SELECT COUNT(*) FROM bg_sarvatobhadra_grid',
    'SELECT pg_total_relation_size(''bg_sarvatobhadra_grid'')',
    0, 'global', true, false, false,
    NULL,
    'Brahmagyan', 'L0', 'CURRENT', 'data',
    ARRAY[]::text[]
) ON CONFLICT (asset_id) DO UPDATE SET
    count_sql               = EXCLUDED.count_sql,
    size_sql                = EXCLUDED.size_sql,
    target_table            = EXCLUDED.target_table,
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
--   DELETE FROM asset_registry WHERE asset_id = 'bg_sarvatobhadra_grid';
--   DROP TABLE IF EXISTS bg_sarvatobhadra_grid;
--   COMMIT;
-- =============================================================================
