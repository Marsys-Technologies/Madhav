-- Migration 028 — KARN-W2-R1 — Add 8 source fields to msr_signals
-- Predecessor: KARN-W1-R1-PHASE-ALPHA (Audit 2 finding §5.3)
-- Adds signal_type, temporal_activation, valence, entities_involved,
-- supporting_rules, rpt_deep_dive, v6_ids_consumed, prior_id.
-- All NULL-able for backward compatibility with existing 499 rows.

BEGIN;

ALTER TABLE msr_signals
  ADD COLUMN IF NOT EXISTS signal_type         text,
  ADD COLUMN IF NOT EXISTS temporal_activation text,
  ADD COLUMN IF NOT EXISTS valence             text,
  ADD COLUMN IF NOT EXISTS entities_involved   jsonb,
  ADD COLUMN IF NOT EXISTS supporting_rules    jsonb,
  ADD COLUMN IF NOT EXISTS rpt_deep_dive       text,
  ADD COLUMN IF NOT EXISTS v6_ids_consumed     jsonb,
  ADD COLUMN IF NOT EXISTS prior_id            text;

-- Indexes on HIGH-priority filter columns
CREATE INDEX IF NOT EXISTS msr_signals_signal_type_idx
  ON msr_signals(signal_type);
CREATE INDEX IF NOT EXISTS msr_signals_temporal_activation_idx
  ON msr_signals(temporal_activation);
CREATE INDEX IF NOT EXISTS msr_signals_valence_idx
  ON msr_signals(valence);

-- GIN index for jsonb @> queries on entities_involved
CREATE INDEX IF NOT EXISTS msr_signals_entities_involved_gin
  ON msr_signals USING GIN (entities_involved);

COMMIT;
