-- Migration 436: build_substep_progress — cross-attempt substep resumption ledger
-- =============================================================================
-- Doctrine Campaign Night-1, guarded-rebuild infrastructure.
--
-- WHY: heavy multi-substep writers (ka_sangam: 1 near + up to 60 lifetime
-- substeps, each a ~100-year convergence scan) can exceed a single DB
-- connection's survivable lifetime through the Cloud SQL Auth Proxy (a real
-- latent connection-instability defect logged separately in
-- MARSYS_DEFECT_GAP_REGISTER). Before this ledger, every retry attempt re-ran
-- ALL substeps from scratch (the orchestrator's _drive_substeps `completed_keys`
-- resumption hook was never fed), so a writer that could not finish inside one
-- connection lifetime could never finish at all.
--
-- WHAT: a per-(chart, asset, substep) durable record of which substeps have
-- committed, tagged with a build_fingerprint. A writer's plan_substeps() reads
-- this ledger to decide, per §N.3 (delete-then-insert REPLACES, never accretes):
--   * fingerprint matches current build  -> SKIP the recorded substeps (resume)
--   * fingerprint differs (prior build)   -> the writer deletes ALL its rows for
--                                            the chart and replans every substep
--                                            fresh (no stale accretion)
-- run_substep() upserts a row here as its final action, INSIDE the orchestrator-
-- owned per-substep transaction — so a substep's ledger row commits atomically
-- with its data rows (both durable, or both rolled back). The FROZEN orchestrator
-- / WriterBase contract is untouched: the writer still never commits/rollbacks/
-- closes; the orchestrator still owns the transaction + savepoint per substep.
--
-- Generic by design (keyed by asset_id) so any future heavy writer can adopt the
-- same resumption pattern; only ka_sangam uses it today.
--
-- Additive-only, idempotent (CREATE ... IF NOT EXISTS). No destructive ops.

BEGIN;

CREATE TABLE IF NOT EXISTS build_substep_progress (
    chart_id          uuid        NOT NULL,
    asset_id          text        NOT NULL,
    substep_key       text        NOT NULL,
    build_fingerprint text        NOT NULL,
    rows_written      integer     NOT NULL DEFAULT 0,
    completed_at      timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (chart_id, asset_id, substep_key)
);

-- Fast lookup of "all recorded substeps for this chart+asset" (the plan_substeps read).
CREATE INDEX IF NOT EXISTS idx_build_substep_progress_chart_asset
    ON build_substep_progress (chart_id, asset_id);

COMMENT ON TABLE build_substep_progress IS
    'Cross-attempt substep-resumption ledger (migration 436). One row per committed '
    'substep, tagged with build_fingerprint. Read by heavy writers'' plan_substeps() '
    'to resume an interrupted build (matching fingerprint) or replan-all on a changed '
    'build (differing fingerprint); upserted by run_substep() inside the orchestrator-'
    'owned per-substep transaction. FROZEN orchestrator contract untouched.';

COMMIT;
