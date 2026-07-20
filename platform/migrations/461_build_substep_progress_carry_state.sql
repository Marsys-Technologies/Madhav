-- Migration 461: build_substep_progress.carry_state — cross-substep continuity carry
-- =====================================================================================
-- D-5 Gochara-Chitra RED-C fix (2026-07-20).
--
-- WHY: ka_gochara_sweep chunks its birth->birth+100y sweep per (event_class x
-- calendar year) for resumability (migration 436's ledger). Before this migration,
-- an `interval`-shaped activation (e.g. major_gain) that was still active at a
-- year-substep's last grid day got closed and served as a complete window ending
-- exactly on that Dec-31 chunk boundary, and the FOLLOWING year's substep opened a
-- brand-new window on Jan-1 for what was actually the SAME still-firing signal --
-- i.e. the served window boundary was an artifact of how the sweep happens to be
-- chunked for resumability, not a true signal-cessation point (RED-C finding,
-- BRIEF_D5 gate). Two live major_gain windows for chart 482012f1 were each
-- observed at exactly ~365 days, exactly bounded by chunk edges.
--
-- WHAT: a nullable JSONB `carry_state` column on the existing per-substep ledger
-- row, additive-only, generic by design (unused by every writer except
-- ka_gochara_sweep today, same as the table itself). `run_substep()` for a given
-- (chart, event_class, year) substep reads the PRIOR year substep's `carry_state`
-- to learn whether an activation was still open when that chunk ended, continues
-- accumulating the SAME window across the boundary if the new chunk's first grid
-- day is still active (confirming continuity, not assuming it), and only closes
-- the window for real on confirmed signal cessation or the ontology's
-- `duration_prior.max_days` cap -- never on a bare chunk edge. See
-- services/ka_gochara_sweep/shape_output.py (`build_interval_rows` continuity
-- carry) and writer.py (`run_substep`) for the consuming logic.
--
-- Additive-only, idempotent (ADD COLUMN IF NOT EXISTS). No destructive ops. The
-- FROZEN orchestrator / WriterBase contract is untouched (writer still never
-- commits/rollbacks/closes ctx.db_conn; this column is written by the SAME
-- run_substep() upsert that already writes this table, migration 436).

BEGIN;

ALTER TABLE build_substep_progress
    ADD COLUMN IF NOT EXISTS carry_state JSONB;

COMMENT ON COLUMN build_substep_progress.carry_state IS
    'Migration 461: optional per-substep continuity-carry payload, generic by '
    'design. ka_gochara_sweep uses it to carry an interval-shaped activation '
    'still open at a year-substep''s chunk boundary forward into the next '
    'year''s substep, so a served window closes only on confirmed signal '
    'cessation or the event_class''s duration_prior.max_days cap, never on a '
    'bare chunk-boundary artifact (D-5 RED-C fix). NULL for substeps with no '
    'open carry (the common case) and for every writer that does not use this '
    'mechanism.';

COMMIT;

-- =====================================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   ALTER TABLE build_substep_progress DROP COLUMN IF EXISTS carry_state;
--   COMMIT;
-- =====================================================================================
