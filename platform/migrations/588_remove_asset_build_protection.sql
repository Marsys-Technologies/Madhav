-- 588_remove_asset_build_protection.sql
--
-- NIRMĀṆA ELEVATION — remove all per-asset build protection.
--
-- WHY
--   Protection was installed 2026-08-06 (migration 540, ṢAḌ-DARŚANA Phase 1a) and
--   extended 2026-08-11 (migration 566, gen-3.0) to prevent an accidental
--   mis-scoped DELETE/UPDATE/TRUNCATE from destroying expensive-to-rebuild
--   gochara corpora during campaign work.
--
--   The Nirmāṇa elevation campaign rebuilds every asset by design, so a guard
--   that must be overridden on every legitimate write is no longer wanted.
--   Native instruction, 2026-08-23.
--
--   It was also actively harmful in its current form: build_protected_assets
--   registered gen-3.0 protection under asset_id='ka_gochara', while the writer
--   that actually produces gen-3.0 rows is ka_gochara_v3_century_materialize.
--   The trigger could not tell a legitimate write from a destructive one, and
--   left that writer in a permanent BUILD-PROTECTED error on the native chart
--   (Defect D-02).
--
-- SAFETY — what replaces the guard
--   A full logical snapshot of kala_gochara_windows (38,287 v1 rows + 1,884
--   gen-3.0 rows) and build_protected_assets was taken immediately before this
--   migration and verified restorable with pg_restore -l:
--     00_ARCHITECTURE/control/snapshots/20260823_pre_protection_removal/
--       gochara_corpus_and_protection.dump    (16,214,137 bytes)
--
--   STANDING CAUTION, recorded here because the migration is the durable record:
--   ka_gochara_sweep's 38,287 generation='v1' rows have NO registered writer.
--   Its @register was removed at retirement (writers/ka_gochara_sweep.py), so the
--   build system CANNOT regenerate them. The snapshot above is their only
--   recovery path. If those rows are ever needed again and the snapshot is lost,
--   the writer must first be un-retired and a ~30h per-chart sweep re-run.
--
-- IDEMPOTENT: all statements are IF EXISTS / unconditional DELETE.
-- REVERSIBLE: re-apply migrations 540 and 566 to reinstate. If protection is ever
--   reinstated, key it on (table, generation) rather than asset_id, so it cannot
--   again block the writer it is meant to protect.

BEGIN;

-- 1. Row + truncate guards installed by migration 540 (v1 corpus).
DROP TRIGGER IF EXISTS trg_kala_gochara_windows_protect_row      ON kala_gochara_windows;
DROP TRIGGER IF EXISTS trg_kala_gochara_windows_protect_truncate ON kala_gochara_windows;

-- 2. Generation-3.0 row guard installed by migration 566.
DROP TRIGGER IF EXISTS trg_kala_gochara_windows_protect_gen3_row ON kala_gochara_windows;

-- 3. Drop the now-unreferenced trigger functions.
DROP FUNCTION IF EXISTS kala_gochara_windows_protect_row();
DROP FUNCTION IF EXISTS kala_gochara_windows_protect_truncate();
DROP FUNCTION IF EXISTS kala_gochara_windows_protect_gen3_row();

-- 4. Empty the protection registry. The TABLE is retained (not dropped) so the
--    mechanism can be reinstated without a schema change, and so nothing that
--    reads it breaks.
DELETE FROM build_protected_assets;

COMMIT;
