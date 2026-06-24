-- Add updated_at to profiles; backfill with created_at.
-- The PATCH route already writes updated_at=now() on every user edit;
-- this column simply did not exist, causing every PATCH to throw.

ALTER TABLE public.profiles
  ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ;

UPDATE public.profiles SET updated_at = created_at WHERE updated_at IS NULL;
