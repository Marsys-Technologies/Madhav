-- 1034_data_plane_l2_producer_generations.sql
-- DP-SD-015: append-only L2 producer observation receipts.
-- This does not copy or reinterpret L0/L1 rows and does not store temporal
-- activation. Existing L2 output tables and legacy temporal columns remain
-- readable. Apply/reapply is forward-only and idempotent; never applied live by
-- the producer-readiness goal.

CREATE TABLE IF NOT EXISTS data_plane_l2_producer_generations (
  generation_id text NOT NULL,
  asset_id text NOT NULL,
  partition_key text NOT NULL,
  chart_id uuid NOT NULL,
  build_id uuid NOT NULL,
  contract_version text NOT NULL,
  accepted_l0_release text NOT NULL,
  accepted_l1_terminal text NOT NULL,
  calculation_context_id text NOT NULL,
  producer_role text NOT NULL,
  source_digest text NOT NULL CHECK (source_digest ~ '^[0-9a-f]{64}$'),
  rows_inserted bigint NOT NULL DEFAULT 0 CHECK (rows_inserted >= 0),
  rows_updated bigint NOT NULL DEFAULT 0 CHECK (rows_updated >= 0),
  rows_skipped bigint NOT NULL DEFAULT 0 CHECK (rows_skipped >= 0),
  temporal_semantics_status text NOT NULL
    CHECK (temporal_semantics_status = 'UNAVAILABLE_AT_L2'),
  state text NOT NULL CHECK (state IN ('completed', 'invalidated')),
  recorded_at timestamptz NOT NULL DEFAULT now(),
  invalidated_at timestamptz,
  invalidation_reason text,
  PRIMARY KEY (generation_id, asset_id, partition_key),
  CHECK ((state = 'invalidated') = (invalidated_at IS NOT NULL)),
  CHECK ((state = 'invalidated') = (invalidation_reason IS NOT NULL))
);

CREATE INDEX IF NOT EXISTS data_plane_l2_producer_generations_head_idx
  ON data_plane_l2_producer_generations
  (chart_id, calculation_context_id, asset_id, recorded_at DESC)
  WHERE state = 'completed';

CREATE OR REPLACE FUNCTION guard_data_plane_l2_completed_generation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF OLD.state = 'completed' AND NEW.state = 'completed' AND
     ROW(NEW.generation_id, NEW.asset_id, NEW.partition_key, NEW.chart_id, NEW.build_id,
         NEW.contract_version, NEW.accepted_l0_release, NEW.accepted_l1_terminal,
         NEW.calculation_context_id, NEW.producer_role, NEW.source_digest,
         NEW.rows_inserted, NEW.rows_updated, NEW.rows_skipped,
         NEW.temporal_semantics_status)
     IS DISTINCT FROM
     ROW(OLD.generation_id, OLD.asset_id, OLD.partition_key, OLD.chart_id, OLD.build_id,
         OLD.contract_version, OLD.accepted_l0_release, OLD.accepted_l1_terminal,
         OLD.calculation_context_id, OLD.producer_role, OLD.source_digest,
         OLD.rows_inserted, OLD.rows_updated, OLD.rows_skipped,
         OLD.temporal_semantics_status) THEN
    RAISE EXCEPTION 'completed L2 producer generation is immutable';
  END IF;
  RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS trg_guard_data_plane_l2_completed_generation
  ON data_plane_l2_producer_generations;
CREATE TRIGGER trg_guard_data_plane_l2_completed_generation
BEFORE UPDATE ON data_plane_l2_producer_generations
FOR EACH ROW EXECUTE FUNCTION guard_data_plane_l2_completed_generation();

COMMENT ON TABLE data_plane_l2_producer_generations IS
  'DP-SD-015 append-only observation receipts; structural outputs remain writer-owned; no L3 activation authority.';
