-- Migration 542: kala_gochara_windows_v2 — W2G's own generation-2.0 surface
-- =============================================================================
-- ṢAḌ-DARŚANA campaign, wave W2G (GOCHARA-2.0, item 19), lane G REWORK.
--
-- NATIVE RULING, 2026-08-06 (SHAD_DARSHANA_STATE.md, "RULING — Lane G / W2G
-- write-target", verbatim), binding on this migration:
--   1. Protection mechanism (migration 540) unchanged. The W2G writer must
--      NEVER set app.allow_protected_sweep_rewrite, in any code path.
--   2. W2G writes exclusively to its own surface (own asset_id + own tables
--      per GOCHARA_SWEEP_2_0_DESIGN_v1_0.md). It does not delete, update, or
--      insert into the protected (ka_gochara_sweep x canonical-chart) rows.
--      §N.3 idempotency applies to W2G's own generation only.
--   3. The protected corpus is W2G's frozen validation benchmark: W2G
--      acceptance REQUIRES an equivalence report against it, verified by
--      PARĪKṢAKA. Corpus disposition (whether 2.0 ever writes INTO
--      kala_gochara_windows, provenance-stamped, per design §4's END-STATE
--      description) is deferred to a W6 native ruling — NOT decided here.
--
-- PARĪKṢAKA found (2026-08-06, PR #1081, PARKED-HONEST) that the prior
-- design's `ka_gochara_sweep_v2` writer targeted `kala_gochara_windows`
-- directly: migration 540's row-level guard trigger fires on ANY DELETE/
-- UPDATE against a protected chart_id's rows in that table (it predates the
-- `generation` column and is not generation-aware), so the writer's own §N.3
-- idempotency delete was non-functional on any re-run against a protected
-- chart. This migration is the fix the ruling directs: a table the migration-
-- 540 trigger pair was never attached to, so the interaction is structurally
-- impossible rather than merely avoided by discipline.
--
-- ── WHY A NEW TABLE, SCHEMA-MIRRORED FROM kala_gochara_windows ──────────────
-- `kala_gochara_windows_v2` reproduces migration 460's column set (+ migration
-- 527's `generation` column, present from creation here rather than
-- retrofitted) column-for-column, so the equivalence-report tool (design §3)
-- can compare same-shaped rows across the two tables without a translation
-- layer. It carries NONE of migration 540's protection:
--   * migration 540's two triggers (`trg_kala_gochara_windows_protect_row`,
--     `trg_kala_gochara_windows_protect_truncate`) are `CREATE TRIGGER ... ON
--     kala_gochara_windows` — a trigger is bound to the specific relation
--     named at CREATE TRIGGER time; Postgres has no mechanism by which a
--     trigger on one table ever fires for statements against a
--     different, unrelated table. `kala_gochara_windows_v2` is a distinct
--     relation this migration creates; the guard functions
--     (`build_protected_assets_guard_row`/`_truncate`) are never invoked for
--     any statement against it, structurally, not by policy.
--   * `build_protected_assets` (the Layer-3 registry) is never INSERTed into
--     by this migration — no (asset_id, chart_id) pair naming this table's
--     writer is ever added to it, so even the row-level guard's WOULD-BE
--     protected-pair EXISTS check (were it ever attached to this table, which
--     it structurally cannot be without a separate future migration) would
--     find nothing.
--   * consequently `app.allow_protected_sweep_rewrite` is irrelevant to every
--     statement this migration or its writer issues — ruling point 1 is
--     satisfied by construction, not by writer-side discipline alone (see the
--     writer's own source + `test_writer_source_never_sets_the_override_
--     setting` / `test_writer_source_never_references_the_protected_table`
--     in `pipeline/orchestrator/writers/tests/test_ka_gochara_v2_materialize.py`
--     for the static, re-checkable proof).
--
-- ── CLEANUP OF THE SUPERSEDED PRIOR-DESIGN ARTIFACTS (this lane's own surface) ──
-- PR #1081's migration 541 (`kala_gochara_v2_build_state`, delta-aware-
-- invalidation fingerprint + horizon-attestation bookkeeping) was HAND-APPLIED
-- to production 2026-08-06 (never through the tracked runner — confirmed live,
-- `_migrations_applied` tops out at 540 as of this migration's authoring).
-- Migration 541's FILE is NOT edited here (already applied to a live database
-- — §N.4 forbids editing an applied migration). Its TABLE
-- (`kala_gochara_v2_build_state`) is generic (chart_id, event_class,
-- generation) fingerprint/horizon bookkeeping, was never coupled to a
-- particular SERVED table, and is KEPT + REUSED unchanged by the reworked
-- writer. Two things ARE cleaned up here, both squarely this lane's own
-- surface (not kala_gochara_windows, not its protection):
--   1. the `asset_registry` row for asset_id='ka_gochara_sweep_v2' (inserted
--      by migration 541) pointed `target_table` at `kala_gochara_windows` —
--      the now-superseded wrong design. That asset_id is retired here
--      (DELETE, not just updated) so no orphaned catalog entry survives
--      pointing at a table its own writer file no longer targets; a fresh row
--      for the renamed asset_id `ka_gochara_v2_materialize`, pointed at THIS
--      migration's table, is inserted below.
--   2. the 6 `kala_gochara_v2_build_state` rows (chart 482012f1, all 6
--      event_classes) left over from PR #1081's contaminated run — their
--      `rows_written`/`class_fingerprint` values describe the 27
--      `kala_gochara_windows` rows the Conductor already DELETEd in the
--      audited contamination-cleanup transaction recorded in
--      SHAD_DARSHANA_STATE.md. Deleting this stale bookkeeping (not the
--      table itself) means the reworked writer's next real run is compared
--      against nothing, not against a fingerprint for data that no longer
--      exists anywhere.
--
-- Idempotent: `CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`,
-- `DELETE ... WHERE` (safe to re-run — no-ops once already clean), `ON
-- CONFLICT DO UPDATE` for the asset_registry seed. No ALTER/DELETE/UPDATE of
-- any kind against `kala_gochara_windows` itself — grep-verifiable: this file
-- contains the literal string `kala_gochara_windows` ONLY inside comments and
-- as a strict prefix of `kala_gochara_windows_v2` / `kala_gochara_v2_build_state`.
--
-- Migration-number coordination: `git log --all --diff-filter=A --name-only`
-- across every fetched ref for `platform/{migrations,supabase/migrations}/54*`
-- at authoring time shows 540 (build_protected_assets), and two DIFFERENT
-- files both claiming 541 on separate branches (this campaign's own
-- `kala_gochara_v2_build_state.sql` and an unrelated `l0-ne-v02` branch's
-- `ne_v02_business_launch_lifetime_count.sql`) — neither branch claims 542.
-- =============================================================================

BEGIN;

SET LOCAL lock_timeout = '2s';

-- ── kala_gochara_windows_v2: schema-mirrored from migration 460 + 527 ───────

CREATE TABLE IF NOT EXISTS kala_gochara_windows_v2 (
  id BIGSERIAL PRIMARY KEY,
  chart_id UUID NOT NULL,
  event_class TEXT NOT NULL,
  temporal_shape TEXT NOT NULL CHECK (temporal_shape IN ('point', 'interval', 'chain')),

  window_start DATE NOT NULL,
  window_end DATE NOT NULL,
  peak_date DATE NOT NULL,

  milestone_id TEXT,
  is_irreversibility_milestone BOOLEAN NOT NULL DEFAULT FALSE,

  signed_intensity NUMERIC NOT NULL,
  raw_intensity NUMERIC NOT NULL,
  valence TEXT NOT NULL,
  is_adverse BOOLEAN NOT NULL,

  active_sentences JSONB NOT NULL DEFAULT '[]'::jsonb,
  contributing_systems JSONB NOT NULL DEFAULT '[]'::jsonb,
  suppression_state JSONB NOT NULL DEFAULT '{}'::jsonb,

  peak_basis TEXT NOT NULL DEFAULT 'gochara_lambda_e_v1',

  calibration_state TEXT NOT NULL DEFAULT 'structural_prior'
    CHECK (calibration_state IN ('structural_prior', 'empirically_calibrated')),
  source TEXT NOT NULL DEFAULT 'live' CHECK (source IN ('live', 'fixture')),
  computed_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  -- Present from creation (unlike v1's retrofit via migration 527) — every
  -- row in this table is GOCHARA-2.0-generation data; the column exists
  -- mainly so a future 2.x generation variant can land beside an earlier one
  -- in this same table using the identical discriminator convention v1 uses.
  generation TEXT NOT NULL DEFAULT '2.0'
);

-- Natural key INCLUDES generation from the start (v1's own equivalent index,
-- migration 460, predates migration 527's generation column and could not
-- include it without an untouchable-table ALTER — a disclosed, deliberately
-- unfixed gap on v1's side, per PR #1081's own writer docstring). This table
-- has no such history, so the gap is closed here rather than reproduced.
CREATE UNIQUE INDEX IF NOT EXISTS uq_kala_gochara_windows_v2_natural_key
  ON kala_gochara_windows_v2 (chart_id, event_class, window_start, peak_date,
                              COALESCE(milestone_id, ''), generation);

COMMENT ON TABLE kala_gochara_windows_v2 IS
    'ṢAḌ-DARŚANA W2G lane G REWORK (migration 542, native ruling 2026-08-06): '
    'the per-chart GOCHARA-2.0 materialization surface, schema-mirrored from '
    'kala_gochara_windows (migration 460+527) for direct equivalence-report '
    'comparability. Carries NONE of migration 540''s protection — it is a '
    'distinct relation the trigger pair was never attached to, structurally, '
    'not by writer discipline. kala_gochara_windows (v1, protected) is this '
    'table''s frozen validation benchmark, read-only, per the ruling''s point '
    '3 — never written to by this table''s writer. Corpus disposition '
    '(whether/when 2.0 data ever moves into kala_gochara_windows itself) is a '
    'DEFERRED W6 native ruling, not decided by this migration.';

COMMENT ON COLUMN kala_gochara_windows_v2.generation IS
    'Present from table creation (contrast migration 527''s retrofit onto '
    'v1). Currently always ''2.0'' -- the writer stamps this value on every '
    'row it inserts. Exists so a future generation variant has a place to '
    'land beside this one under the same discriminator convention v1 uses, '
    'without requiring another schema migration.';

CREATE INDEX IF NOT EXISTS idx_kala_gochara_windows_v2_chart_event
  ON kala_gochara_windows_v2 (chart_id, event_class);

CREATE INDEX IF NOT EXISTS idx_kala_gochara_windows_v2_chart_window
  ON kala_gochara_windows_v2 (chart_id, window_start, window_end);

CREATE INDEX IF NOT EXISTS idx_kala_gochara_windows_v2_chart_adverse
  ON kala_gochara_windows_v2 (chart_id, is_adverse, signed_intensity DESC);

CREATE INDEX IF NOT EXISTS idx_kala_gochara_windows_v2_chart_generation
  ON kala_gochara_windows_v2 (chart_id, generation);

-- ── asset_registry: retire the superseded asset_id, register the renamed one ──

-- Retire PR #1081's hand-applied, wrong-target row. Safe to re-run (no-op
-- once already deleted). Does not touch kala_gochara_windows or any of its
-- rows -- asset_registry is a catalog/bookkeeping table, not sweep data.
DELETE FROM asset_registry WHERE asset_id = 'ka_gochara_sweep_v2';

INSERT INTO asset_registry (
    asset_id, layer, sort_order,
    sanskrit_name, english_name, english_description,
    storage_type, target_table, count_sql, size_sql,
    target_floor, scope, is_active, has_writer, has_substeps,
    writer_timeout_seconds,
    layer_name, layer_index, catalog_status
) VALUES (
    'ka_gochara_v2_materialize',
    'kala',
    107,
    'Gochara Purah-Sancalana Cakra (2.0, satyapana)',
    'GOCHARA-2.0 Per-Chart Materialization (validation surface)',
    'ṢAḌ-DARŚANA W2G (item 19), lane G REWORK: joins the chart-independent '
    'bg_gochara_arcs contact stream against a chart''s gochara_resonance_map '
    'natal targets and scores each candidate instant through v1''s own, '
    'unmodified gochara_intensity.compute_lambda_e grammar (design §5: 2.0 '
    'changes HOW, never WHAT). Writes to kala_gochara_windows_v2, its OWN '
    'table -- NEVER to the protected kala_gochara_windows (native ruling '
    '2026-08-06). v1''s corpus is this asset''s frozen equivalence-report '
    'benchmark, read-only. Renamed from the superseded ka_gochara_sweep_v2 '
    '(PR #1081, PARKED-HONEST) to avoid any implication this is "v2 of the '
    'sweep" -- it is a wholly separate validation-phase surface. Progressive-'
    'horizon posture: builds +/-3 years from "now" first; full-century '
    'backfill is a future lane. Point-shaped event classes only in this '
    'first lane -- interval/chain deferred (see services/w2g/materialize.py '
    'module docstring).',
    'postgres_table', 'kala_gochara_windows_v2',
    'SELECT COUNT(*) FROM kala_gochara_windows_v2 WHERE chart_id=$1',
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
WHERE asset_id = 'ka_gochara_v2_materialize';

-- ── Stale bookkeeping cleanup: PR #1081's contaminated run's fingerprints ───
-- The 6 rows this DELETE removes describe class_fingerprint/rows_written
-- values for the 27 kala_gochara_windows rows the Conductor already deleted
-- (SHAD_DARSHANA_STATE.md, "Contamination cleanup EXECUTED", same-session,
-- audited COMMIT). Scoped tightly (chart_id + generation) so it is
-- structurally incapable of touching any OTHER chart's bookkeeping, and it
-- touches kala_gochara_v2_build_state only -- never kala_gochara_windows.
DELETE FROM kala_gochara_v2_build_state
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
  AND generation = '2.0';

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   DELETE FROM asset_registry WHERE asset_id = 'ka_gochara_v2_materialize';
--   DROP TABLE IF EXISTS kala_gochara_windows_v2;
--   COMMIT;
-- Safe: kala_gochara_windows_v2 is wholly owned by this migration (created
-- here, nothing else references it). The asset_registry DELETE only removes
-- the row this migration itself inserted. The stale kala_gochara_v2_build_
-- state rows this migration deleted are NOT restored by the DOWN (they
-- described already-purged data; restoring them would just re-create the
-- inconsistency this migration fixed). kala_gochara_windows itself, and its
-- data, are untouched by both this migration and its DOWN.
-- =============================================================================
