-- Migration 1419: Record when a paused preparation is dispatched again
-- Created: 2026-11-20

SET LOCAL lock_timeout = '5s';

ALTER TABLE public.build_runs
  ADD COLUMN IF NOT EXISTS resume_requested_at timestamptz;

COMMENT ON COLUMN public.build_runs.resume_requested_at IS
  'Last accepted paused-to-planned resume request. Distinct from the actual worker start time.';
