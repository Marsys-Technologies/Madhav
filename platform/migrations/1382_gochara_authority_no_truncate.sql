-- Migration 1382: retain Gochara authority through generation-blind TRUNCATE.
-- Created: 2026-10-15. J-6m pre-build, SR-A4-01.
-- NEEDS-PROTECTED-WINDOW: CREATE TRIGGER in public. Apply after 1379 only
-- in its approved protected window; no authority row is changed by this file.
-- Allocation: 1380 highest on main; 1381 claimed by in-flight P06b.
-- 1236 and 1379 remain immutable. migrate.ts owns the transaction.
--
-- 1379 refuses DELETE of a governed head, requiring an explicit retained-head
-- UPDATE. TRUNCATE bypasses row triggers and would erase that head, silently
-- selecting the absent-row legacy default. Refuse it even in replica mode.
-- (I) INTERPRETATION: retain the family-wide ban on generation-blind TRUNCATE,
-- including legacy-only/empty tables; scoped legacy DELETE remains unchanged.

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint
      WHERE conrelid = 'public.kala_gochara_authority'::regclass
        AND conname = 'kga_sealed_authority_ck' AND contype = 'c' AND convalidated)
     OR to_regprocedure('public.ka_gochara_refuse_truncate()') IS NULL THEN
    RAISE EXCEPTION '1382 preflight: validated sealed authority CHECK (1379) and family truncate guard required';
  END IF;
END;
$$;

CREATE TRIGGER kala_gochara_authority_no_truncate
  BEFORE TRUNCATE ON public.kala_gochara_authority
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_refuse_truncate();
ALTER TABLE public.kala_gochara_authority
  ENABLE ALWAYS TRIGGER kala_gochara_authority_no_truncate;
COMMENT ON TRIGGER kala_gochara_authority_no_truncate ON public.kala_gochara_authority IS
  '1382: preserve authority; restore an explicit retained previous head, never the implicit legacy default via TRUNCATE.';

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_trigger
      WHERE tgrelid = 'public.kala_gochara_authority'::regclass
        AND tgname = 'kala_gochara_authority_no_truncate'
        AND NOT tgisinternal AND tgenabled = 'A' AND tgtype = 34
        AND tgfoid = 'public.ka_gochara_refuse_truncate()'::regprocedure) THEN
    RAISE EXCEPTION '1382 postflight: ALWAYS BEFORE STATEMENT truncate refusal required';
  END IF;
END;
$$;
