-- Production's stricter generation guard on public.kala_gochara_windows, captured READ-ONLY from the production catalog on 2026-10-04
-- (pg_get_functiondef + pg_get_triggerdef; no table row was read). Installed in production by the cutover script, NOT by a migration, so
-- the repository carries no copy: this file is the fixture the C55 test installs (profile "production") BEFORE migration 1071, which then
-- verifies and skips exactly as it does in production (1071's REPAIR NOTE). Query used:
--   select pg_get_functiondef(p.oid) from pg_proc p join pg_namespace n on n.oid = p.pronamespace
--    where n.nspname = 'public' and p.proname = 'kala_gochara_generation_guard';
--   select tgname, pg_get_triggerdef(oid) from pg_trigger where tgrelid = 'public.kala_gochara_windows'::regclass and tgname like 'trg_kgw_%';
-- Protects generations 'v1' AND '3.0' (row DELETE/UPDATE; TRUNCATE while such a row exists); the override is the session GUC
-- app.allow_protected_sweep_rewrite = 'on'. A drift of the production definition from this text must be re-captured, never edited by hand.
CREATE OR REPLACE FUNCTION public.kala_gochara_generation_guard()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
DECLARE
  guard_generation TEXT;
BEGIN
  -- Per-session override reserved for the release authority, same convention
  -- as migration 540's app.allow_protected_sweep_rewrite.
  IF current_setting('app.allow_protected_sweep_rewrite', true) = 'on' THEN
    RETURN COALESCE(NEW, OLD);
  END IF;

  IF TG_OP = 'TRUNCATE' THEN
    -- TRUNCATE has no row scope: refuse whenever the table holds any
    -- protected-generation row.
    IF EXISTS (SELECT 1 FROM kala_gochara_windows
               WHERE generation IN ('v1', '3.0')) THEN
      RAISE EXCEPTION
        'GOCHARA GENERATION GUARD: TRUNCATE on kala_gochara_windows refused — '
        'the table holds protected generations (v1, 3.0). Set '
        'app.allow_protected_sweep_rewrite=on for this session to override '
        '(release authority only).';
    END IF;
    RETURN NULL;
  END IF;

  guard_generation := OLD.generation;
  IF guard_generation IN ('v1', '3.0') THEN
    RAISE EXCEPTION
      'GOCHARA GENERATION GUARD: % on kala_gochara_windows refused for '
      'protected generation % (row id %, chart %). Set '
      'app.allow_protected_sweep_rewrite=on for this session to override '
      '(release authority only).',
      TG_OP, guard_generation, OLD.id, OLD.chart_id;
  END IF;
  -- UPDATE may not re-label a row INTO a protected generation either.
  IF TG_OP = 'UPDATE' AND NEW.generation IN ('v1', '3.0')
     AND NEW.generation IS DISTINCT FROM OLD.generation THEN
    RAISE EXCEPTION
      'GOCHARA GENERATION GUARD: UPDATE may not re-label row id % into '
      'protected generation %.', OLD.id, NEW.generation;
  END IF;
  RETURN COALESCE(NEW, OLD);
END;
$function$

;
CREATE TRIGGER trg_kgw_generation_guard_row BEFORE DELETE OR UPDATE ON public.kala_gochara_windows FOR EACH ROW EXECUTE FUNCTION kala_gochara_generation_guard();
CREATE TRIGGER trg_kgw_generation_guard_truncate BEFORE TRUNCATE ON public.kala_gochara_windows FOR EACH STATEMENT EXECUTE FUNCTION kala_gochara_generation_guard();
