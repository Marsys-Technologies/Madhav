-- Migration 541: kala_gochara_v2_build_state — W2G per-chart delta-aware
-- invalidation + honest horizon attestation store
-- =============================================================================
-- ṢAḌ-DARŚANA campaign · wave W2G (GOCHARA-2.0, item 19) · lane G. Ratified
-- design amendments this table exists to satisfy: amendment 2 (delta-aware
-- invalidation -- per-class, per-grammar-version fingerprints so one class's
-- grammar change never forces a full century-stream replan) and amendment 3
-- (progressive horizon onboarding -- build ±3 years from "now" first, serve
-- with an HONEST horizon attestation, never silently present a partial
-- horizon as complete).
--
-- ── WHY A NEW TABLE, NOT NEW COLUMNS ON kala_gochara_windows ────────────────
-- `kala_gochara_windows` is the untouchable-data rail's protected surface
-- (v1's sweep table; per-row generation stamping landed via migration 527,
-- ADJUDICATION-6). This table is deliberately NOT an ALTER TABLE on it:
--   1. per-row generation stamping is already solved (migration 527);
--   2. per-class fingerprint/horizon state is a BUILD-BOOKKEEPING concern,
--      not a served-row concern -- it belongs beside kala_gochara_windows,
--      the same way kala_gochara_authority (also migration 527) sits beside
--      it rather than inside it;
--   3. this campaign has multiple lanes touching kala_gochara_windows-
--      adjacent surfaces concurrently this week (migration 540's
--      build_protected_assets rail, the sweep-relay work) -- a schema change
--      to the shared table itself is exactly the kind of change this lane
--      was told to avoid without a dedicated ruling, whereas a wholly new,
--      independently-rollback-able table carries none of that risk.
--
-- ── WHAT IT RECORDS, PER (chart_id, event_class) ────────────────────────────
--   * `class_fingerprint` -- services.w2g.fingerprint.class_fingerprint's
--     output for the LAST successful materialization of this class: hashes
--     the event_class, its grammar_version, its resonance targets, and the
--     arc_fingerprint of every body substrate it read. A future build
--     recomputes the same fingerprint before touching anything; an unchanged
--     fingerprint means an honest no-op (see services/w2g/fingerprint.py's
--     own docstring for the incident this exists to prevent -- v1's single
--     whole-fingerprint design forced an all-~606-substep replan for a
--     ONE-CLASS grammar edit).
--   * `horizon_start_date`/`horizon_end_date`/`horizon_status` -- design
--     amendment 3's attestation: exactly what span of time this class's rows
--     actually cover right now. `horizon_status` is 'progressive_partial'
--     until a future backfill lane advances it to 'full_backfill' -- a
--     caller reading kala_gochara_windows' 2.0-generation rows for this
--     class can join back here and know honestly whether it is looking at
--     the whole picture or a fast first slice.
--   * `contacts_evaluated`/`rows_written` -- earned counters (§N.8), not
--     estimates: how many arc-substrate candidate instants this build asked
--     the frozen v1 scoring grammar about, and how many of those were
--     genuinely active and therefore served.
--
-- Writer: ka_gochara_sweep_v2 (L3 Kāla, HEAVY -- plan_substeps/run_substep,
-- one substep per populated gochara_resonance_map event_class). v1's
-- ka_gochara_sweep is UNTOUCHED by this migration and this writer -- see
-- CLAUDECODE_BRIEF/PR body for the strangler-fig disposition (v1 stays
-- authoritative; 2.0 rows land generation-stamped beside it per
-- ADJUDICATION-6; no authority flip is authorized by this lane).
--
-- Idempotent: `CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`. No
-- destructive ops, no ALTER of any existing table, no data written by this
-- migration (the table starts empty; the writer populates it going forward).
--
-- Migration-number coordination: highest claimed at authoring time was 540
-- (`540_build_protected_assets.sql`, already on `shad-darshana/integration`);
-- cross-checked against every open `shad-darshana/*` branch's
-- `platform/supabase/migrations/` tree at claim time -- none claims 541.
-- =============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS kala_gochara_v2_build_state (
    chart_id              UUID NOT NULL,
    event_class           TEXT NOT NULL,
    generation             TEXT NOT NULL DEFAULT '2.0',

    class_fingerprint      TEXT NOT NULL,
    grammar_version         TEXT NOT NULL,
    arc_engine_version       TEXT NOT NULL,
    bodies_scope              TEXT[] NOT NULL DEFAULT '{}',

    horizon_start_date         DATE NOT NULL,
    horizon_end_date            DATE NOT NULL,
    horizon_status                TEXT NOT NULL
        CHECK (horizon_status IN ('progressive_partial', 'full_backfill')),

    contacts_evaluated              INTEGER NOT NULL DEFAULT 0,
    rows_written                      INTEGER NOT NULL DEFAULT 0,
    skipped_reason                      TEXT,

    build_id                              TEXT,
    computed_at                             TIMESTAMPTZ NOT NULL DEFAULT now(),

    PRIMARY KEY (chart_id, event_class, generation)
);

COMMENT ON TABLE kala_gochara_v2_build_state IS
    'Migration 541 (ṢAḌ-DARŚANA W2G lane G): per (chart_id, event_class, '
    'generation) build bookkeeping for the GOCHARA-2.0 per-chart writer -- '
    'delta-aware invalidation fingerprint (design amendment 2) + honest '
    'progressive-horizon attestation (design amendment 3). Deliberately a '
    'NEW table, not a column added to the protected kala_gochara_windows -- '
    'see migration header. Never read by v1''s ka_gochara_sweep; never '
    'written by anything other than ka_gochara_sweep_v2.';

COMMENT ON COLUMN kala_gochara_v2_build_state.class_fingerprint IS
    'services.w2g.fingerprint.class_fingerprint output for the last '
    'successful build of this (chart_id, event_class): a hash of the class, '
    'its grammar_version, its resonance targets, and the arc_fingerprint of '
    'every body substrate consulted. A future build recomputes the same '
    'fingerprint BEFORE touching kala_gochara_windows; a match is an honest '
    'no-op, never a fabricated re-write.';

COMMENT ON COLUMN kala_gochara_v2_build_state.horizon_status IS
    'progressive_partial until a future backfill lane advances this row to '
    'full_backfill. Design amendment 3: never silently present a partial '
    'horizon as the whole century.';

CREATE INDEX IF NOT EXISTS idx_kala_gochara_v2_build_state_chart
    ON kala_gochara_v2_build_state (chart_id);

-- ── asset_registry registration (per_chart, HEAVY, beside v1's ka_gochara_sweep) ──

INSERT INTO asset_registry (
    asset_id, layer, sort_order,
    sanskrit_name, english_name, english_description,
    storage_type, target_table, count_sql, size_sql,
    target_floor, scope, is_active, has_writer, has_substeps,
    writer_timeout_seconds,
    layer_name, layer_index, catalog_status
) VALUES (
    'ka_gochara_sweep_v2',
    'kala',
    106,
    'Gochara Purah-Sancalana Cakra (2.0)',
    'GOCHARA-2.0 Per-Chart Materialization',
    'ṢAḌ-DARŚANA W2G (item 19): joins the chart-independent bg_gochara_arcs '
    'contact stream against a chart''s gochara_resonance_map natal targets '
    'and scores each candidate instant through v1''s own, unmodified '
    'gochara_intensity.compute_lambda_e grammar (design §5: 2.0 changes HOW, '
    'never WHAT). Writes generation=''2.0''-stamped rows BESIDE v1''s '
    'kala_gochara_windows rows (ADJUDICATION-6) -- v1 rows are never '
    'touched. Progressive-horizon posture (amendment 3): builds ±3 years '
    'from "now" first; full-century backfill is a future lane. Point-shaped '
    'event classes only in this first lane -- interval/chain deferred (see '
    'services/w2g/materialize.py module docstring).',
    'postgres_table', 'kala_gochara_windows',
    'SELECT COUNT(*) FROM kala_gochara_windows WHERE chart_id=$1 AND generation=''2.0''',
    NULL,
    0, 'per_chart', true, true, true,
    1800,
    'Kāla', 'L3', 'CURRENT'
) ON CONFLICT (asset_id) DO UPDATE SET
    count_sql              = EXCLUDED.count_sql,
    target_table            = EXCLUDED.target_table,
    has_writer               = EXCLUDED.has_writer,
    has_substeps              = EXCLUDED.has_substeps,
    writer_timeout_seconds     = EXCLUDED.writer_timeout_seconds,
    sort_order                  = EXCLUDED.sort_order,
    english_description          = EXCLUDED.english_description;

UPDATE asset_registry SET depends_on = ARRAY['bg_gochara_arcs', 'ka_gochara_resonance']::text[]
WHERE asset_id = 'ka_gochara_sweep_v2';

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   DELETE FROM asset_registry WHERE asset_id = 'ka_gochara_sweep_v2';
--   DROP TABLE IF EXISTS kala_gochara_v2_build_state;
--   COMMIT;
-- Safe: this migration wrote zero rows to any pre-existing table (the
-- asset_registry INSERT is a brand-new row keyed on a brand-new asset_id;
-- ON CONFLICT DO UPDATE only ever touches that same new row on a re-run).
-- No kala_gochara_windows row -- v1's or 2.0's -- is created, altered, or
-- deleted by this migration.
-- =============================================================================
