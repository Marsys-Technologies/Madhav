-- Migration 1337: K2-1b additive candidate-generation carriage for the F1 promise graph.
-- Created: 2026-10-08
--
-- Legacy/published predicate rows remain readable during the K9 contract phase.
-- New candidate writers pin a generation and describe the mechanism route and
-- candidate/effective conclusion state in JSON; no existing column is retired.

SET LOCAL lock_timeout = '5s';

ALTER TABLE public.kala_activation_predicates
    ADD COLUMN IF NOT EXISTS generation text NOT NULL DEFAULT 'legacy',
    ADD COLUMN IF NOT EXISTS mechanism_route text NOT NULL DEFAULT 'testimony'
        CHECK (mechanism_route IN ('admitted', 'testimony')),
    ADD COLUMN IF NOT EXISTS conclusion_state_jsonb jsonb NOT NULL DEFAULT '{}'::jsonb;

CREATE INDEX IF NOT EXISTS idx_kap_candidate_generation
    ON public.kala_activation_predicates (chart_id, generation, signature_class);

-- The legacy identity prevents a candidate row from coexisting with its
-- published counterpart.  Expand it before candidate partitions are written.
DROP INDEX IF EXISTS public.idx_kap_chart_signal_ayan;
CREATE UNIQUE INDEX IF NOT EXISTS idx_kap_chart_signal_ayan_generation
    ON public.kala_activation_predicates (chart_id, signal_id, ayanamsha_id, generation);

-- L1 mechanisms exist independently of the optional L2 signal attachment.
ALTER TABLE public.kala_activation_predicates
    ALTER COLUMN signal_id DROP NOT NULL,
    ADD COLUMN IF NOT EXISTS mechanism_id text,
    ADD COLUMN IF NOT EXISTS event_class_id text;

CREATE UNIQUE INDEX IF NOT EXISTS idx_kap_mechanism_generation_class
    ON public.kala_activation_predicates
       (chart_id, ayanamsha_id, generation, mechanism_id, COALESCE(event_class_id, ''))
    WHERE mechanism_id IS NOT NULL;

-- Version the registered detector at the same boundary as its payload. Keep
-- every old conjunct intact over retained legacy rows; candidate graphs are
-- checked against their L1 identities, sources and effective state instead of
-- requiring an L2-selected signal or inventing a numeric strength template.
DO $k2$
DECLARE
    old_check text;
    graph_check text := $graph$
    AND NOT EXISTS (
      SELECT 1 FROM kala_activation_predicates p
      WHERE p.generation <> 'legacy' AND (
        p.mechanism_id IS NULL
        OR p.derivation_ledger_jsonb->>'mechanism_id' IS DISTINCT FROM p.mechanism_id
        OR p.derivation_ledger_jsonb->>'route' IS DISTINCT FROM p.mechanism_route
        OR p.derivation_ledger_jsonb->>'event_class_id' IS DISTINCT FROM p.event_class_id
        OR NULLIF(p.derivation_ledger_jsonb->>'source', '') IS NULL
        OR (p.conclusion_state_jsonb->>'qualification' = 'sourced'
            AND NULLIF(p.derivation_ledger_jsonb->>'rule_version', '') IS NULL)
        OR COALESCE(p.conclusion_state_jsonb->>'scored', '') NOT IN ('true','false')
        OR COALESCE(p.conclusion_state_jsonb->>'fact_state', '') NOT IN
           ('present','missing_fact','evaluated_empty')
        OR COALESCE(p.conclusion_state_jsonb->>'effective_state', '') NOT IN
           ('in_force','defeated','partly_defeated','contested','unresolved')
        OR (p.conclusion_state_jsonb->>'scored' = 'true' AND (
          p.mechanism_route <> 'admitted' OR p.event_class_id IS NULL
          OR COALESCE(p.conclusion_state_jsonb->>'effective_state', '') <> 'in_force'
          OR COALESCE(p.conclusion_state_jsonb->>'qualification', '') <> 'sourced'
          OR COALESCE(p.conclusion_state_jsonb->>'fact_state', '') <> 'present'))
        OR (p.conclusion_state_jsonb->>'fact_state' = 'present'
            AND COALESCE(jsonb_array_length(p.derivation_ledger_jsonb->'fact_ids'), 0) = 0)
        OR (p.conclusion_state_jsonb->>'fact_state' = 'present' AND EXISTS (
          SELECT 1 FROM jsonb_array_elements_text(p.derivation_ledger_jsonb->'fact_ids') fid
          WHERE NOT EXISTS (SELECT 1 FROM chart_facts f WHERE f.fact_id = fid
            AND f.chart_id = p.chart_id AND f.ayanamsha_id = p.ayanamsha_id)))
        OR (p.mechanism_route = 'admitted' AND NOT EXISTS (
          SELECT 1 FROM ga_yoga_firings f WHERE f.chart_id = p.chart_id
            AND f.ayanamsha_id = p.ayanamsha_id AND f.fired
            AND f.yoga_canonical_id = p.derivation_ledger_jsonb->>'canonical_id'))
      )
    ) AS integrity_passed
    $graph$;
BEGIN
    SELECT integrity_check_sql INTO old_check FROM asset_registry WHERE asset_id = 'ka_yojaka';
    IF old_check IS NULL OR position('AS integrity_passed' IN old_check) = 0 THEN
        RAISE EXCEPTION 'K2-1b requires the existing registered Yojaka integrity contract';
    END IF;
    IF old_check NOT LIKE 'WITH k2_legacy_predicates AS%' THEN
        UPDATE asset_registry SET integrity_check_sql =
          'WITH k2_legacy_predicates AS (SELECT * FROM kala_activation_predicates WHERE generation = ''legacy'') '
          || replace(replace(old_check, 'kala_activation_predicates', 'k2_legacy_predicates'),
                     'AS integrity_passed', graph_check)
        WHERE asset_id = 'ka_yojaka';
    END IF;
    UPDATE asset_registry SET has_substeps = true,
      depends_on = (SELECT ARRAY(SELECT DISTINCT d FROM unnest(depends_on ||
                    ARRAY['ga_positions','bg_yogas']::text[]) d ORDER BY d))
    WHERE asset_id = 'ka_yojaka';
END $k2$;
