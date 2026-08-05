-- Migration 539: chart_facts.verification_pass_status CHECK constraint
-- =============================================================================
-- DEFECT SALVAGE campaign, S8 (last step; needs S5/S6/S7 settled or halted — S5 drained the
-- estate, S6 backfilled ga_structural across all 3 charts, S7 halted for a native decision on
-- ga_sensitive; none of those leave a chart_facts row this constraint would reject).
--
-- chart_facts has carried NO verification_pass_status CHECK since the table's creation
-- (brahmagyan/verification_vocab.py's own module docstring: "chart_facts and every bodha_* table
-- carry NO constraint at all" — one of six documented sources of the pre-Ruling-13 vocabulary
-- disagreement). This migration closes that gap using the FULL 13-value settled vocabulary
-- (ALL_STATUSES in verification_vocab.py), not the narrower 4-value RESTRICTED_TABLE_VOCAB that
-- chart_dashas/chart_divisionals enforce — copying the restricted set here would repeat the exact
-- "hand-written set describing a row shape the DB never had" defect the vocab module's own
-- docstring warns against (chart_facts legitimately stores all 13 members; chart_dashas/
-- chart_divisionals never see the other 9).
--
-- NOT VALID: chart_facts is 684MB live (2026-08-05 measurement; 481MB when this migration was
-- first drafted the previous session). A plain ADD CONSTRAINT would take ACCESS EXCLUSIVE for the
-- full-table validation scan. NOT VALID adds the constraint (enforced on all NEW/UPDATEd rows
-- immediately) without scanning existing rows or taking that lock. VALIDATE CONSTRAINT against
-- existing rows is deliberately deferred to a separate future migration, once this is deployed
-- and confirmed stable — matching the two-phase pattern this table's size calls for, not
-- expanding this migration's scope.
--
-- Runtime-verified immediately before this migration was authored (DEFECT SALVAGE S8, 2026-08-05):
-- zero live chart_facts rows violate this constraint. S5's drain (59,282 rows) and S6's
-- ga_structural backfill (310,128 rows across all 3 charts) are the reason that's true now — both
-- ran earlier in the same campaign, specifically to make this migration safe to add.
--
-- lock_timeout: NOT VALID skips the validation scan, but the ALTER TABLE still needs a brief
-- ACCESS EXCLUSIVE to write the constraint into the catalog. On a live table, if any other
-- transaction holds a lock on chart_facts at that moment, this DDL queues for it — and Postgres's
-- FIFO lock queue means every NEW query against chart_facts issued after that queues behind the
-- pending DDL too, turning a cheap catalog update into a stall/pileup. lock_timeout aborts this
-- transaction cleanly instead of queueing indefinitely; migration_number_guard-reviewed addition
-- (migration-guard pass, DEFECT SALVAGE S8, WARN-2), scoped to this transaction only.
-- =============================================================================

BEGIN;

SET LOCAL lock_timeout = '2s';

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'chart_facts_verification_pass_status_check'
      AND conrelid = 'chart_facts'::regclass
  ) THEN
    ALTER TABLE chart_facts
      ADD CONSTRAINT chart_facts_verification_pass_status_check
      CHECK (verification_pass_status IN (
        'two_pass_verified',
        'classical_match',
        'divergent_flagged',
        'single',
        'single_pass',
        'documented_approximation',
        'computed_extension',
        'floored',
        'not_defined_for_nodes',
        'scope_cap_sentinel',
        'skipped_malformed_source',
        'external_computation_required',
        'pending_w3_verification'
      ))
      NOT VALID;
  END IF;
END $$;

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   ALTER TABLE chart_facts DROP CONSTRAINT IF EXISTS chart_facts_verification_pass_status_check;
--   COMMIT;
-- =============================================================================
