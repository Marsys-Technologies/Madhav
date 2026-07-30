-- Migration 467: asset_throughput CHECK constraint — add 'incomplete' state
-- (SATYA-DIPA, 2026-07-29)
--
-- Purpose: the no-op-completion rescue in asset_runner.py (`_run_data_writer`,
-- D-1.6 root-cause fix) reclassifies a 0-rows-this-run 'dormant' result to 'lit'
-- whenever the asset's data table has any rows present. That rescue exists for a
-- real reason (a resumable writer, e.g. ka_sangam/ka_gochara_sweep, can legitimately
-- report 0 rows because its full substep plan was already committed in a prior
-- attempt) but never verified that the substep plan was ACTUALLY complete before
-- promoting — so a genuinely partial build (some substeps done, rows present from
-- those, substeps still remaining) could be marked 'lit' too, the same class of
-- defect D-1.6 itself was, silently unblocking downstream dependents on incomplete
-- data.
--
-- The SATYA-DIPA fix (asset_runner.py:596-630, the one authorized freeze exception
-- per SATYA_DIPA_BRIEF_v1_0.md §9.1) now checks substep-plan completeness (for
-- has_substeps=true writers only — has_substeps=false/NULL writers are unaffected,
-- "no substep plan defined behaves as before") before promoting. When rows are
-- present but the writer's own plan_substeps(ctx) reports substeps still
-- remaining, the asset must NOT become 'lit' (would falsely unblock downstream)
-- and must NOT become 'dormant' (that state means "ran, produced nothing, data
-- absent" — false here, since data IS partially present; 'dormant' also does not
-- convey "a rebuild is needed to finish", inviting the same D-1.6-style confusion
-- in the other direction). A new, honest, deliberately-chosen state is required:
--
--   'incomplete' — ran, produced 0 net rows THIS attempt, some data IS present
--   from earlier committed substeps, but the writer's own substep plan reports
--   work still remaining. NOT in the ('lit','service_ok') dependency-satisfied
--   allowlist read by runner.py's out-of-plan dependency seed and
--   staleness.py's downstream-stale cascade (both allowlist-based, not
--   deny-list-based — no change needed there), so downstream deps correctly
--   stay BLOCKED until a future build actually finishes the plan. Distinct from
--   'error' (no exception occurred; this is not a crash) and 'dormant' (data is
--   not absent).
--
-- CLAUDE.md §N.4 vocabulary-drift discipline: the writer vocabulary (states a
-- writer's outcome can honestly map to) and the CHECK constraint must agree —
-- applying the audit pattern from the prior wave (ŚUDDHA-VĀCA) so this fix does
-- not itself become a vocabulary-drift defect.
--
-- Idempotent: DROP + re-ADD is safe to re-run (Postgres has no
-- ADD CONSTRAINT IF NOT EXISTS; guard via catalog check instead).

BEGIN;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'asset_throughput_state_check'
  ) THEN
    ALTER TABLE asset_throughput DROP CONSTRAINT asset_throughput_state_check;
  END IF;

  ALTER TABLE asset_throughput
    ADD CONSTRAINT asset_throughput_state_check
    CHECK (state = ANY (ARRAY['dormant'::text, 'building'::text, 'lit'::text,
                               'stale'::text, 'error'::text, 'incomplete'::text]));
END $$;

COMMENT ON CONSTRAINT asset_throughput_state_check ON asset_throughput IS
  'SATYA-DIPA (mig 467): added ''incomplete'' — a genuinely partial substep-plan '
  'build with some data present, distinct from dormant (no data) and error (crash). '
  'Deliberately excluded from the (lit, service_ok) dependency-satisfied allowlist.';

COMMIT;

-- ROLLBACK:
-- BEGIN;
-- UPDATE asset_throughput SET state = 'dormant' WHERE state = 'incomplete';
-- ALTER TABLE asset_throughput DROP CONSTRAINT asset_throughput_state_check;
-- ALTER TABLE asset_throughput
--   ADD CONSTRAINT asset_throughput_state_check
--   CHECK (state = ANY (ARRAY['dormant'::text, 'building'::text, 'lit'::text,
--                              'stale'::text, 'error'::text]));
-- COMMIT;
