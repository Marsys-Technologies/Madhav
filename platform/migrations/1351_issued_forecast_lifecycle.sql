-- Migration 1351: L5 issued-forecast lifecycle (K6-5a / D-R11 / KYD-5).
-- Created: 2026-10-10. NEEDS-PROTECTED-WINDOW: creates public objects.
-- migrate.ts owns the transaction. No legacy table, row, or grant is changed.

CREATE OR REPLACE FUNCTION public.issued_forecast_intervals_valid(value tstzmultirange)
RETURNS boolean LANGUAGE sql IMMUTABLE STRICT AS $$
  SELECT NOT isempty(value) AND bool_and(
    NOT lower_inf(part) AND NOT upper_inf(part) AND lower_inc(part) AND NOT upper_inc(part)
  ) FROM unnest(value) AS part
$$;

CREATE TABLE IF NOT EXISTS public.issued_forecast (
  issue_id uuid NOT NULL,
  version integer NOT NULL CHECK (version > 0),
  chart_id uuid NOT NULL,
  generation text NOT NULL,
  event_class text NOT NULL CHECK (btrim(event_class) <> ''),
  phase text NOT NULL CHECK (btrim(phase) <> ''),
  affected_person text NOT NULL CHECK (btrim(affected_person) <> ''),
  episode text NOT NULL CHECK (btrim(episode) <> ''),
  issued_at timestamptz NOT NULL,
  information_cutoff timestamptz NOT NULL CHECK (information_cutoff <= issued_at),
  delivered_at timestamptz NOT NULL CHECK (delivered_at <= issued_at),
  delivery_channel text NOT NULL CHECK (btrim(delivery_channel) <> ''),
  delivered_statement text NOT NULL CHECK (btrim(delivered_statement) <> ''),
  result_policy text NOT NULL CHECK (btrim(result_policy) <> ''),
  calibration_status text NOT NULL
    CHECK (calibration_status IN ('calibrated', 'uncalibrated', 'unqualified')),
  intervals tstzmultirange NOT NULL CHECK (public.issued_forecast_intervals_valid(intervals)),
  disclosed_grain text NOT NULL CHECK (btrim(disclosed_grain) <> ''),
  point_functional text NOT NULL CHECK (btrim(point_functional) <> ''),
  probability_target numeric CHECK (
    probability_target IS NULL OR
    (calibration_status = 'calibrated' AND result_policy <> 'all_null'
      AND probability_target >= 0 AND probability_target <= 1)
  ),
  falsifier jsonb NOT NULL CHECK (
    jsonb_typeof(falsifier) = 'object'
    AND falsifier ? 'ontology_locator' AND falsifier ? 'observation_predicate'
    AND jsonb_typeof(falsifier->'ontology_locator') = 'string'
    AND jsonb_typeof(falsifier->'observation_predicate') = 'string'
    AND btrim(falsifier->>'ontology_locator') <> ''
    AND btrim(falsifier->>'observation_predicate') <> ''
  ),
  PRIMARY KEY (issue_id, version),
  FOREIGN KEY (chart_id, generation)
    REFERENCES public.kala_layer_candidate (chart_id, generation) ON DELETE RESTRICT ON UPDATE RESTRICT
);

CREATE TABLE IF NOT EXISTS public.issued_forecast_outcome (
  outcome_id uuid PRIMARY KEY,
  issue_id uuid NOT NULL,
  version integer NOT NULL,
  observed_at timestamptz NOT NULL,
  recorded_at timestamptz NOT NULL,
  observation jsonb NOT NULL CHECK (jsonb_typeof(observation) = 'object' AND observation <> '{}'::jsonb),
  FOREIGN KEY (issue_id, version)
    REFERENCES public.issued_forecast (issue_id, version) ON DELETE RESTRICT ON UPDATE RESTRICT
);

-- Even an unreferenced issue is delivered history. Immutable retries use
-- INSERT ... ON CONFLICT DO NOTHING; refinements append a new version.
CREATE OR REPLACE FUNCTION public.issued_forecast_refuse_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'Delivered forecasts and their outcomes are append-only: % on % refused', TG_OP, TG_TABLE_NAME
    USING ERRCODE = '55000';
END;
$$;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgrelid = 'public.issued_forecast'::regclass
                 AND tgname = 'issued_forecast_immutable_rows') THEN
    CREATE TRIGGER issued_forecast_immutable_rows BEFORE UPDATE OR DELETE ON public.issued_forecast
      FOR EACH ROW EXECUTE FUNCTION public.issued_forecast_refuse_mutation();
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgrelid = 'public.issued_forecast'::regclass
                 AND tgname = 'issued_forecast_immutable_truncate') THEN
    CREATE TRIGGER issued_forecast_immutable_truncate BEFORE TRUNCATE ON public.issued_forecast
      FOR EACH STATEMENT EXECUTE FUNCTION public.issued_forecast_refuse_mutation();
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgrelid = 'public.issued_forecast_outcome'::regclass
                 AND tgname = 'issued_forecast_outcome_immutable_rows') THEN
    CREATE TRIGGER issued_forecast_outcome_immutable_rows BEFORE UPDATE OR DELETE ON public.issued_forecast_outcome
      FOR EACH ROW EXECUTE FUNCTION public.issued_forecast_refuse_mutation();
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgrelid = 'public.issued_forecast_outcome'::regclass
                 AND tgname = 'issued_forecast_outcome_immutable_truncate') THEN
    CREATE TRIGGER issued_forecast_outcome_immutable_truncate BEFORE TRUNCATE ON public.issued_forecast_outcome
      FOR EACH STATEMENT EXECUTE FUNCTION public.issued_forecast_refuse_mutation();
  END IF;
END;
$$;

COMMENT ON TABLE public.issued_forecast IS
  'L5 lifecycle, D-R11: delivered immutable issue/version; L3 registrar supplies manifest reference. Episode identity clusters outcome credit.';
COMMENT ON TABLE public.issued_forecast_outcome IS
  'L5 append-only observations, referencing exact issue/version with RESTRICT; legacy L4 phala_anchors protection remains active.';
