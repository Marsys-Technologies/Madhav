-- Migration 1094 — asset_throughput.duration_seconds (Nirmāṇa engine packet A1)
--
-- Before this migration, asset_throughput.rows_per_second (present since migration 169,
-- 2026-06-06) was NULL for 100% of rows across all six layers: the column existed but no
-- code path anywhere in the engine ever wrote it, and asset_throughput had no duration or
-- started_at column at all to compute a rate from. This migration adds the missing column
-- so the engine (asset_runner.py) has somewhere to persist a duration.
--
-- What actually populates it (corrected here after gate review A1_rereview_20260926T132725Z.md
-- N-4 found this header still describing A1's original, superseded design): the ORCHESTRATOR
-- itself measures `time.monotonic()` around its own call into `writer.run_substep(ctx, step)`
-- in asset_runner.py `_drive_substeps`, summed across every executed sub-step. This is a
-- single call site for BOTH frozen writer shapes: `WriterBase.plan_substeps`/`run_substep`
-- default to exactly one sub-step whose default body is `self.run(ctx)`, so a light writer's
-- entire `run()` executes inside that same timed bracket as a heavy writer's `run_substep()`.
-- Coverage is therefore universal and does not depend on which shape a writer uses, or on
-- whether it self-reports anything at all. `WriterResult.duration_seconds` (the frozen
-- contract's own field) still exists and writers may still set it, but the engine no longer
-- reads it for this column — a writer's self-report is never persisted, only ever the
-- engine's own measurement. Written at the completion-write site for EVERY completion state
-- that write reaches, not only strictly-successful builds — see the corrected COMMENT ON
-- blocks below for the full contract (NULL semantics, the degraded-environment case, etc).
--
-- Numbered max+1 scanned across BOTH platform/migrations/ and platform/supabase/migrations/ at
-- execution time (max found: 1093, platform/supabase/migrations/1093_kala_convergence_episodes.sql).

ALTER TABLE asset_throughput
    ADD COLUMN IF NOT EXISTS duration_seconds double precision;

COMMENT ON COLUMN asset_throughput.duration_seconds IS
    'Wall-clock seconds the ORCHESTRATOR ITSELF measured (time.monotonic() around each '
    'writer.run_substep() call, summed across substeps in asset_runner.py _drive_substeps) for '
    'the asset''s most recent completion write. Set at the completion-write site (asset_runner.py '
    '_run_data_writer) for EVERY completion state that write reaches -- ''lit'', ''dormant'', and '
    '''incomplete'' alike, not only strictly-successful (''lit'') builds -- and at the legacy L1 '
    'telemetry helper (ga_writers/_telemetry.py), which instead relies on its caller to pass an '
    'already-measured duration_seconds (none of its current call sites do, so that path still '
    'always writes NULL). NULL means no completion write has recorded a duration yet -- a failed '
    '(mark_asset_error), orphan-reaped, or watchdog-aborted build never reaches the completion-'
    'write site at all and so leaves this column untouched (NULL by omission, never a fabricated '
    '0). Also NULL, by design, in any environment where this column does not yet exist at the '
    'time the orchestrator process started: the completion write probes for the column once per '
    'process and omits naming it entirely rather than fail the build (see asset_runner.py '
    '_duration_columns_present).';

COMMENT ON COLUMN asset_throughput.rows_per_second IS
    'rows_written / duration_seconds for the asset''s most recent completion write (column has '
    'existed since migration 169; this is the first migration to document a real writer for it -- '
    'see migration 1094 / A1 packet). Written for EVERY completion state the completion write '
    'reaches -- ''lit'', ''dormant'', and ''incomplete'' alike, not only strictly-successful builds. '
    'Computed whenever duration_seconds is a positive, finite number -- INCLUDING when '
    'rows_written is 0: that is an honest measured rate of 0.0 (the writer genuinely ran and wrote '
    'nothing this run, e.g. a 0-row service-asset health probe), never NULL. NULL (never 0, never '
    'a fabricated value) only when duration_seconds itself is NULL, zero, negative, or non-finite '
    '-- see the duration_seconds comment for when that column itself is NULL.';
