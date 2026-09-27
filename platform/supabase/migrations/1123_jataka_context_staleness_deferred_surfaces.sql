-- Migration 1123: Jātaka chart-context staleness for the three deferred
-- surfaces (JATAKA-REQ-04).
--
-- Number: 1123 is the next cross-cutting number above the Pūrṇa (1042–1069) and
-- L3 Kāla (1070–1119) partitions, reserved on origin/campaign-coordination by
-- JATAKA-REQ-04 (native-authorized 2026-09-27, Phase-A3 source integrity) after
-- a fresh origin/main (6b26f3ff0, max 1079) and complete open-PR sweep (21 open
-- PRs, max 1090); 1120, 1121 and 1122 are the only prior 1120+ reservations.
-- Authored under CCD-016 / the Phase-A3 source-integrity addendum; NOT applied
-- in that phase.
--
-- Purpose: migration 1122 marked event_chart_state_index/mimamsa_predictions
-- chart-context-stale. Three further surfaces are preserved (never deleted) by
-- a birth-details correction and read by current-chart consumers, and need the
-- identical orthogonal marker:
--
--   brahma_mimamsa_prediction_ledger  Samīkṣā's own human-review ledger
--                                     (470_pariprashna_samiksha_prediction_
--                                     ledger.sql). A `detected`/`confirmed`/...
--                                     row records that the model, at reading
--                                     time, under the chart's THEN-current
--                                     birth details, surfaced or a human
--                                     confirmed a claim. A correction does not
--                                     erase that historical fact, but the claim
--                                     must stop seeding current-chart review
--                                     counts, current calibration or a new
--                                     reading once the birth details it was
--                                     computed under no longer apply.
--   brahma_prospective_ledger         The standing-predictions ledger
--                                     (458_brahma_prospective_ledger.sql), read
--                                     by L4 phala's `query_prospective_ledger`
--                                     (MCP `standing_predictions_read`), the
--                                     lifecycle sweep, and mi_bhara's own
--                                     current-calibration read.
--   mimamsa_calibration_snapshot      Two-key versioned calibration snapshots
--                                     (400_mimamsa_p6_schema.sql), one row per
--                                     chart (`chart_id UUID NOT NULL`, no
--                                     cross-chart aggregation — confirmed by
--                                     reading the live schema before authoring
--                                     this migration), read by the co-sign
--                                     review surface. Never cleared by any
--                                     build-DAG asset today (mi_gunanaka's own
--                                     registered clear target is
--                                     mimamsa_multipliers, a different table),
--                                     so a correction can only mark it, not
--                                     regenerate it.
--
-- Same three orthogonal columns as migration 1122, same semantics:
--
--   chart_context_stale_at               NULL while current; set the instant a
--                                         correction supersedes the birth
--                                         details the row was computed under.
--   chart_context_stale_reason           'chart_details_changed' — the only
--                                         reason a correction ever needs.
--   chart_context_superseded_by_run_id   the correction's rebuild run. ON
--                                         DELETE SET NULL: pruning a run never
--                                         erases which rows it made historical.
--
-- The row itself is never deleted, edited or reclassified — lifecycle_status,
-- outcome, confirmed/denied/falsified/dismissed/matched/observed values, claim
-- text, confidence, window, direction, domain and (for
-- brahma_mimamsa_prediction_ledger) every field
-- `trg_bmpl_freeze_confirmed` (migration 470) already freezes past `detected`
-- (build_id, priors_version, formula_versions, ranking_config,
-- now_context_date, claim_text, domain, window, confidence, direction) are all
-- untouched by this migration and by the marking transaction: the new columns
-- are outside that trigger's own equality check, so marking a frozen/confirmed
-- row stale never conflicts with its freeze.
--
-- Additive and idempotent: IF NOT EXISTS columns/index, pg_constraint-guarded
-- constraints. No existing row is rewritten; every existing row's
-- chart_context_stale_at is NULL and satisfies the CHECKs.
--
-- Lock note (same as migrations 359/414/415/1122): the migrate.ts runner wraps
-- each file in BEGIN/COMMIT, incompatible with CREATE INDEX CONCURRENTLY, so
-- these are plain index builds under an ACCESS EXCLUSIVE lock for the
-- migration's duration; all three tables are small (chart-scoped, per-chart
-- ledgers/snapshots), so the lock window is brief.
--
-- Known follow-up (recorded here, not fixed by this migration): applying this
-- migration changes these three tables' DDL shape. No schema-hash pin exists
-- for them today (unlike mimamsa_predictions'
-- MIMAMSA_PREDICTIONS_SCHEMA_PIN.json) — confirmed by inspecting
-- platform/scripts/governance/ before authoring this migration — so no
-- baseline needs regenerating for this change specifically.

ALTER TABLE public.brahma_mimamsa_prediction_ledger
  ADD COLUMN IF NOT EXISTS chart_context_stale_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS chart_context_stale_reason TEXT,
  ADD COLUMN IF NOT EXISTS chart_context_superseded_by_run_id UUID;

ALTER TABLE public.brahma_prospective_ledger
  ADD COLUMN IF NOT EXISTS chart_context_stale_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS chart_context_stale_reason TEXT,
  ADD COLUMN IF NOT EXISTS chart_context_superseded_by_run_id UUID;

ALTER TABLE public.mimamsa_calibration_snapshot
  ADD COLUMN IF NOT EXISTS chart_context_stale_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS chart_context_stale_reason TEXT,
  ADD COLUMN IF NOT EXISTS chart_context_superseded_by_run_id UUID;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'brahma_mimamsa_prediction_ledger_stale_reason_check'
  ) THEN
    ALTER TABLE public.brahma_mimamsa_prediction_ledger
      ADD CONSTRAINT brahma_mimamsa_prediction_ledger_stale_reason_check
      CHECK (chart_context_stale_reason IS NULL OR chart_context_stale_reason IN ('chart_details_changed'));
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'brahma_mimamsa_prediction_ledger_stale_pair_check'
  ) THEN
    ALTER TABLE public.brahma_mimamsa_prediction_ledger
      ADD CONSTRAINT brahma_mimamsa_prediction_ledger_stale_pair_check
      CHECK ((chart_context_stale_at IS NULL) = (chart_context_stale_reason IS NULL));
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'brahma_mimamsa_prediction_ledger_superseded_by_run_id_fkey'
  ) THEN
    ALTER TABLE public.brahma_mimamsa_prediction_ledger
      ADD CONSTRAINT brahma_mimamsa_prediction_ledger_superseded_by_run_id_fkey
      FOREIGN KEY (chart_context_superseded_by_run_id)
      REFERENCES public.build_runs(id) ON DELETE SET NULL;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'brahma_prospective_ledger_stale_reason_check'
  ) THEN
    ALTER TABLE public.brahma_prospective_ledger
      ADD CONSTRAINT brahma_prospective_ledger_stale_reason_check
      CHECK (chart_context_stale_reason IS NULL OR chart_context_stale_reason IN ('chart_details_changed'));
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'brahma_prospective_ledger_stale_pair_check'
  ) THEN
    ALTER TABLE public.brahma_prospective_ledger
      ADD CONSTRAINT brahma_prospective_ledger_stale_pair_check
      CHECK ((chart_context_stale_at IS NULL) = (chart_context_stale_reason IS NULL));
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'brahma_prospective_ledger_superseded_by_run_id_fkey'
  ) THEN
    ALTER TABLE public.brahma_prospective_ledger
      ADD CONSTRAINT brahma_prospective_ledger_superseded_by_run_id_fkey
      FOREIGN KEY (chart_context_superseded_by_run_id)
      REFERENCES public.build_runs(id) ON DELETE SET NULL;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'mimamsa_calibration_snapshot_stale_reason_check'
  ) THEN
    ALTER TABLE public.mimamsa_calibration_snapshot
      ADD CONSTRAINT mimamsa_calibration_snapshot_stale_reason_check
      CHECK (chart_context_stale_reason IS NULL OR chart_context_stale_reason IN ('chart_details_changed'));
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'mimamsa_calibration_snapshot_stale_pair_check'
  ) THEN
    ALTER TABLE public.mimamsa_calibration_snapshot
      ADD CONSTRAINT mimamsa_calibration_snapshot_stale_pair_check
      CHECK ((chart_context_stale_at IS NULL) = (chart_context_stale_reason IS NULL));
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'mimamsa_calibration_snapshot_superseded_by_run_id_fkey'
  ) THEN
    ALTER TABLE public.mimamsa_calibration_snapshot
      ADD CONSTRAINT mimamsa_calibration_snapshot_superseded_by_run_id_fkey
      FOREIGN KEY (chart_context_superseded_by_run_id)
      REFERENCES public.build_runs(id) ON DELETE SET NULL;
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_brahma_mimamsa_prediction_ledger_chart_current
  ON public.brahma_mimamsa_prediction_ledger(chart_id)
  WHERE chart_context_stale_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_brahma_prospective_ledger_chart_current
  ON public.brahma_prospective_ledger(chart_id)
  WHERE chart_context_stale_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_mimamsa_calibration_snapshot_chart_current
  ON public.mimamsa_calibration_snapshot(chart_id)
  WHERE chart_context_stale_at IS NULL;

COMMENT ON COLUMN public.brahma_mimamsa_prediction_ledger.chart_context_stale_at IS
  'NULL = reflects the chart''s current birth details. Set once a correction supersedes them. Outside trg_bmpl_freeze_confirmed''s equality check — marking a confirmed row stale never conflicts with its freeze.';
COMMENT ON COLUMN public.brahma_mimamsa_prediction_ledger.chart_context_stale_reason IS
  'NULL = current. chart_details_changed = superseded by a chart-details correction.';
COMMENT ON COLUMN public.brahma_mimamsa_prediction_ledger.chart_context_superseded_by_run_id IS
  'The correction''s rebuild run; SET NULL if the run row is pruned.';
COMMENT ON COLUMN public.brahma_prospective_ledger.chart_context_stale_at IS
  'NULL = reflects the chart''s current birth details. Set once a correction supersedes them; lifecycle_status is never touched by this marker.';
COMMENT ON COLUMN public.brahma_prospective_ledger.chart_context_stale_reason IS
  'NULL = current. chart_details_changed = superseded by a chart-details correction.';
COMMENT ON COLUMN public.brahma_prospective_ledger.chart_context_superseded_by_run_id IS
  'The correction''s rebuild run; SET NULL if the run row is pruned.';
COMMENT ON COLUMN public.mimamsa_calibration_snapshot.chart_context_stale_at IS
  'NULL = reflects the chart''s current birth details. Set once a correction supersedes them; publication_status/two_key_complete are never touched by this marker.';
COMMENT ON COLUMN public.mimamsa_calibration_snapshot.chart_context_stale_reason IS
  'NULL = current. chart_details_changed = superseded by a chart-details correction.';
COMMENT ON COLUMN public.mimamsa_calibration_snapshot.chart_context_superseded_by_run_id IS
  'The correction''s rebuild run; SET NULL if the run row is pruned.';
