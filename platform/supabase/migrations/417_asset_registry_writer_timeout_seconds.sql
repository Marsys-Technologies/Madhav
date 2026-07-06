-- Migration 417: per-writer timeout budgets in asset_registry
-- (BA Phase-3 RULING JL-023: per-writer timeout budgets + watchdog).
--
-- Root cause (BA Phase-3 Abhinandan diagnostics): the orchestrator watchdog used
-- a single global WRITER_TIMEOUT_SECONDS (default 600s) for EVERY asset. Several
-- writers legitimately run longer than 600s on a full chart build:
--   - ga_dashas   ~5 min (536k+ dasha rows, COPY-heavy)
--   - bo_samskara ~8 min (heavy in-memory pass)
--   - ga_structural — two-pass fact-id verification over a large fact set
-- Under the global 600s budget these were killed mid-build in wave-parallel mode
-- (they only survived under WORKER_LIMIT=1 because serial execution gave each the
-- whole process to itself). A global bump would over-budget every fast writer and
-- let a genuinely-hung fast asset sit for the slowest writer's budget.
--
-- Fix (JL-023): give each asset its OWN budget in asset_registry. The orchestrator
-- watchdog (runner.py execute_dag) reads the per-asset value and still KILLS+FAILS
-- (marks 'error', never hangs) any writer that exceeds ITS budget. Assets without
-- an explicit value fall back to the column default (600s) and then to the
-- WRITER_TIMEOUT_SECONDS env default, so behaviour is unchanged for everything
-- except the three long-runners.
--
-- This is a prerequisite for the parallel restore (WORKER_LIMIT>1): the higher
-- budgets are exactly what let the slow writers survive concurrent scheduling.

BEGIN;

ALTER TABLE asset_registry
  ADD COLUMN IF NOT EXISTS writer_timeout_seconds integer NOT NULL DEFAULT 600;

COMMENT ON COLUMN asset_registry.writer_timeout_seconds IS
  'Per-writer watchdog budget (seconds). Orchestrator kills+fails a writer that '
  'exceeds this. Default 600; long-runners raised per JL-023.';

-- Long-runner budgets (JL-023 explicit set: 1200-1800s).
UPDATE asset_registry SET writer_timeout_seconds = 1800 WHERE asset_id = 'ga_dashas';
UPDATE asset_registry SET writer_timeout_seconds = 1800 WHERE asset_id = 'bo_samskara';
UPDATE asset_registry SET writer_timeout_seconds = 1200 WHERE asset_id = 'ga_structural';

COMMIT;

-- DOWN:
-- ALTER TABLE asset_registry DROP COLUMN IF EXISTS writer_timeout_seconds;
