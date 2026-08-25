-- Migration 595: Nirmana F0 immutable build-run manifest.
--
-- New runs persist the exact ordered waves, per-asset scope, and declared
-- dependencies accepted at dispatch. Existing historical runs remain readable,
-- but the runner rejects an absent/tampered manifest rather than silently
-- recreating a plan from the mutable asset_registry.

ALTER TABLE build_runs
  ADD COLUMN IF NOT EXISTS plan_manifest JSONB,
  ADD COLUMN IF NOT EXISTS plan_manifest_digest TEXT;

ALTER TABLE build_runs
  DROP CONSTRAINT IF EXISTS build_runs_plan_manifest_pair_check,
  ADD CONSTRAINT build_runs_plan_manifest_pair_check CHECK (
    (plan_manifest IS NULL) = (plan_manifest_digest IS NULL)
  ),
  DROP CONSTRAINT IF EXISTS build_runs_plan_manifest_object_check,
  ADD CONSTRAINT build_runs_plan_manifest_object_check CHECK (
    plan_manifest IS NULL OR jsonb_typeof(plan_manifest) = 'object'
  ),
  DROP CONSTRAINT IF EXISTS build_runs_plan_manifest_digest_check,
  ADD CONSTRAINT build_runs_plan_manifest_digest_check CHECK (
    plan_manifest_digest IS NULL OR plan_manifest_digest ~ '^[0-9a-f]{64}$'
  );

CREATE OR REPLACE FUNCTION reject_build_run_manifest_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF OLD.plan_manifest IS NOT NULL
     AND (
       NEW.plan IS DISTINCT FROM OLD.plan
       OR NEW.plan_manifest IS DISTINCT FROM OLD.plan_manifest
       OR NEW.plan_manifest_digest IS DISTINCT FROM OLD.plan_manifest_digest
     ) THEN
    RAISE EXCEPTION 'build run % frozen manifest is immutable', OLD.id
      USING ERRCODE = 'check_violation';
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_build_runs_manifest_immutable ON build_runs;
CREATE TRIGGER trg_build_runs_manifest_immutable
BEFORE UPDATE OF plan, plan_manifest, plan_manifest_digest ON build_runs
FOR EACH ROW
EXECUTE FUNCTION reject_build_run_manifest_mutation();

COMMENT ON COLUMN build_runs.plan_manifest IS
  'Nirmana F0 dispatch-time immutable DAG manifest: ordered waves plus each planned asset scope and dependencies.';
COMMENT ON COLUMN build_runs.plan_manifest_digest IS
  'SHA-256 of the recursively key-sorted canonical JSON plan_manifest; verified by the Python runner before execution.';
