-- 641_nirmana_owave_wp2_disposition.sql
--
-- NIRMANA_UNIFIED_ELEVATION_PLAN_v2_0.md §3.2 (O-wave WP-2, delta-skip).
-- Transaction ownership belongs to platform/scripts/migrate.ts.
--
-- Records, per (run_id, asset_id), the O-wave WP-3 disposition taxonomy
-- (build | skip_no_delta | deferred_no_writer | withheld_protected | dormant
-- | out_of_domain | blocked_dependency) at EXECUTION time. WP-3 (migration-
-- free, plan.ts-only) computes the same taxonomy at PLAN time, in memory,
-- for the cockpit UI; this column is the durable execution-time record WP-2's
-- acceptance criterion asks for ("record disposition skip_no_delta -- run
-- row + tracker"). NULL means "no disposition recorded" -- a row from before
-- this migration, or an asset whose execution path doesn't set it (probes;
-- future non-'build'/'skip_no_delta' executor-side dispositions are plan.ts's
-- domain, not asset_runner.py's).

ALTER TABLE build_run_assets
    ADD COLUMN IF NOT EXISTS disposition TEXT;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'build_run_assets_disposition_check'
    ) THEN
        ALTER TABLE build_run_assets
            ADD CONSTRAINT build_run_assets_disposition_check
            CHECK (disposition IS NULL OR disposition IN (
                'build', 'skip_no_delta', 'deferred_no_writer', 'withheld_protected',
                'dormant', 'out_of_domain', 'blocked_dependency'
            ));
    END IF;
END $$;

COMMENT ON COLUMN build_run_assets.disposition IS
    'O-wave WP-2/WP-3: the AssetDisposition taxonomy value asset_runner.py recorded for this execution. Set to skip_no_delta by the pre-execution delta-skip gate (WP-2 §3.2); NULL for rows predating this migration or execution paths that do not set it.';

-- Forward reversal (safe at any time -- the column is additive and read-only
-- outside this migration's writers): DROP CONSTRAINT
-- build_run_assets_disposition_check, then DROP COLUMN
-- build_run_assets.disposition.
