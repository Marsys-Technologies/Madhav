-- Migration 553: LEL event_class resolution side table
-- SAMPURTI Campaign, Lane L0f, G14a (2026-08-10)
--
-- Adds per-row resolution state for life_events → brahma_event_ontology.event_class.
-- Persistence design: a side table keyed to life_events(chart_id, event_id) rather
-- than columns on life_events itself. Rationale:
--   (a) life_events is already wide (27 columns); the audit trail is a JSONB blob
--       that does not belong inline;
--   (b) the resolver may be re-run with a newer RESOLVER_VERSION — the side table
--       cleanly replaces the prior row via ON CONFLICT DO UPDATE, so old-version rows
--       are always superseded rather than accreting;
--   (c) keeps the leakage firewall intact: the resolver result is clearly a derived,
--       write-once classification layer, not a field on the primary event record.
--
-- Idempotency: ON CONFLICT DO UPDATE (global reference-style; the resolver backfill
-- always re-runs cleanly).
--
-- CRITICAL RAIL: this table feeds SCORING only. It is NEVER read by:
--   - ka_kshetra or any bodha-layer writer
--   - chart_facts (L1 sealed, R19)
-- The FK reference is to life_events, NOT to any interpretive layer table.

BEGIN;

CREATE TABLE IF NOT EXISTS lel_event_class_resolution (
    id                uuid NOT NULL DEFAULT gen_random_uuid(),
    chart_id          uuid NOT NULL,
    event_id          text NOT NULL,
    resolved_event_class  text,          -- NULL when confidence=AMBIGUOUS
    confidence        text NOT NULL,     -- EXACT | KEYWORD | AMBIGUOUS
    rule_matched      text NOT NULL,     -- which rule fired
    matched_tokens    text NOT NULL,     -- domain string or keyword that matched
    candidates        text[],            -- non-empty only when AMBIGUOUS
    resolver_version  text NOT NULL,     -- e.g. 'l0f_v1.0'
    audit_trail       jsonb NOT NULL,    -- full structured audit dict
    resolved_at       timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT lel_event_class_resolution_pkey PRIMARY KEY (id),
    CONSTRAINT lel_event_class_resolution_chart_event_uq
        UNIQUE (chart_id, event_id)
);

-- Index for efficient per-chart queries (the primary use pattern)
CREATE INDEX IF NOT EXISTS idx_lel_ecr_chart_id
    ON lel_event_class_resolution (chart_id);

-- Index to support "find all rows with a given event_class" queries (scoring)
CREATE INDEX IF NOT EXISTS idx_lel_ecr_resolved_event_class
    ON lel_event_class_resolution (resolved_event_class)
    WHERE resolved_event_class IS NOT NULL;

-- CHECK constraint: confidence must be one of the three defined values
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'lel_ecr_confidence_check'
  ) THEN
    ALTER TABLE lel_event_class_resolution
      ADD CONSTRAINT lel_ecr_confidence_check
      CHECK (confidence IN ('EXACT', 'KEYWORD', 'AMBIGUOUS'));
  END IF;
END $$;

-- CHECK constraint: resolved_event_class is NULL iff confidence=AMBIGUOUS
-- (an AMBIGUOUS row must carry NULL; a resolved row must carry a non-NULL class).
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'lel_ecr_class_null_iff_ambiguous'
  ) THEN
    ALTER TABLE lel_event_class_resolution
      ADD CONSTRAINT lel_ecr_class_null_iff_ambiguous
      CHECK (
        (confidence = 'AMBIGUOUS' AND resolved_event_class IS NULL)
        OR
        (confidence != 'AMBIGUOUS' AND resolved_event_class IS NOT NULL)
      );
  END IF;
END $$;

COMMIT;
