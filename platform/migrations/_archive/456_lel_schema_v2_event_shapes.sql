-- Migration 456: LEL schema v2 — additive event-shape columns (DR-13/DIS.026)
-- Created: 2026-07-19
--
-- Implements LEL_SCHEMA_V2_PROPOSAL.md (APPROVED, native 2026-07-18, D-3 closeout
-- directive). Additive only: 9 new nullable/defaulted columns on `life_events`, no
-- rewriting of existing rows, no DROP/ALTER TYPE on existing columns. Every existing
-- row keeps its current single `event_date` and is implicitly shape='point',
-- date_confidence='exact' via the column defaults below — no bulk reclassification.
--
-- Consumed by: platform/scripts/audit/t0_retrodiction/lib/checks.ts's shape-aware
-- matcher (scoreShapeAwareEvent / scorePointEvent / scoreIntervalEvent /
-- scoreChainEvent, CR-47 / D-4a Lane A-1) and lel.ts's LelEvent type.

BEGIN;

ALTER TABLE life_events ADD COLUMN IF NOT EXISTS shape text NOT NULL DEFAULT 'point';
ALTER TABLE life_events ADD COLUMN IF NOT EXISTS date_confidence text NOT NULL DEFAULT 'exact';
ALTER TABLE life_events ADD COLUMN IF NOT EXISTS interval_start date;
ALTER TABLE life_events ADD COLUMN IF NOT EXISTS interval_end date;
ALTER TABLE life_events ADD COLUMN IF NOT EXISTS chain_parent_event_id text;
ALTER TABLE life_events ADD COLUMN IF NOT EXISTS milestone_label text;
ALTER TABLE life_events ADD COLUMN IF NOT EXISTS date_tightened_at timestamptz;
ALTER TABLE life_events ADD COLUMN IF NOT EXISTS date_tightened_by_source text;
ALTER TABLE life_events ADD COLUMN IF NOT EXISTS superseded_by_chain_note text;

-- CHECK constraints added separately (not inline) so IF NOT EXISTS-style idempotency
-- can be expressed via DO blocks — Postgres has no `ADD CONSTRAINT IF NOT EXISTS`.
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'life_events_shape_check'
  ) THEN
    ALTER TABLE life_events
      ADD CONSTRAINT life_events_shape_check CHECK (shape IN ('point', 'interval', 'chain'));
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'life_events_date_confidence_check'
  ) THEN
    ALTER TABLE life_events
      ADD CONSTRAINT life_events_date_confidence_check
      CHECK (date_confidence IN ('exact', 'month_known', 'year_only'));
  END IF;
END $$;

COMMIT;
