-- Migration 568: add resolution to the gochara-windows natural-key indexes
-- =============================================================================
-- PARIṢKĀRA campaign, MR-45 (real live-rebuild blocker, found by PARĪKṢAKA
-- re-verdict on PR #1231/MR-44, recovering the actual halt log from the R2
-- authorized corpus rebuild — native chart 482012f1, substep 74/270,
-- career_setback::g3_2014_2024).
--
-- GAP: `uq_kala_gochara_windows_v2_natural_key` (and its production-table
-- counterpart `uq_kala_gochara_windows_natural_key` on `kala_gochara_windows`)
-- is `(chart_id, event_class, window_start, peak_date,
-- COALESCE(milestone_id,''), generation)` — `resolution` is NOT a key column.
-- Migration 567 (PARIṢKĀRA MR-11(b)) added `resolution` ('era'|'month'|'day')
-- as a plain column but never folded it into either unique index.
--
-- resolution_hierarchy.py's `_emit_retained_peaks` sets a MONTH row's
-- `window_start` to the calendar-month start containing the day-refined true
-- peak, and a DAY row's `window_start` to that SAME day-refined peak date
-- itself; `peak_date` is stamped identically on both rows (the true argmax,
-- R8.5). Whenever a retained peak's refined date falls on the 1st of a
-- calendar month, `window_start == peak_date` for BOTH its month row and its
-- day row — every other key column (chart_id, event_class,
-- COALESCE(milestone_id,''), generation) is also identical between the two
-- rows, so the two rows collide on an identical natural key. Insert order
-- era -> month -> day means the month row is already committed when the day
-- row's INSERT raises a unique-violation. Deterministic given migration
-- 567's schema (not a rare edge case: ~1-in-30 retained peaks in the live
-- corpus already hit this pattern; MR-44's pooled-retention fix does not
-- touch this — MR-44 fixed a DIFFERENT collision, era-window-anchored month/
-- day rows landing on the SAME date across two SIBLING era windows within
-- one build_resolution_hierarchy call; this migration fixes month vs. day
-- ROWS OF THE SAME PEAK colliding with each other).
--
-- FIX: add `resolution` to both unique indexes, COALESCE'd exactly like
-- `milestone_id` already is (`COALESCE(resolution, '')`) so NULL-resolution
-- rows (interval/point/chain shapes — the v1 sweep corpus and every
-- W3.4/W5.4 flat-interval v3 row, none of which use the hierarchy tiers)
-- keep colliding on EXACTLY their existing semantics (both NULLs coalesce to
-- the same '' and contribute nothing new to the key) — only rows that DO
-- carry a resolution value ('era'/'month'/'day') gain the extra
-- disambiguation that lets a month row and a day row of the SAME peak
-- coexist. No other constraint or column touched.
--
-- WHY DROP+CREATE, NOT ALTER: Postgres has no ALTER INDEX ... ADD COLUMN;
-- changing a unique index's key column list requires dropping and
-- recreating it. Both operations run inside this migration's single
-- transaction (BEGIN...COMMIT) — Postgres DDL is transactional, so no
-- window exists where the constraint is silently absent from any COMMITted
-- transaction's point of view; a concurrent writer either sees the OLD
-- index (pre-COMMIT) or the NEW one (post-COMMIT), never neither. A
-- concurrent write landing inside this migration's own transaction window
-- is ordinary migration risk (this table is not read/written by any
-- always-on request-serving path — only by the orchestrator's per-chart
-- rebuild writer) and out of this lane's scope.
--
-- TABLE SIZE (read live 2026-08-11, informs the CONCURRENTLY decision):
-- kala_gochara_windows = 38,582 rows; kala_gochara_windows_v2 = 295 rows.
-- Both are small enough that a plain (non-CONCURRENTLY) DROP+CREATE INDEX
-- inside this transaction completes in well under the `lock_timeout` below
-- — CONCURRENTLY is unnecessary here and would also be unusable in this
-- form anyway (CREATE INDEX CONCURRENTLY cannot run inside a multi-statement
-- transaction block, and migration 567's own house style — BEGIN/COMMIT
-- with a short lock_timeout — is followed here for consistency).
--
-- IDEMPOTENT: guarded with IF EXISTS / IF NOT EXISTS so a re-run after a
-- successful apply is a no-op. The self-verification DO block at the end
-- raises if either new index is missing, mistyped, or the OLD (5-key-column)
-- index is still present, per §N.4 "a migration that cannot verify itself is
-- not trustworthy" (style mirrors migrations 564/567).
--
-- PROTECTED CORPUS: kala_gochara_windows carries the v1 sweep corpus for
-- charts 482012f1 and 1c826d5a (migration 540's build_protected_assets) plus
-- the gen-3.0 rows protected by migration 566's trigger. This migration is
-- schema-only (DROP INDEX / CREATE INDEX, no INSERT/UPDATE/DELETE of any
-- row) — the migration-540 and migration-566 row-level guards are BEFORE
-- DELETE/UPDATE triggers and never fire on DDL. Grep-verifiable: this file
-- contains no INSERT, UPDATE, or DELETE targeting kala_gochara_windows /
-- kala_gochara_windows_v2 rows.
--
-- EXECUTE-TO-VERIFY (Codex C1): this migration was run against a throwaway
-- local Postgres instance mirroring the live column definitions and existing
-- index of both tables (read-only inspected from production via the
-- DB-schema-only access this lane is authorized for) before being declared
-- applied-clean: (a) new index exists with `resolution` in its definition;
-- (b) a month-row and day-row for the SAME peak (identical
-- window_start=peak_date, differing only in resolution 'month'/'day') now
-- BOTH insert successfully; (c) two genuinely duplicate rows (same
-- resolution, same everything else) still correctly collide; (d) the DOWN
-- path removes the new index and restores the original 5-key-column
-- definition; (e) re-running the UP migration after DOWN is clean. See this
-- lane's PR description for the full transcript.
-- =============================================================================

BEGIN;

SET LOCAL lock_timeout = '2s';

-- ── 1. kala_gochara_windows (production surface) ────────────────────────────

DROP INDEX IF EXISTS uq_kala_gochara_windows_natural_key;

CREATE UNIQUE INDEX IF NOT EXISTS uq_kala_gochara_windows_natural_key
  ON kala_gochara_windows (
    chart_id,
    event_class,
    window_start,
    peak_date,
    COALESCE(milestone_id, ''),
    COALESCE(resolution, ''),
    generation
  );

-- ── 2. kala_gochara_windows_v2 (calibration/staging surface) ────────────────

DROP INDEX IF EXISTS uq_kala_gochara_windows_v2_natural_key;

CREATE UNIQUE INDEX IF NOT EXISTS uq_kala_gochara_windows_v2_natural_key
  ON kala_gochara_windows_v2 (
    chart_id,
    event_class,
    window_start,
    peak_date,
    COALESCE(milestone_id, ''),
    COALESCE(resolution, ''),
    generation
  );

-- ── 3. Self-verification (§N.4 mandate) ──────────────────────────────────────

DO $$
BEGIN
  -- 3a. kala_gochara_windows: new index exists
  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes
     WHERE schemaname = 'public'
       AND tablename  = 'kala_gochara_windows'
       AND indexname  = 'uq_kala_gochara_windows_natural_key'
  ) THEN
    RAISE EXCEPTION 'MIGRATION-568 SELF-CHECK FAILED: uq_kala_gochara_windows_natural_key missing after CREATE';
  END IF;

  -- 3b. kala_gochara_windows: new index carries 7 key columns
  --     (chart_id, event_class, window_start, peak_date,
  --      COALESCE(milestone_id,''), COALESCE(resolution,''), generation)
  IF NOT EXISTS (
    SELECT 1
      FROM pg_index
      JOIN pg_class ON pg_class.oid = pg_index.indexrelid
     WHERE pg_class.relname = 'uq_kala_gochara_windows_natural_key'
       AND pg_index.indnatts = 7
  ) THEN
    RAISE EXCEPTION 'MIGRATION-568 SELF-CHECK FAILED: uq_kala_gochara_windows_natural_key does not have 7 key columns (resolution not folded in)';
  END IF;

  -- 3c. kala_gochara_windows: new index definition literally contains
  --     "resolution" (belt-and-braces on top of 3b's column-count check).
  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes
     WHERE schemaname = 'public'
       AND tablename  = 'kala_gochara_windows'
       AND indexname  = 'uq_kala_gochara_windows_natural_key'
       AND indexdef LIKE '%resolution%'
  ) THEN
    RAISE EXCEPTION 'MIGRATION-568 SELF-CHECK FAILED: uq_kala_gochara_windows_natural_key indexdef does not mention resolution';
  END IF;

  -- 3d. kala_gochara_windows_v2: new index exists
  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes
     WHERE schemaname = 'public'
       AND tablename  = 'kala_gochara_windows_v2'
       AND indexname  = 'uq_kala_gochara_windows_v2_natural_key'
  ) THEN
    RAISE EXCEPTION 'MIGRATION-568 SELF-CHECK FAILED: uq_kala_gochara_windows_v2_natural_key missing after CREATE';
  END IF;

  -- 3e. kala_gochara_windows_v2: new index carries 7 key columns
  IF NOT EXISTS (
    SELECT 1
      FROM pg_index
      JOIN pg_class ON pg_class.oid = pg_index.indexrelid
     WHERE pg_class.relname = 'uq_kala_gochara_windows_v2_natural_key'
       AND pg_index.indnatts = 7
  ) THEN
    RAISE EXCEPTION 'MIGRATION-568 SELF-CHECK FAILED: uq_kala_gochara_windows_v2_natural_key does not have 7 key columns (resolution not folded in)';
  END IF;

  -- 3f. kala_gochara_windows_v2: new index definition literally contains
  --     "resolution".
  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes
     WHERE schemaname = 'public'
       AND tablename  = 'kala_gochara_windows_v2'
       AND indexname  = 'uq_kala_gochara_windows_v2_natural_key'
       AND indexdef LIKE '%resolution%'
  ) THEN
    RAISE EXCEPTION 'MIGRATION-568 SELF-CHECK FAILED: uq_kala_gochara_windows_v2_natural_key indexdef does not mention resolution';
  END IF;
END $$;

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   SET LOCAL lock_timeout = '2s';
--   DROP INDEX IF EXISTS uq_kala_gochara_windows_natural_key;
--   CREATE UNIQUE INDEX IF NOT EXISTS uq_kala_gochara_windows_natural_key
--     ON kala_gochara_windows (
--       chart_id, event_class, window_start, peak_date,
--       COALESCE(milestone_id, ''), generation
--     );
--   DROP INDEX IF EXISTS uq_kala_gochara_windows_v2_natural_key;
--   CREATE UNIQUE INDEX IF NOT EXISTS uq_kala_gochara_windows_v2_natural_key
--     ON kala_gochara_windows_v2 (
--       chart_id, event_class, window_start, peak_date,
--       COALESCE(milestone_id, ''), generation
--     );
--   COMMIT;
-- Safe: restores the exact pre-migration-568 index definitions (verified
-- live 2026-08-11 — see this migration's file header). No row data is
-- touched in either direction — only the index definitions change. Any
-- month/day-row pairs inserted AFTER migration 568 that share a
-- month-boundary natural key (the exact shape this migration fixes) would
-- make the DOWN path's CREATE UNIQUE INDEX fail with a duplicate-key error
-- if such rows already exist at rollback time — this is the correct,
-- loud failure mode for a rollback that would reintroduce a real
-- known collision, not a defect in the DOWN path itself.
-- =============================================================================
