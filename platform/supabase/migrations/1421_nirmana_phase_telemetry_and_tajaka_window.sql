-- Migration 1421: Durable phase telemetry on build_run_assets and dynamic ga_tajaka window
--
-- Consolidated additive migration (NIR-03 + NIR-08):
--   Part A (NIR-03): Adds durable phase, substep, and per-phase wall-clock duration
--     columns to public.build_run_assets so reload/reconnect/SSE-fallback reads show
--     truthful in-flight phase progress and measured phase timings without relying on
--     ephemeral SSE memory or transaction-start NOW().
--   Part B (NIR-08): Updates asset_registry.ga_tajaka target_floor to NULL and
--     syncs volume_explanation with platform/scripts/seed/asset_registry_seed.ts so
--     younger charts do not emit false below-floor warnings while pre-insert window
--     completeness checks enforce contiguous gap-free years per frame.

SET LOCAL lock_timeout = '5s';

-- ── Part A: NIR-03 Durable phase & substep telemetry on build_run_assets ─────

ALTER TABLE build_run_assets
    ADD COLUMN IF NOT EXISTS phase text,
    ADD COLUMN IF NOT EXISTS substep_index integer,
    ADD COLUMN IF NOT EXISTS substep_total integer,
    ADD COLUMN IF NOT EXISTS substep_label text,
    ADD COLUMN IF NOT EXISTS compute_ms integer,
    ADD COLUMN IF NOT EXISTS write_ms integer,
    ADD COLUMN IF NOT EXISTS verify_ms integer,
    ADD COLUMN IF NOT EXISTS publish_ms integer;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'build_run_assets_phase_check'
    ) THEN
        ALTER TABLE build_run_assets
            ADD CONSTRAINT build_run_assets_phase_check
            CHECK (phase IS NULL OR phase IN (
                'queued',
                'computing',
                'writing',
                'verifying',
                'publishing',
                'complete',
                'skipped',
                'error',
                'aborted'
            ));
    END IF;
END $$;

COMMENT ON COLUMN build_run_assets.phase IS
    'NIR-03: durable orchestrator execution phase (queued, computing, writing, verifying, publishing, complete, skipped, error, aborted). Written out-of-band during deferred-commit integrity runs so live progress survives reload without weakening writer rollback atomicity.';
COMMENT ON COLUMN build_run_assets.substep_index IS
    'NIR-03: 1-based index of the current or most recently executed writer substep for this run asset.';
COMMENT ON COLUMN build_run_assets.substep_total IS
    'NIR-03: total planned substep count reported by writer.plan_substeps(ctx) for this run asset.';
COMMENT ON COLUMN build_run_assets.substep_label IS
    'NIR-03: human-readable label of the current or most recently executed writer substep.';
COMMENT ON COLUMN build_run_assets.compute_ms IS
    'NIR-03: wall-clock milliseconds measured by the orchestrator for the setup/planning (computing) phase.';
COMMENT ON COLUMN build_run_assets.write_ms IS
    'NIR-03: wall-clock milliseconds measured by the orchestrator across executed writer substeps (writing phase).';
COMMENT ON COLUMN build_run_assets.verify_ms IS
    'NIR-03: wall-clock milliseconds measured by the orchestrator for integrity/completeness verification (verifying phase).';
COMMENT ON COLUMN build_run_assets.publish_ms IS
    'NIR-03: wall-clock milliseconds measured by the orchestrator for throughput/receipt persistence and commit (publishing phase).';

-- ── Part B: NIR-08 Dynamic ga_tajaka window in asset_registry ────────────────

DO $$
DECLARE
  v_floor bigint;
  v_expl  text;
  v_rows  integer;
  c_target_expl CONSTANT text :=
    'Dynamic per-chart varsha window = 1..(reference_year - birth_year + 6) × 5 canonical ayanamshas (e.g. 240 rows for 1984 birth, 305 for 1971, 180 for 1996, 60 for 2020 in 2026); target_floor is NULL so younger charts do not emit false below-floor warnings while pre-insert completeness checks enforce contiguous gap-free years per frame. Windowed storage — only varshas inside the precomputed window are stored; varshas outside that window are NOT computed on-demand (get_tajik.ts honestly reports them via its own empty_reason disclosure).';
BEGIN
  SELECT target_floor, volume_explanation
    INTO v_floor, v_expl
    FROM asset_registry
   WHERE asset_id = 'ga_tajaka'
     FOR UPDATE;

  IF NOT FOUND THEN
    RAISE NOTICE 'nir08: no ga_tajaka registry row; nothing to do';
  ELSIF v_floor IS NULL AND v_expl = c_target_expl THEN
    RAISE NOTICE 'nir08: ga_tajaka already has target_floor=NULL and updated volume_explanation; nothing to do';
  ELSIF v_floor IS NOT NULL AND v_floor <> 240 THEN
    RAISE NOTICE 'nir08: ga_tajaka target_floor is % (expected 240 or NULL); NO-OP', v_floor;
  ELSE
    UPDATE asset_registry
       SET target_floor = NULL,
           volume_explanation = c_target_expl
     WHERE asset_id = 'ga_tajaka'
       AND (target_floor = 240 OR target_floor IS NULL);
    GET DIAGNOSTICS v_rows = ROW_COUNT;
    IF v_rows <> 1 THEN
      RAISE EXCEPTION 'nir08: ga_tajaka registry update affected % rows (expected 1)', v_rows;
    END IF;
  END IF;
END $$;
