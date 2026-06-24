-- Admin audit log: record every admin action on user accounts.
-- actor_id and target_user_id use SET NULL on delete so the log survives
-- even if the involved accounts are later removed.

CREATE TABLE IF NOT EXISTS public.admin_audit_log (
  id             UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  actor_id       TEXT        REFERENCES public.profiles(id) ON DELETE SET NULL,
  action         TEXT        NOT NULL,
  target_user_id TEXT        REFERENCES public.profiles(id) ON DELETE SET NULL,
  detail         JSONB,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS admin_audit_log_created_at_idx
  ON public.admin_audit_log (created_at DESC);
