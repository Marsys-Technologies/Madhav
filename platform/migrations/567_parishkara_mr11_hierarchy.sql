-- Migration 567: hierarchy columns (parent_window_id, resolution) on gochara windows
-- =============================================================================
-- PARISHKARA campaign, MR-11(b) (hierarchy windows CODE lane).
--
-- GOVERNING RULING — PK-R-1 (native, binding): "a 'window' served for timing
-- decisions must be at MINIMUM a month-resolution span carrying a day-precision
-- peak, or a dated point row. Decade-era rows alone are CONTEXT, not windows —
-- they may serve, but only labeled at their own resolution, never presented as
-- the timing claim itself. MR-11(b)'s hierarchy build = month/day rows for at
-- least the LEL-represented classes, parent_window_id wired, resolution facet
-- served."
--
-- BACKGROUND: the original W3.3 lane (services/gochara_v3/resolution_hierarchy.py,
-- already merged CODE, DB-free unit-tested at
-- services/gochara_v3/tests/test_w33_resolution_hierarchy.py) computes an
-- era ⊃ month ⊃ day window hierarchy with an in-memory (UUID-keyed)
-- parent_window_id, but was never wired into the production materializer
-- (ka_gochara_v3_century_materialize.py) and kala_gochara_windows/_v2 never
-- gained columns to persist the hierarchy tier or the parent linkage — so
-- zero hierarchy rows exist despite the code's existence. This migration adds
-- the two columns the writer needs to persist that hierarchy once wired
-- (companion PARIṢKĀRA MR-11(b) commit); the writer wiring is a SEPARATE
-- (non-DDL) commit in this same PR.
--
-- THE 2 COLUMNS (added identically to BOTH kala_gochara_windows and
-- kala_gochara_windows_v2 — the writer dual-writes to both surfaces per the
-- W5.4/UTK-R1 repoint):
--   parent_window_id  BIGINT  — the `id` of this row's widest containing
--                     coarser-tier window IN THE SAME TABLE (an era window's
--                     month/day children point at the era row's own `id`;
--                     the `id` column type on both tables is `bigint`,
--                     confirmed by live schema inspection 2026-08-11 — see
--                     this migration's self-check §3c/3d). NULL for a
--                     top-tier (era) row, or any row with no computed parent.
--                     Deliberately NO FOREIGN KEY constraint: the writer's
--                     §N.3 delete-then-insert idempotency pattern re-creates
--                     an entire (chart_id × event_class × generation ×
--                     era_slice_key) row set on every rebuild, and children
--                     may be inserted in the same transaction as their
--                     not-yet-committed parent — a same-table self-FK would
--                     force either deferred-constraint machinery or a strict
--                     parent-before-child COMMIT ordering neither the FROZEN
--                     orchestrator contract (single sub-step transaction) nor
--                     this table's existing DELETE/INSERT pattern assumes.
--                     The column is documentary/logical linkage, resolved at
--                     INSERT time from the writer's own in-memory hierarchy
--                     (RETURNING id captured per inserted parent row before
--                     its children are inserted) — same discipline as every
--                     other "additive, nullable, no behavior change for
--                     existing rows" column this table has gained
--                     (migrations 556/558/559/564).
--   resolution        TEXT    — the hierarchy tier this row was produced at:
--                     'era' | 'month' | 'day' (services/gochara_v3/
--                     resolution_hierarchy.py's RESOLUTION_TIERS, minus the
--                     not-yet-built 'muhurta' tier). NULL for every row
--                     written before this migration (all pre-MR-11(b) rows,
--                     both v1 sweep rows and W3.4/W5.4 flat-interval v3
--                     rows) — an honest "not classified into the hierarchy"
--                     value, per PK-R-1: a NULL-resolution row must never be
--                     silently presented as a timing-precision window by a
--                     caller; register_gochara_windows.ts (companion TS
--                     commit, same PR) derives an honest IMPLIED label from
--                     window_start/window_end duration for NULL rows, and
--                     marks it explicitly as inferred (never conflated with
--                     a genuinely stored resolution tier).
--
-- Both columns are NULLABLE: all pre-existing rows on both tables (the v1
-- sweep corpus and every W3.4/W5.4 flat-interval v3 row already materialized)
-- carry NULL in both columns and remain valid under the new schema — no
-- existing row's shape changes, no existing row is touched by this DDL-only
-- migration. Per §N.4 "Floors aspirational, not gates" / §N.7 item 6: an
-- honest NULL beats an invented resolution tier for rows this migration did
-- not (and cannot) retroactively classify.
--
-- IDEMPOTENT: ADD COLUMN IF NOT EXISTS — safe to re-run. The self-verification
-- DO block at the end raises if any column is still missing/mistyped/NOT-NULL
-- after the ADD, per §N.4 "a migration that cannot verify itself is not
-- trustworthy" (style mirrors migration 564).
--
-- PROTECTED CORPUS: kala_gochara_windows carries the v1 sweep corpus for
-- charts 482012f1 and 1c826d5a (build_protected_assets) plus the gen-3.0 rows
-- protected by migration 566's trigger. This migration is schema-only (ADD
-- COLUMN, no INSERT/UPDATE/DELETE of any row) — both the migration-540 and
-- migration-566 row-level guards are BEFORE DELETE/UPDATE triggers and never
-- fire on DDL. Grep-verifiable: this file contains no INSERT, UPDATE, or
-- DELETE targeting kala_gochara_windows/kala_gochara_windows_v2 rows.
--
-- EXECUTE-TO-VERIFY (Codex C1): this migration was run against a throwaway
-- local Postgres instance seeded with the live column definitions of both
-- tables (read-only inspected from production via the DB-schema-only access
-- this lane is authorized for) before being declared applied-clean. See this
-- lane's close report / PR description for the transcript.
-- =============================================================================

BEGIN;

SET LOCAL lock_timeout = '2s';

-- ── 1. kala_gochara_windows (production surface, generation='3.0'+'v1') ─────

ALTER TABLE kala_gochara_windows
  ADD COLUMN IF NOT EXISTS parent_window_id  BIGINT,
  ADD COLUMN IF NOT EXISTS resolution        TEXT;

COMMENT ON COLUMN kala_gochara_windows.parent_window_id IS
  'Migration 567 (PARIṢKĀRA MR-11(b)): id of the widest containing coarser-'
  'tier hierarchy window IN THIS SAME TABLE (e.g. a month/day row''s era '
  'parent). NULL for era-tier rows (no coarser parent exists) and for every '
  'row predating this migration. No FK constraint — see migration file header '
  'for the delete-then-insert idempotency rationale. Resolved by the writer '
  '(ka_gochara_v3_century_materialize.py) from services.gochara_v3.'
  'resolution_hierarchy.assign_parent_window_ids'' in-memory UUID linkage, '
  'mapped to this table''s own bigint ids via INSERT ... RETURNING id, '
  'parents inserted before children.';

COMMENT ON COLUMN kala_gochara_windows.resolution IS
  'Migration 567 (PARIṢKĀRA MR-11(b)): hierarchy tier this row was produced '
  'at -- ''era'' | ''month'' | ''day'' (services/gochara_v3/'
  'resolution_hierarchy.py RESOLUTION_TIERS, muhurta tier not yet built). '
  'NULL for every row written before this migration (honest -- never '
  'retroactively classified). Per PK-R-1 (native ruling): a NULL or ''era'' '
  'row must never be served as a genuine timing-precision window without '
  'explicit context-only disclosure -- see register_gochara_windows.ts.';

-- ── 2. kala_gochara_windows_v2 (calibration/staging surface) ────────────────
-- Same two columns, identical semantics, mirrored per the writer's dual-write
-- design (migrations 558/559/564 already mirror columns across both tables).

ALTER TABLE kala_gochara_windows_v2
  ADD COLUMN IF NOT EXISTS parent_window_id  BIGINT,
  ADD COLUMN IF NOT EXISTS resolution        TEXT;

COMMENT ON COLUMN kala_gochara_windows_v2.parent_window_id IS
  'Migration 567 (PARIṢKĀRA MR-11(b)): mirrors kala_gochara_windows.'
  'parent_window_id (this migration) -- id of the containing coarser-tier '
  'window IN THIS SAME TABLE. No FK constraint (see kala_gochara_windows '
  'comment / migration file header).';

COMMENT ON COLUMN kala_gochara_windows_v2.resolution IS
  'Migration 567 (PARIṢKĀRA MR-11(b)): mirrors kala_gochara_windows.'
  'resolution (this migration) -- ''era''|''month''|''day'', NULL for '
  'pre-migration rows.';

-- ── 3. Self-verification (§N.4 mandate) ──────────────────────────────────────

DO $$
BEGIN
  -- 3a. kala_gochara_windows.parent_window_id exists
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
     WHERE table_schema = 'public'
       AND table_name   = 'kala_gochara_windows'
       AND column_name  = 'parent_window_id'
  ) THEN
    RAISE EXCEPTION 'MIGRATION-567 SELF-CHECK FAILED: parent_window_id column missing on kala_gochara_windows';
  END IF;

  -- 3b. kala_gochara_windows.resolution exists
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
     WHERE table_schema = 'public'
       AND table_name   = 'kala_gochara_windows'
       AND column_name  = 'resolution'
  ) THEN
    RAISE EXCEPTION 'MIGRATION-567 SELF-CHECK FAILED: resolution column missing on kala_gochara_windows';
  END IF;

  -- 3c. kala_gochara_windows.parent_window_id type matches id column type (bigint)
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
     WHERE table_schema = 'public'
       AND table_name   = 'kala_gochara_windows'
       AND column_name  = 'parent_window_id'
       AND data_type    = 'bigint'
  ) THEN
    RAISE EXCEPTION 'MIGRATION-567 SELF-CHECK FAILED: kala_gochara_windows.parent_window_id must be bigint (matching id column type)';
  END IF;

  -- 3d. kala_gochara_windows_v2.parent_window_id exists and is bigint
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
     WHERE table_schema = 'public'
       AND table_name   = 'kala_gochara_windows_v2'
       AND column_name  = 'parent_window_id'
       AND data_type    = 'bigint'
  ) THEN
    RAISE EXCEPTION 'MIGRATION-567 SELF-CHECK FAILED: kala_gochara_windows_v2.parent_window_id missing or not bigint';
  END IF;

  -- 3e. kala_gochara_windows_v2.resolution exists
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
     WHERE table_schema = 'public'
       AND table_name   = 'kala_gochara_windows_v2'
       AND column_name  = 'resolution'
  ) THEN
    RAISE EXCEPTION 'MIGRATION-567 SELF-CHECK FAILED: resolution column missing on kala_gochara_windows_v2';
  END IF;

  -- 3f. All 4 new columns (2 per table) are nullable -- existing rows carry
  --     NULL and must remain valid.
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
     WHERE table_schema = 'public'
       AND table_name   IN ('kala_gochara_windows', 'kala_gochara_windows_v2')
       AND column_name  IN ('parent_window_id', 'resolution')
       AND is_nullable  = 'NO'
  ) THEN
    RAISE EXCEPTION 'MIGRATION-567 SELF-CHECK FAILED: one or more of the new columns '
      'has a NOT NULL constraint -- must be nullable (existing rows carry NULL)';
  END IF;

  -- 3g. No FK constraint was created on parent_window_id (deliberate design --
  --     see migration file header). This asserts the deliberate absence so a
  --     future edit that silently adds one is caught by this same-file check.
  IF EXISTS (
    SELECT 1
      FROM information_schema.table_constraints tc
      JOIN information_schema.key_column_usage kcu
        ON tc.constraint_name = kcu.constraint_name
       AND tc.table_schema = kcu.table_schema
     WHERE tc.constraint_type = 'FOREIGN KEY'
       AND tc.table_schema = 'public'
       AND tc.table_name IN ('kala_gochara_windows', 'kala_gochara_windows_v2')
       AND kcu.column_name = 'parent_window_id'
  ) THEN
    RAISE EXCEPTION 'MIGRATION-567 SELF-CHECK FAILED: parent_window_id unexpectedly '
      'carries a FOREIGN KEY constraint -- this migration''s design is a plain '
      'nullable bigint with no FK (see file header rationale)';
  END IF;

END $$;

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   SET LOCAL lock_timeout = '2s';
--   ALTER TABLE kala_gochara_windows
--     DROP COLUMN IF EXISTS parent_window_id,
--     DROP COLUMN IF EXISTS resolution;
--   ALTER TABLE kala_gochara_windows_v2
--     DROP COLUMN IF EXISTS parent_window_id,
--     DROP COLUMN IF EXISTS resolution;
--   COMMIT;
-- Safe: both columns are wholly owned by this migration. No existing row data
-- is modified by either direction -- only the schema extension is reversed.
-- The v1/gen-3.0 protected row corpus (NULL in both new columns) is
-- unaffected by both this migration and its DOWN. No INSERT/UPDATE/DELETE of
-- kala_gochara_windows/kala_gochara_windows_v2 rows in either direction -- the
-- protection triggers (migrations 540/566) are never invoked by DDL.
-- =============================================================================
