-- Migration 1335: K2-1b additive candidate-generation carriage for the F1 promise graph.
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
