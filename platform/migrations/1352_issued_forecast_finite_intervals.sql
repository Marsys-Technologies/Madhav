-- Migration 1352: finite interval validation for new issued forecasts (K6-5a).
-- Created: 2026-10-10. NEEDS-PROTECTED-WINDOW: public function replacement.
-- 1351 was already applied in lane rehearsal: preserve its exact bytes.
-- No issued row is rewritten. The stricter predicate governs new inserts.
CREATE OR REPLACE FUNCTION public.issued_forecast_intervals_valid(value tstzmultirange)
RETURNS boolean LANGUAGE sql IMMUTABLE STRICT AS $$
  SELECT NOT isempty(value) AND bool_and(
    NOT lower_inf(part) AND NOT upper_inf(part) AND isfinite(lower(part)) AND isfinite(upper(part))
    AND lower_inc(part) AND NOT upper_inc(part)
  ) FROM unnest(value) AS part
$$;
