-- K3-2 pre-build, SR-A4-01. Additive v2 storage prerequisite; no activation,
-- row rewrite, fixture-contract relaxation, data deletion or publication.
-- Allocated after 1385 across origin/main and 178 open kalayantra/* heads.
-- NEEDS-PROTECTED-WINDOW (owner job requires public ALTER on the protected list).
SET LOCAL lock_timeout = '5s';
DO $k3$
BEGIN
 IF NOT EXISTS (SELECT 1 FROM pg_constraint
     WHERE conrelid='public.kala_obstruction'::regclass AND conname='kala_obstruction_k3_sealed_check') THEN
  ALTER TABLE public.kala_obstruction ADD CONSTRAINT kala_obstruction_k3_sealed_check CHECK (
   negative_space_contract_version IS DISTINCT FROM 'k3-negative-space/2.0.0' OR COALESCE((
    generation LIKE 'candidate:%' AND length(generation)>10
    AND assertion_id<>'' AND event_class_id<>''
    AND jsonb_typeof(assertion)='object'
    AND assertion->>'contract_version'=negative_space_contract_version
    AND assertion->>'acceptance_scope'='sealed_producers'
    AND assertion->>'chart_id'=chart_id::text AND assertion->>'generation'=generation
    AND assertion->>'assertion_id'=assertion_id AND assertion->>'event_class_id'=event_class_id
    AND assertion->>'exposure'=exposure AND assertion->>'knowledge'=knowledge
    AND assertion->>'rule_conclusion'=rule_conclusion AND assertion->>'defeat_state'=defeat_state
    AND assertion->>'effective_state'=effective_state AND assertion->>'measurement'=measurement
    AND assertion->>'null_reason' IS NOT DISTINCT FROM null_reason
    AND assertion->'roots'=roots AND assertion->'release'=release
    AND jsonb_typeof(roots->'record_ids')='array' AND jsonb_typeof(roots->'contact_ids')='array'
    AND jsonb_typeof(roots->'fact_ids')='array'
    AND jsonb_typeof(assertion->'provenance'->'pins')='object'
    AND assertion->'provenance'->'pins'->>'chart_id'=chart_id::text
    AND assertion->'provenance'->'pins'->>'judge_generation'='5.0'
    AND length(assertion->'provenance'->'pins'->>'manifest_id')>0
    AND length(assertion->'provenance'->'pins'->>'verifier_execution_id')>0
    AND exposure IN ('in_risk_set','outside_risk_set','method_inapplicable')
    AND knowledge IN ('searched','unsearched','inputs_missing','computation_failed','complete')
    AND rule_conclusion IN ('none','supportive','adverse','obstructed','conditionally_deferred','denied')
    AND defeat_state IN ('active','excepted','cancelled','partly_cancelled','contested','unresolved')
    AND measurement='not_estimated_here' AND severity_score=0 AND override_score=0
    AND interval_start<interval_end AND isfinite(interval_start) AND isfinite(interval_end)
    AND (assertion->'interval'->>'t0')::timestamptz=interval_start
    AND (assertion->'interval'->>'t1')::timestamptz=interval_end
    AND effective_state IN ('outside_risk_set','method_inapplicable','information_unavailable','evaluated_silent',
        'obstruction_in_force','obstruction_cancelled','obstruction_partly_cancelled','obstruction_contested')
    AND ((effective_state='information_unavailable' AND length(btrim(null_reason))>0)
      OR (effective_state<>'information_unavailable' AND null_reason IS NULL))
    AND (effective_state NOT IN ('evaluated_silent','obstruction_in_force','obstruction_cancelled',
        'obstruction_partly_cancelled','obstruction_contested') OR
       (knowledge IN ('complete','searched') AND exposure='in_risk_set' AND defeat_state<>'unresolved'
        AND rule_conclusion<>'conditionally_deferred'))
    AND (effective_state<>'outside_risk_set' OR exposure='outside_risk_set')
    AND (effective_state<>'method_inapplicable' OR exposure='method_inapplicable')
    AND (effective_state<>'evaluated_silent' OR rule_conclusion IN ('none','supportive'))
    AND (effective_state<>'obstruction_in_force' OR (defeat_state='active' AND rule_conclusion IN ('adverse','obstructed','denied')))
    AND (effective_state<>'obstruction_cancelled' OR defeat_state IN ('cancelled','excepted'))
    AND (effective_state<>'obstruction_partly_cancelled' OR defeat_state='partly_cancelled')
    AND (effective_state<>'obstruction_contested' OR defeat_state='contested')
    AND (effective_state NOT IN ('obstruction_cancelled','obstruction_partly_cancelled','obstruction_contested') OR (
      jsonb_path_exists(assertion,
       '$.protections[*] ? (@.target_assertion_id == $target && @.fact_ids.type() == "array" && @.fact_ids.size() > 0 && @.source.text like_regex "\\S" && @.source.locator like_regex "\\S" && @.interval.t0.datetime() < @.interval.t1.datetime() && @.interval.t0.datetime() < $ends.datetime() && @.interval.t1.datetime() > $starts.datetime() && (($contest == true && @.kind == "contests") || ($contest == false && (@.kind == "defeats" || @.kind == "excepts" || ($partial == true && @.kind == "partly_defeats")))))'::jsonpath,
       jsonb_build_object('target',assertion->>'source_assertion_id',
        'partial',effective_state='obstruction_partly_cancelled','contest',effective_state='obstruction_contested',
        'starts',interval_start,'ends',interval_end)) IS TRUE
      AND roots->'fact_ids' @> jsonb_path_query_array(assertion,'$.protections[*].fact_ids[*]')
    ))
    AND ((release->>'kind'='instant' AND release_reason IS NULL
        AND release->>'instant' ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}([.][0-9]+)?(Z|[+-][0-9]{2}:[0-9]{2})$'
        AND (release->>'instant')::timestamptz>=interval_start AND release->>'predicate_ref' IS NULL)
      OR (release->>'kind'='unknown' AND release_reason='release_unknown'
        AND release->>'instant' IS NULL AND release->>'predicate_ref' IS NULL)
      OR (release->>'kind'='conditional' AND release_reason='release_conditional'
        AND release->>'instant' IS NULL AND length(btrim(release->>'predicate_ref'))>0))
   ),false)
  );
 END IF;
END $k3$;

-- Private v2 physical assertions have one immutable natural identity per candidate.
-- No legacy/fixture row participates in this index.
CREATE UNIQUE INDEX IF NOT EXISTS kala_obstruction_k3_sealed_identity
 ON public.kala_obstruction(chart_id,generation,assertion_id)
 WHERE negative_space_contract_version='k3-negative-space/2.0.0';
