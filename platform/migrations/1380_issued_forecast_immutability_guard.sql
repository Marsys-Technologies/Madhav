-- Migration 1380: restore the complete K6-5a append-only lifecycle contract.
-- NEEDS-PROTECTED-WINDOW: replaces triggers in public. migrate.ts owns the transaction.
-- 1351 is applied history and is deliberately unchanged. Its IF NOT EXISTS
-- checks cannot repair an installed, column-limited trigger with the same name.
-- Recreate all four guards without updating/deleting any issue or outcome.

LOCK TABLE public.issued_forecast, public.issued_forecast_outcome IN ACCESS EXCLUSIVE MODE;

DROP TRIGGER IF EXISTS issued_forecast_immutable_rows ON public.issued_forecast;
CREATE TRIGGER issued_forecast_immutable_rows
  BEFORE UPDATE OR DELETE ON public.issued_forecast
  FOR EACH ROW EXECUTE FUNCTION public.issued_forecast_refuse_mutation();

DROP TRIGGER IF EXISTS issued_forecast_immutable_truncate ON public.issued_forecast;
CREATE TRIGGER issued_forecast_immutable_truncate
  BEFORE TRUNCATE ON public.issued_forecast
  FOR EACH STATEMENT EXECUTE FUNCTION public.issued_forecast_refuse_mutation();

DROP TRIGGER IF EXISTS issued_forecast_outcome_immutable_rows ON public.issued_forecast_outcome;
CREATE TRIGGER issued_forecast_outcome_immutable_rows
  BEFORE UPDATE OR DELETE ON public.issued_forecast_outcome
  FOR EACH ROW EXECUTE FUNCTION public.issued_forecast_refuse_mutation();

DROP TRIGGER IF EXISTS issued_forecast_outcome_immutable_truncate ON public.issued_forecast_outcome;
CREATE TRIGGER issued_forecast_outcome_immutable_truncate
  BEFORE TRUNCATE ON public.issued_forecast_outcome
  FOR EACH STATEMENT EXECUTE FUNCTION public.issued_forecast_refuse_mutation();
