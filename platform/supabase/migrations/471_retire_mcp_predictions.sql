-- Migration 471: retire mcp_predictions — PB-3 (SAMĪKṢĀ) lane L-1
-- Created: 2026-07-28
--
-- DESTRUCTIVE migration (table DROP). Authorized by MEMO_PB-3_0 (Pratinidhi ruling executing
-- OT-11), item 2 — the ONE non-additive migration this wave permits. Every other PB-3
-- migration is additive-only.
--
-- Why mcp_predictions is retired (from MEMO_PB-3_0 §2, evidence X-5):
--   - Sole writers: ppl_writer.ts (logPrediction/recordOutcome) and
--     calibration_producer.ts (recordCalibrationStamp). Both are retired to no-ops in the
--     same L-1 commit (see platform/src/lib/mcp/ppl_writer.ts and
--     platform/src/lib/predictions/calibration_producer.ts).
--   - Self-described in its own origin migration (071) as an interim relay predating §14.
--   - No downstream analytical consumer, no inbound FK.
--   - Content: 12 rows live at BIND (X-5's snapshot said 0 — see MEMO_PB-3_0's BIND-AT-OPEN
--     correction), ALL content-empty calibration stamp rows (every substantive column NULL;
--     only prediction_id/chart_id/logged_at populated). No meaningful data to lose.
--
-- ROLLBACK PATH — implemented EXACTLY as written in MEMO_PB-3_0 §2 "Rollback path":
--   * Pre-migration, inside this same transaction, before the DROP:
--       CREATE TABLE mcp_predictions_retired_backup AS TABLE mcp_predictions;
--     This captures whatever rows are ACTUALLY live at migration time (not a hardcoded
--     assumption of emptiness) plus the column layout verbatim.
--   * To roll back (if ever needed), run the DOWN block below:
--       CREATE TABLE mcp_predictions AS TABLE mcp_predictions_retired_backup;
--     This re-creates the table with its columns and every backed-up row.
--   * IMPORTANT (per MEMO): the SQL rollback ALONE is NOT sufficient. `CREATE TABLE ... AS
--     TABLE ...` restores columns + data but NOT the PRIMARY KEY, the unique/ON CONFLICT
--     index, defaults, or CHECK constraints. AND the code that wrote this table
--     (ppl_writer.ts / calibration_producer.ts) was retired to no-ops in this same L-1
--     commit — resurrecting live writes requires a SEPARATE code-revert (git revert of the
--     L-1 commit that neutered them), not a SQL-only rollback. Do not resurrect the live
--     `mcp_predictions` name without a fresh Pratinidhi ruling (MEMO_PB-3_0 §2, LEDGER_MAP).
--
-- Idempotency: guarded so a re-run does not error. If mcp_predictions no longer exists
-- (already retired), the whole block is a no-op via the DO guard.

BEGIN;

DO $retire$
BEGIN
  IF to_regclass('public.mcp_predictions') IS NULL THEN
    RAISE NOTICE 'mcp_predictions already retired (table absent) — migration 471 is a no-op.';
    RETURN;
  END IF;

  -- (1) Backup FIRST, inside this transaction, before the drop — captures live rows + layout.
  --     Drop any stale backup from a prior aborted attempt so the fresh backup is faithful.
  IF to_regclass('public.mcp_predictions_retired_backup') IS NOT NULL THEN
    DROP TABLE mcp_predictions_retired_backup;
  END IF;
  EXECUTE 'CREATE TABLE mcp_predictions_retired_backup AS TABLE mcp_predictions';

  -- (2) Now drop the retired relay.
  EXECUTE 'DROP TABLE mcp_predictions';

  RAISE NOTICE 'mcp_predictions retired; backup captured as mcp_predictions_retired_backup.';
END
$retire$;

COMMENT ON TABLE mcp_predictions_retired_backup IS
  'PB-3/L-1: pre-retirement backup of mcp_predictions (dropped in migration 471 per '
  'MEMO_PB-3_0). Content-empty calibration stamp rows only. Restore = CREATE TABLE '
  'mcp_predictions AS TABLE mcp_predictions_retired_backup (columns+rows only; PK/indexes/'
  'defaults NOT restored) + a git revert of the ppl_writer/calibration_producer no-op '
  'commit. Do not resurrect the live name without a fresh Pratinidhi ruling.';

COMMIT;

-- DOWN (manual rollback — audit + local throwaway-DB rollback testing only):
-- BEGIN;
-- CREATE TABLE mcp_predictions AS TABLE mcp_predictions_retired_backup;
-- -- NOTE: PK, the (chart_id,ayanamsha_id,query_hash,salience_formula_version) partial unique
-- -- index, column defaults, and any CHECK constraints are NOT restored by CREATE TABLE AS.
-- -- A faithful schema restore would re-apply migration 071's original DDL. And the writer
-- -- code (ppl_writer.ts / calibration_producer.ts) must be git-reverted separately — the SQL
-- -- rollback alone does not restore live writes. (MEMO_PB-3_0 §2.)
-- COMMIT;
