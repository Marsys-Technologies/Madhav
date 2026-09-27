-- Migration 1122: Jātaka chart-context staleness (JATAKA-REQ-03).
--
-- Number: 1122 is the next cross-cutting number above the Pūrṇa (1042–1069) and
-- L3 Kāla (1070–1119) partitions, reserved on origin/campaign-coordination by
-- JATAKA-REQ-03 (native-authorized 2026-09-27, Phase-A2 integrity) after a fresh
-- origin/main (6b26f3ff0, max 1079) and complete open-PR sweep (22 migration
-- files, max 1090); 1120 and 1121 are the only prior 1120+ reservations. Authored
-- under CCD-015 / the Phase-A2 integrity addendum; NOT applied in that phase.
--
-- Purpose: a birth-details correction (recomputeChart.ts) preserves two kinds of
-- rows that no rebuild will ever regenerate on its own schedule and that would
-- otherwise silently keep reading as current chart truth:
--
--   event_chart_state_index  the dasha/transit context computed for each seeded
--                            life-event row. Its only writer is a manual CLI
--                            (`lel_intake.py seed`), never the automated build
--                            DAG — a correction cannot rebuild it, only mark it.
--   mimamsa_predictions      rows whose lifecycle_status has moved past
--                            'pending'/'due' (real, native-verified outcomes —
--                            see mi_bhavisya.py's own DELETE-scope guard) survive
--                            a correction's rebuild untouched.
--
-- This migration adds the metadata the correction transaction (and every
-- current-query consumer) needs to tell "current chart truth" from "historical
-- evidence computed under a birth-detail set that no longer applies":
--
--   chart_context_stale_at               NULL while the row reflects the
--                                         chart's current birth details; set the
--                                         instant a correction supersedes them.
--   chart_context_stale_reason           'chart_details_changed' for now — the
--                                         only reason a correction ever needs.
--   chart_context_superseded_by_run_id   the correction's rebuild run. ON DELETE
--                                         SET NULL: pruning a run never erases
--                                         which rows it made historical.
--
-- The row itself is never deleted, edited or reclassified by this migration or
-- by the marking transaction — B.10/B.3 discipline: the fact is preserved
-- exactly as computed; only an orthogonal, additive marker says it is no longer
-- current. `lifecycle_status`/`outcome`/`confirmed`/`denied` on
-- mimamsa_predictions are never touched, and life_events is never touched at all
-- (it carries no derived chart-context data of its own).
--
-- Additive and idempotent: IF NOT EXISTS columns/index, pg_constraint-guarded
-- constraints. No existing row is rewritten; every existing row's
-- chart_context_stale_at is NULL and satisfies the CHECKs.
--
-- Known follow-up (recorded here, not fixed by this migration): applying this
-- migration changes `mimamsa_predictions`' DDL shape, which
-- `platform/scripts/governance/MIMAMSA_PREDICTIONS_SCHEMA_PIN.json` hash-pins.
-- That baseline must be regenerated (`schema_pin_mimamsa_predictions.py
-- --print-canonical` against the live DB) once this migration is actually
-- applied — a live-DB step outside this session's authority (no database
-- access), so the baseline JSON is not touched here.

ALTER TABLE public.event_chart_state_index
  ADD COLUMN IF NOT EXISTS chart_context_stale_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS chart_context_stale_reason TEXT,
  ADD COLUMN IF NOT EXISTS chart_context_superseded_by_run_id UUID;

ALTER TABLE public.mimamsa_predictions
  ADD COLUMN IF NOT EXISTS chart_context_stale_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS chart_context_stale_reason TEXT,
  ADD COLUMN IF NOT EXISTS chart_context_superseded_by_run_id UUID;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'event_chart_state_index_stale_reason_check'
  ) THEN
    ALTER TABLE public.event_chart_state_index
      ADD CONSTRAINT event_chart_state_index_stale_reason_check
      CHECK (chart_context_stale_reason IS NULL OR chart_context_stale_reason IN ('chart_details_changed'));
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'event_chart_state_index_stale_pair_check'
  ) THEN
    ALTER TABLE public.event_chart_state_index
      ADD CONSTRAINT event_chart_state_index_stale_pair_check
      CHECK ((chart_context_stale_at IS NULL) = (chart_context_stale_reason IS NULL));
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'event_chart_state_index_superseded_by_run_id_fkey'
  ) THEN
    ALTER TABLE public.event_chart_state_index
      ADD CONSTRAINT event_chart_state_index_superseded_by_run_id_fkey
      FOREIGN KEY (chart_context_superseded_by_run_id)
      REFERENCES public.build_runs(id) ON DELETE SET NULL;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'mimamsa_predictions_stale_reason_check'
  ) THEN
    ALTER TABLE public.mimamsa_predictions
      ADD CONSTRAINT mimamsa_predictions_stale_reason_check
      CHECK (chart_context_stale_reason IS NULL OR chart_context_stale_reason IN ('chart_details_changed'));
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'mimamsa_predictions_stale_pair_check'
  ) THEN
    ALTER TABLE public.mimamsa_predictions
      ADD CONSTRAINT mimamsa_predictions_stale_pair_check
      CHECK ((chart_context_stale_at IS NULL) = (chart_context_stale_reason IS NULL));
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'mimamsa_predictions_superseded_by_run_id_fkey'
  ) THEN
    ALTER TABLE public.mimamsa_predictions
      ADD CONSTRAINT mimamsa_predictions_superseded_by_run_id_fkey
      FOREIGN KEY (chart_context_superseded_by_run_id)
      REFERENCES public.build_runs(id) ON DELETE SET NULL;
  END IF;
END $$;

-- Lock note (same as migrations 359/414/415): the migrate.ts runner wraps
-- each file in BEGIN/COMMIT, incompatible with CREATE INDEX CONCURRENTLY, so
-- these are plain index builds under an ACCESS EXCLUSIVE lock for the
-- migration's duration. mimamsa_predictions is pinned at ~286 rows
-- (MIMAMSA_PREDICTIONS_SCHEMA_PIN.json); event_chart_state_index has no
-- automated writer (a manual per-event CLI seed only), so both tables are
-- small and the lock window is brief.
--
-- Partial indexes: every current-query consumer filters
-- `chart_context_stale_at IS NULL` (or, in a LEFT JOIN, adds it to the ON
-- clause) — this is the index that filter actually uses.
CREATE INDEX IF NOT EXISTS idx_event_chart_state_index_chart_current
  ON public.event_chart_state_index(chart_id)
  WHERE chart_context_stale_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_mimamsa_predictions_chart_current
  ON public.mimamsa_predictions(chart_id)
  WHERE chart_context_stale_at IS NULL;

COMMENT ON COLUMN public.event_chart_state_index.chart_context_stale_at IS
  'NULL = reflects the chart''s current birth details. Set once a correction supersedes them; the row itself is preserved unchanged as historical evidence.';
COMMENT ON COLUMN public.event_chart_state_index.chart_context_stale_reason IS
  'NULL = current. chart_details_changed = superseded by a chart-details correction.';
COMMENT ON COLUMN public.event_chart_state_index.chart_context_superseded_by_run_id IS
  'The correction''s rebuild run; SET NULL if the run row is pruned.';
COMMENT ON COLUMN public.mimamsa_predictions.chart_context_stale_at IS
  'NULL = reflects the chart''s current birth details. Set once a correction supersedes them; lifecycle_status/outcome are never touched by this marker.';
COMMENT ON COLUMN public.mimamsa_predictions.chart_context_stale_reason IS
  'NULL = current. chart_details_changed = superseded by a chart-details correction.';
COMMENT ON COLUMN public.mimamsa_predictions.chart_context_superseded_by_run_id IS
  'The correction''s rebuild run; SET NULL if the run row is pruned.';
