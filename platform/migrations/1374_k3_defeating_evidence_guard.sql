-- Migration 1374: K3 review, retained rule-targeted defeating evidence.
-- Additive and version-scoped; no legacy or published row is rewritten.
-- CHECK only: no public-schema CREATE privilege or new index is needed.
SET LOCAL lock_timeout = '5s';
DO $constraints$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint
                 WHERE conrelid='public.kala_obstruction'::regclass
                   AND conname='kala_obstruction_k3_defeating_evidence_check') THEN
    ALTER TABLE public.kala_obstruction
      ADD CONSTRAINT kala_obstruction_k3_defeating_evidence_check CHECK (
        negative_space_contract_version IS DISTINCT FROM 'k3-negative-space/1.0.0'
        OR effective_state NOT IN ('obstruction_cancelled','obstruction_partly_cancelled')
        OR (
          jsonb_typeof(assertion->'protections')='array'
          AND jsonb_typeof(roots->'fact_ids')='array'
          AND roots->'fact_ids' @> jsonb_path_query_array(assertion, '$.protections[*].fact_ids[*]')
          AND jsonb_path_exists_tz(assertion, $path$
            $.protections[*] ? (
              @.target_assertion_id == $target
              && (@.kind == "defeats" || @.kind == "excepts"
                  || ($partial == true && @.kind == "partly_defeats"))
              && @.fact_ids.type() == "array" && @.fact_ids.size() > 0
              && !exists(@.fact_ids[*] ? (@.type() != "string" || !(@ like_regex "\\S")))
              && @.source.text like_regex "\\S"
              && @.source.locator like_regex "\\S"
              && @.interval.t0.datetime() < @.interval.t1.datetime()
              && @.interval.t0.datetime() < $ends.datetime()
              && @.interval.t1.datetime() > $starts.datetime()
            )
          $path$::jsonpath, jsonb_build_object(
            'target', assertion_id, 'partial', effective_state='obstruction_partly_cancelled',
            'starts', interval_start, 'ends', interval_end))
        ) IS TRUE
      ) NOT VALID;
    -- Enforce every new/updated row without certifying or rewriting old
    -- fixture candidates. Historical validation needs a separate readback.
  END IF;
END $constraints$;
