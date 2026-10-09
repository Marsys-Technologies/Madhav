-- Migration 1343: K3-1 / KYD-134: additive, version-scoped candidate axes. ROUTINE-OK; no index.
-- Legacy, K0a rehearsal and other candidate versions retain their prior contract.
SET LOCAL lock_timeout = '5s';
ALTER TABLE public.kala_obstruction
  ADD COLUMN IF NOT EXISTS negative_space_contract_version text,
  ADD COLUMN IF NOT EXISTS event_class_id text,
  ADD COLUMN IF NOT EXISTS roots jsonb,
  ADD COLUMN IF NOT EXISTS null_reason text,
  ADD COLUMN IF NOT EXISTS release_reason text;
DO $constraints$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.kala_obstruction'::regclass
                 AND conname='kala_obstruction_k3_axes_check') THEN
    ALTER TABLE public.kala_obstruction ADD CONSTRAINT kala_obstruction_k3_axes_check CHECK (
      negative_space_contract_version IS DISTINCT FROM 'k3-negative-space/1.0.0' OR (
        generation IS NOT NULL AND generation LIKE 'candidate:%' AND length(generation)>10
        AND assertion_id IS NOT NULL AND length(assertion_id)>0
        AND event_class_id IS NOT NULL AND length(event_class_id)>0
        AND assertion IS NOT NULL AND jsonb_typeof(assertion)='object'
        AND roots IS NOT NULL AND jsonb_typeof(roots)='object'
        AND exposure IS NOT NULL AND exposure IN ('in_risk_set','outside_risk_set','method_inapplicable')
        AND knowledge IS NOT NULL AND knowledge IN ('searched','unsearched','inputs_missing','computation_failed','complete')
        AND rule_conclusion IS NOT NULL AND rule_conclusion IN ('none','supportive','adverse','obstructed','conditionally_deferred','denied')
        AND defeat_state IS NOT NULL AND defeat_state IN ('active','excepted','cancelled','partly_cancelled','contested','unresolved')
        AND measurement IS NOT NULL AND measurement='not_estimated_here'
        AND effective_state IS NOT NULL AND effective_state IN ('outside_risk_set','method_inapplicable','information_unavailable','evaluated_silent','obstruction_in_force','obstruction_cancelled','obstruction_partly_cancelled','obstruction_contested')
        AND interval_start IS NOT NULL AND interval_end IS NOT NULL AND interval_start<interval_end
        AND severity_score=0 AND override_score=0
        AND release IS NOT NULL AND jsonb_typeof(release)='object'
        AND release->>'kind' IS NOT NULL AND release->>'kind' IN ('instant','conditional','unknown')
        AND ((release->>'kind'='instant' AND release->>'instant' IS NOT NULL
              AND release->>'instant' ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}([.][0-9]+)?(Z|[+-][0-9]{2}:[0-9]{2})$'
              AND (release->>'instant')::timestamptz >= interval_start
              AND release->>'predicate_ref' IS NULL)
          OR (release->>'kind'='conditional' AND release->>'predicate_ref' IS NOT NULL AND length(btrim(release->>'predicate_ref'))>0 AND release->>'instant' IS NULL)
          OR (release->>'kind'='unknown' AND release->>'instant' IS NULL AND release->>'predicate_ref' IS NULL))
        AND (release->>'kind'<>'unknown' OR release_reason IS NOT DISTINCT FROM 'release_unknown')
        AND (release->>'kind'<>'conditional' OR release_reason IS NOT DISTINCT FROM 'release_conditional')
        AND (effective_state<>'obstruction_in_force' OR (defeat_state='active' AND rule_conclusion IN ('adverse','obstructed','conditionally_deferred','denied')))
        AND (effective_state<>'obstruction_cancelled' OR defeat_state IN ('cancelled','excepted'))
        AND (effective_state<>'obstruction_partly_cancelled' OR defeat_state='partly_cancelled')
        AND (effective_state<>'obstruction_contested' OR defeat_state='contested')
        AND (effective_state NOT IN ('evaluated_silent','obstruction_in_force','obstruction_cancelled','obstruction_partly_cancelled','obstruction_contested')
             OR (knowledge IN ('searched','complete') AND defeat_state<>'unresolved'
                 AND null_reason IS NULL AND assertion->>'acceptance_scope' IS NOT DISTINCT FROM 'fixture_only'))
        AND (effective_state<>'information_unavailable' OR (null_reason IS NOT NULL AND length(null_reason)>0))
      )
    );
  END IF;
END $constraints$;
