-- Migration 1120: Jātaka conversation archive context (JATAKA-REQ-01).
--
-- Number: 1120 is the first cross-cutting number above the Pūrṇa (1042–1069) and
-- L3 Kāla (1070–1119) partitions, reserved on origin/campaign-coordination by
-- JATAKA-REQ-01 (native-authorized 2026-09-27) after a live origin/main + open-PR
-- sweep. Authored under JATAKA_CHART_WORKSPACE_PARALLEL_EXECUTION_AMENDMENT_v1_0;
-- NOT applied in that phase.
--
-- Purpose: when an authorised owner corrects a chart's computation-affecting birth
-- details (date, time, place, coordinates, timezone, ayanāṃśas), the chart keeps
-- its UUID and grants, every active conversation for it is archived, and the whole
-- per-chart corpus is recomputed. Those archived conversations must remain
-- readable as clearly historical material without being reconstructed from the
-- newly edited chart row. This migration adds the metadata that makes that
-- possible:
--
--   archive_reason           'chart_details_changed' for a correction archive;
--                            NULL for an ordinary manual archive, whose existing
--                            semantics are unchanged.
--   archived_chart_snapshot  the pre-correction chart input set (name, birth
--                            date/time/place, coordinates, timezone and effective
--                            offset, ayanāṃśas, capture time) — an immutable
--                            historical record, never live chart fields,
--                            ownership or derived facts.
--   archived_by_run_id       the rebuild run created by that correction.
--                            ON DELETE SET NULL: pruning a run never deletes or
--                            un-archives the history it produced.
--
-- Only `chart_details_changed` archives are system-locked read-only (enforced in
-- the application's turn-writing and conversation-mutation doors). The
-- correction-snapshot CHECK below makes the lock structural too: a correction
-- archive can never be un-archived or lose its snapshot while its reason stands.
--
-- Additive and idempotent: IF NOT EXISTS columns/index and pg_constraint-guarded
-- constraints. No existing row is rewritten; every existing row has
-- archive_reason NULL and satisfies both CHECKs.

ALTER TABLE public.conversations
  ADD COLUMN IF NOT EXISTS archive_reason TEXT,
  ADD COLUMN IF NOT EXISTS archived_chart_snapshot JSONB,
  ADD COLUMN IF NOT EXISTS archived_by_run_id UUID;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'conversations_archive_reason_check'
  ) THEN
    ALTER TABLE public.conversations
      ADD CONSTRAINT conversations_archive_reason_check
      CHECK (archive_reason IS NULL OR archive_reason IN ('chart_details_changed'));
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'conversations_correction_archive_snapshot_check'
  ) THEN
    ALTER TABLE public.conversations
      ADD CONSTRAINT conversations_correction_archive_snapshot_check
      CHECK (
        archive_reason IS DISTINCT FROM 'chart_details_changed'
        OR (archived_at IS NOT NULL AND archived_chart_snapshot IS NOT NULL)
      );
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'conversations_archived_by_run_id_fkey'
  ) THEN
    ALTER TABLE public.conversations
      ADD CONSTRAINT conversations_archived_by_run_id_fkey
      FOREIGN KEY (archived_by_run_id)
      REFERENCES public.build_runs(id) ON DELETE SET NULL;
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_conversations_chart_archive_reason
  ON public.conversations(chart_id, archive_reason, archived_at DESC)
  WHERE archived_at IS NOT NULL;

COMMENT ON COLUMN public.conversations.archive_reason IS
  'NULL = manual archive (existing semantics). chart_details_changed = archived by a chart-details correction; system-locked read-only.';
COMMENT ON COLUMN public.conversations.archived_chart_snapshot IS
  'Immutable pre-correction chart input snapshot (ChartInputSnapshot) captured when a correction archived this conversation.';
COMMENT ON COLUMN public.conversations.archived_by_run_id IS
  'Rebuild run created by the correction that archived this conversation; SET NULL if the run row is pruned.';
