-- Migration 1336: K0a-4 additive candidate envelope and negative-space axes.
-- ROUTINE-OK: ADD COLUMN only, no indexes, schema grants or key replacement.
-- NULL generation identifies unchanged legacy rows. No backfill is performed.
ALTER TABLE public.kala_obstruction
  ADD COLUMN IF NOT EXISTS generation text,
  ADD COLUMN IF NOT EXISTS assertion_id text,
  ADD COLUMN IF NOT EXISTS assertion jsonb,
  ADD COLUMN IF NOT EXISTS exposure text,
  ADD COLUMN IF NOT EXISTS knowledge text,
  ADD COLUMN IF NOT EXISTS rule_conclusion text,
  ADD COLUMN IF NOT EXISTS defeat_state text,
  ADD COLUMN IF NOT EXISTS effective_state text,
  ADD COLUMN IF NOT EXISTS measurement text,
  ADD COLUMN IF NOT EXISTS what text,
  ADD COLUMN IF NOT EXISTS by_what text,
  ADD COLUMN IF NOT EXISTS release jsonb,
  ADD COLUMN IF NOT EXISTS interval_start timestamptz,
  ADD COLUMN IF NOT EXISTS interval_end timestamptz;

ALTER TABLE public.kala_darshana
  ADD COLUMN IF NOT EXISTS generation text,
  ADD COLUMN IF NOT EXISTS assertion_id text,
  ADD COLUMN IF NOT EXISTS assertion jsonb,
  ADD COLUMN IF NOT EXISTS candidate_effective_state text,
  ADD COLUMN IF NOT EXISTS source_assertion_ids text[],
  ADD COLUMN IF NOT EXISTS interval_start timestamptz,
  ADD COLUMN IF NOT EXISTS interval_end timestamptz;
