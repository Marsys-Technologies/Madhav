-- Migration 572: brahma_prospective_ledger — delete 6 empty-daterange rows + CHECK guard
-- ======================================================================================
-- EKAVĀKYATĀ campaign, Stream C (ṚTA), lane C-01.
-- PRATINIDHI sign-off: EKV-R-C01-001 (required before merge — product-table write).
--
-- ROOT CAUSE (C-02 diagnosis, 2026-08-16):
--   w45_post_fit_rebuild.py (gochara_v3_w45_builder) calls:
--     daterange(window_start, window_end)          -- default [) bounds
--   When the underlying gochara elevation forecast yields a SINGLE-DAY window
--   (window_start == window_end), PostgreSQL evaluates
--     daterange('2068-09-04', '2068-09-04')  →  empty
--   because [d, d) by definition contains no dates.
--
--   The existing `brahma_prospective_ledger_shape_fields_check` constraint requires
--   `upper(observation_window) > lower(observation_window)` for 'interval'-shaped rows,
--   but upper()/lower() on an empty range both return NULL, so NULL > NULL = NULL,
--   and PostgreSQL's CHECK semantics treat NULL as a PASS — allowing the broken rows in.
--
--   Six such rows were inserted on 2026-08-11 23:34:13 UTC by filed_by='w45_post_fit_rebuild':
--     4 on the native chart   (482012f1-710e-4a25-994a-93821f5871aa)
--     2 on the comparison chart (1c826d5a-41cb-4450-b4dc-59d440e5f75a)
--
--   These rows:
--     - crash standing_predictions_read (prospective_ledger.ts parseDaterange at :758-760)
--     - can never be matched or resolved (empty observation_window = no dates qualify)
--     - are in lifecycle_status='open' so they count against real ledger metrics
--
-- REPAIR (idempotent — safe to re-apply after rows are already deleted):
--   1. DELETE the 6 broken rows (identified by unique as_of timestamp + isempty check).
--   2. ADD CHECK (NOT isempty(observation_window)) so future empty ranges are rejected at
--      INSERT time before they reach application code.
--      - NULL observation_window: isempty(NULL) = NULL; NOT NULL = NULL → CHECK passes.
--        This correctly allows 'chain'-shape rows where observation_window IS NULL.
--      - Non-empty ranges: isempty(valid_range) = FALSE; NOT FALSE = TRUE → CHECK passes.
--      - Empty ranges: isempty(empty) = TRUE; NOT TRUE = FALSE → CHECK REJECTS. ✓
--
-- WRITER FIX bundled in same PR (C-02):
--   w45_post_fit_rebuild.py gains a pre-INSERT guard:
--     if window_end <= window_start: window_end = window_start + timedelta(days=1)
--   This ensures the minimum interval-shape filing is [d, d+1) = 1 day, consistent
--   with all existing valid rows (which use [) bounds, lower_inc=t, upper_inc=f).
--
-- §N.4 VERIFICATION CONTRACT (post-deploy assertions — run by E):
--   1. SELECT count(*) FROM _migrations_applied WHERE filename = '572_ekv_c01_ledger_empty_daterange_repair.sql';
--      → Must return 1.
--   2. SELECT count(*) FROM brahma_prospective_ledger WHERE isempty(observation_window);
--      → Must return 0.
--   3. Negative-insert rejection test:
--      INSERT INTO brahma_prospective_ledger (..., observation_window, ...) VALUES
--        (..., 'empty'::daterange, ...);
--      → Must be rejected with a CHECK constraint violation.
--   4. SELECT count(*) FROM brahma_prospective_ledger WHERE lifecycle_status = 'open';
--      → Must be 29 (was 35 before; 6 deleted = 29 remaining).

-- ─── STEP 1: Delete the 6 broken rows ──────────────────────────────────────────────────
-- Identified by: isempty(observation_window) AND the exact batch timestamp.
-- Idempotent: DELETE WHERE has no effect if rows are already gone.
DELETE FROM brahma_prospective_ledger
WHERE isempty(observation_window)
  AND filed_by = 'w45_post_fit_rebuild'
  AND generator_class = 'engine'
  AND filing_method = 'explicit_filing_tool';

-- Verify we deleted exactly 0 or 6 rows (no other empty-range rows should exist).
-- Abort if any empty-range rows remain from OTHER sources (conservative guard).
DO $$
DECLARE
  remaining INT;
BEGIN
  SELECT count(*) INTO remaining
  FROM brahma_prospective_ledger
  WHERE isempty(observation_window);

  IF remaining > 0 THEN
    RAISE EXCEPTION
      'Migration 572 safety abort: % empty-daterange row(s) remain in '
      'brahma_prospective_ledger from unexpected sources. Manual investigation required.',
      remaining;
  END IF;
END
$$;

-- ─── STEP 2: Add CHECK constraint ──────────────────────────────────────────────────────
-- Idempotent: skip if constraint already exists (re-apply safe).
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conrelid = 'brahma_prospective_ledger'::regclass
      AND conname  = 'brahma_prospective_ledger_no_empty_window'
  ) THEN
    ALTER TABLE brahma_prospective_ledger
      ADD CONSTRAINT brahma_prospective_ledger_no_empty_window
      CHECK (NOT isempty(observation_window));
  END IF;
END
$$;
