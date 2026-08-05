-- Migration 540: build_protected_assets — sweep-protection Layers 3+4
-- Created: 2026-08-06
-- Renumbered 539->540 2026-08-06: this file was authored as 539 (see the
-- MIGRATION NUMBER note below for the collision this section already
-- anticipated), but a DIFFERENT 539_chart_facts_verification_pass_status_check.sql
-- (main PR #1060) landed on shad-darshana/integration in the interim and made
-- the 539 filename a real collision on this branch's own merge target,
-- not just a same-number-different-branch coincidence. 540 was free on both
-- `main` and `shad-darshana/integration` at rename time (re-verified
-- immediately before finalizing). Content below is otherwise unchanged from
-- the original 539 authoring.
-- =============================================================================
-- Tonight's directive Phase 1a (SHAD-DARSHANA sweep-protection). ka_gochara_sweep
-- already carries a binding native protection ruling at the application layer
-- ("enumerate the exact asset/chart list, no wider cascade" —
-- platform/python-sidecar/run_elev_beta_integration_rebuild.py's own docstring;
-- platform/python-sidecar/routers/permission_curve.py names it a
-- must_not_touch module). That ruling has had no DATABASE-level enforcement
-- until now — any direct DELETE/UPDATE/TRUNCATE against kala_gochara_windows
-- (a manual psql session, a mis-scoped clear, a future writer bug) could still
-- silently destroy the protected sweep. This migration is Layers 3+4 of that
-- protection: a registry table naming exactly which (asset_id, chart_id) pairs
-- are protected, and a trigger pair on kala_gochara_windows that refuses to
-- DELETE/UPDATE/TRUNCATE a protected pair's rows unless a session explicitly
-- opts in with `SET LOCAL app.allow_protected_sweep_rewrite = 'on'` — a
-- deliberately loud, per-session, non-default override a native decision must
-- authorize. INSERTs are never restricted (a rebuild's normal write path).
--
-- MIGRATION NUMBER (original 539 authoring note, kept for audit trail):
-- checked via `npm run migration:next` against this branch's own tree (cut
-- from origin/shad-darshana/integration) immediately before authoring —
-- platform/migrations max = 474, platform/supabase/migrations max = 538
-- (538_bg_gochara_arcs.sql). 539 was free in both directories on this branch
-- at that time. NOTE (disclosed, not silently assumed away): a DIFFERENT
-- 539_chart_facts_verification_pass_status_check.sql already landed on `main`
-- (PR #1060, unrelated DEFECT SALVAGE S8 campaign) but had not yet reached
-- `shad-darshana/integration` as of that write — the two files were unrelated
-- content sharing a number by the same "two campaigns, two branches" class
-- MIGRATION_AND_MERGE_PROTOCOL_v1_0.md §1 describes.
--
-- RESOLVED 2026-08-06: 539_chart_facts_verification_pass_status_check.sql
-- (the real, unrelated migration) subsequently merged to both `main` and
-- `shad-darshana/integration`, turning the anticipated same-number-different-
-- branch coincidence into an actual collision against this PR's own merge
-- target. Applying the renumber-on-collision protocol (§3, §7 R6) this file
-- was renumbered 539->540 in place; the chart_facts migration keeps its
-- original 539 number unchanged (it landed first and is unrelated to this
-- one).
--
-- LAYER 3: build_protected_assets registry --------------------------------
-- (asset_id, chart_id) pairs a native has designated protected. No FK to
-- `charts`/`asset_registry` by design — mirrors kala_gochara_windows.chart_id
-- and every other per-chart table in this codebase, which carry chart_id as a
-- loosely-coupled UUID, not an enforced FK (chart lifecycle/deletion is
-- managed at the application layer, not via cascade).
--
-- LAYER 4: kala_gochara_windows DELETE/UPDATE/TRUNCATE guard ---------------
-- BEFORE DELETE OR UPDATE, FOR EACH ROW: raises when OLD.chart_id is a
-- protected pair for asset_id='ka_gochara_sweep'. BEFORE TRUNCATE, FOR EACH
-- STATEMENT: raises when ANY protected pair for asset_id='ka_gochara_sweep'
-- exists at all — a TRUNCATE has no per-row OLD/NEW to test and unconditionally
-- affects every chart's rows, so any protected pair's presence is sufficient
-- to block it (the row-level trigger's per-row OLD.chart_id test does not
-- apply to a statement-level TRUNCATE trigger). Every other (asset_id,
-- chart_id) pair — i.e. every chart NOT listed in build_protected_assets —
-- is completely unaffected: the EXISTS check is scoped to the specific row's
-- chart_id, so a DELETE/UPDATE against an unprotected chart's rows in the
-- same table proceeds exactly as before this migration.
--
-- lock_timeout: kala_gochara_windows is actively written by other processes
-- (the ka_gochara_sweep HEAVY writer, migration 436's substep-resumable
-- pattern). CREATE TRIGGER takes a brief ACCESS EXCLUSIVE lock on the target
-- table to write into the catalog; on a live table, if another transaction
-- holds a lock at that moment this DDL would otherwise queue for it, and
-- Postgres's FIFO lock queue means every NEW query against the table issued
-- after that queues behind the pending DDL too. SET LOCAL lock_timeout aborts
-- this transaction cleanly instead of queueing indefinitely — same hardening
-- migration 539 (chart_facts_verification_pass_status_check, main PR #1060)
-- applied to its own ALTER TABLE after a migration-guard WARN-2 review; this
-- migration adopts the identical pattern up front rather than waiting for the
-- same review to flag it.
--
-- Idempotency: CREATE TABLE IF NOT EXISTS, ON CONFLICT DO NOTHING for the two
-- seed rows, CREATE OR REPLACE FUNCTION for both trigger functions, and
-- DROP TRIGGER IF EXISTS + CREATE TRIGGER (Postgres has no CREATE TRIGGER IF
-- NOT EXISTS) so a re-run of this migration is a clean no-op rebuild of the
-- same trigger definitions rather than an ON-CONFLICT error.
-- =============================================================================

BEGIN;

SET LOCAL lock_timeout = '2s';

-- LAYER 3: the registry table -----------------------------------------------

CREATE TABLE IF NOT EXISTS build_protected_assets (
  asset_id         TEXT        NOT NULL,
  chart_id         UUID        NOT NULL,
  protected_since  TIMESTAMPTZ NOT NULL DEFAULT now(),
  reason           TEXT        NOT NULL,
  PRIMARY KEY (asset_id, chart_id)
);

COMMENT ON TABLE build_protected_assets IS
  'SHAD-DARSHANA sweep-protection Phase 1a, Layer 3. Native-designated '
  '(asset_id, chart_id) pairs whose build data must not be silently '
  'DELETEd/UPDATEd/TRUNCATEd. Enforced on kala_gochara_windows by the Layer-4 '
  'trigger pair this same migration installs; a planner-side guard (Layer '
  '1/2, platform/src/lib/build/plan.ts + the cockpit plan/clear routes) '
  'additionally surfaces a protected pair as ''protected — native override '
  'required'' instead of silently including it in a build/delete/clear plan.';

COMMENT ON COLUMN build_protected_assets.reason IS
  'Human-readable justification for the protection, recorded at the time the '
  'pair was designated protected — never blank, per this table''s own '
  'protective purpose (a protection with no stated reason cannot be reviewed '
  'or later lifted with confidence).';

-- Seed: ka_gochara_sweep protected for both canonical charts.
INSERT INTO build_protected_assets (asset_id, chart_id, reason) VALUES
  (
    'ka_gochara_sweep',
    '482012f1-710e-4a25-994a-93821f5871aa',
    'Native protection ruling (binding, application-layer precedent in '
    'run_elev_beta_integration_rebuild.py / permission_curve.py must_not_touch '
    'discipline): the native chart''s birth->birth+100y gochara sweep is '
    'expensive to rebuild (HEAVY writer, 1800s timeout, migration 436 '
    'substep-resumable) and must never be silently destroyed by a mis-scoped '
    'DELETE/UPDATE/TRUNCATE. SHAD-DARSHANA Phase 1a, 2026-08-06.'
  ),
  (
    'ka_gochara_sweep',
    '1c826d5a-41cb-4450-b4dc-59d440e5f75a',
    'Same protection extended to the second canonical chart (Abhinandan '
    'Mohanty), the standing SAFE non-native rebuild/rehearsal subject '
    '(REBUILD_SESSION_PLAN_v1_0.md) — its sweep is equally expensive to '
    'regenerate and equally subject to accidental destructive operations '
    'during rehearsal/testing sessions. SHAD-DARSHANA Phase 1a, 2026-08-06.'
  )
ON CONFLICT (asset_id, chart_id) DO NOTHING;

-- LAYER 4: the kala_gochara_windows guard triggers ---------------------------

CREATE OR REPLACE FUNCTION build_protected_assets_guard_row()
RETURNS TRIGGER AS $$
BEGIN
  -- Explicit, per-session, non-default override. `true` as the second arg to
  -- current_setting means "missing_ok" — an unset GUC reads as NULL rather
  -- than raising, so the IF below is false (not an error) when nobody has
  -- opted in.
  IF current_setting('app.allow_protected_sweep_rewrite', true) = 'on' THEN
    RETURN COALESCE(NEW, OLD);
  END IF;

  IF EXISTS (
    SELECT 1 FROM build_protected_assets
     WHERE asset_id = 'ka_gochara_sweep'
       AND chart_id = OLD.chart_id
  ) THEN
    RAISE EXCEPTION
      'BUILD-PROTECTED: kala_gochara_windows row(s) for chart_id % '
      '(asset_id=ka_gochara_sweep) are protected — % is refused. Set '
      'app.allow_protected_sweep_rewrite=on for this session to override '
      '(native decision required; see build_protected_assets.reason).',
      OLD.chart_id, TG_OP;
  END IF;

  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION build_protected_assets_guard_row() IS
  'SHAD-DARSHANA sweep-protection Layer 4 (row-level). BEFORE DELETE/UPDATE '
  'guard on kala_gochara_windows — refuses to modify a row whose chart_id is '
  'protected for asset_id=ka_gochara_sweep in build_protected_assets, unless '
  'app.allow_protected_sweep_rewrite=on is set for the session. INSERT is '
  'never gated by this function (not attached to an INSERT trigger).';

DROP TRIGGER IF EXISTS trg_kala_gochara_windows_protect_row ON kala_gochara_windows;
CREATE TRIGGER trg_kala_gochara_windows_protect_row
  BEFORE DELETE OR UPDATE ON kala_gochara_windows
  FOR EACH ROW EXECUTE FUNCTION build_protected_assets_guard_row();

CREATE OR REPLACE FUNCTION build_protected_assets_guard_truncate()
RETURNS TRIGGER AS $$
BEGIN
  IF current_setting('app.allow_protected_sweep_rewrite', true) = 'on' THEN
    RETURN NULL;
  END IF;

  -- TRUNCATE has no per-row OLD to test and unconditionally wipes every
  -- chart's rows in one statement — so the presence of ANY protected pair
  -- for this asset is sufficient to refuse it, not just a pair whose rows
  -- currently exist in the table.
  IF EXISTS (
    SELECT 1 FROM build_protected_assets WHERE asset_id = 'ka_gochara_sweep'
  ) THEN
    RAISE EXCEPTION
      'BUILD-PROTECTED: kala_gochara_windows cannot be TRUNCATEd while any '
      'chart_id is protected for asset_id=ka_gochara_sweep (a TRUNCATE '
      'affects every chart''s rows, protected or not). Set '
      'app.allow_protected_sweep_rewrite=on for this session to override '
      '(native decision required; see build_protected_assets.reason).';
  END IF;

  RETURN NULL;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION build_protected_assets_guard_truncate() IS
  'SHAD-DARSHANA sweep-protection Layer 4 (statement-level). BEFORE TRUNCATE '
  'guard on kala_gochara_windows — refuses the TRUNCATE while any '
  'asset_id=ka_gochara_sweep pair is protected, unless '
  'app.allow_protected_sweep_rewrite=on is set for the session.';

DROP TRIGGER IF EXISTS trg_kala_gochara_windows_protect_truncate ON kala_gochara_windows;
CREATE TRIGGER trg_kala_gochara_windows_protect_truncate
  BEFORE TRUNCATE ON kala_gochara_windows
  FOR EACH STATEMENT EXECUTE FUNCTION build_protected_assets_guard_truncate();

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   SET LOCAL lock_timeout = '2s';
--   DROP TRIGGER IF EXISTS trg_kala_gochara_windows_protect_truncate ON kala_gochara_windows;
--   DROP TRIGGER IF EXISTS trg_kala_gochara_windows_protect_row ON kala_gochara_windows;
--   DROP FUNCTION IF EXISTS build_protected_assets_guard_truncate();
--   DROP FUNCTION IF EXISTS build_protected_assets_guard_row();
--   DROP TABLE IF EXISTS build_protected_assets;
--   COMMIT;
-- (kala_gochara_windows itself, and its data, are untouched by this DOWN —
--  this migration only ever added protection around that table, never
--  altered its own schema or rows.)
-- =============================================================================
