-- Migration 1379: sealed-generation authority admission (KĀLA-YANTRA P09 / J-6m).
-- Created: 2026-10-15. NEEDS-PROTECTED-WINDOW: creates functions/triggers in public.
-- Allocated by scripts/ci/migration_number_guard.ts --next; reallocate on rebase.
-- Replaces, never edits, 1236. No authority row or generation content is changed.
-- migrate.ts owns the transaction (no nested BEGIN/COMMIT).

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint
      WHERE conrelid = 'public.kala_gochara_authority'::regclass
      AND conname = 'kga_governed_generation_refused_ck' AND convalidated) THEN
    RAISE EXCEPTION '1379 preflight: validated migration 1236 constraint required';
  END IF;
  IF to_regclass('public.ka_gochara_generation_seal') IS NULL
     OR to_regclass('public.kala_gochara_publication') IS NULL
     OR to_regprocedure('public.ka_gochara_lock_chart(uuid)') IS NULL THEN
    RAISE EXCEPTION '1379 preflight: governed publication/seal/locking schema required';
  END IF;
END;
$$;

-- A CHECK cannot contain a subquery directly. This predicate is also enforced by
-- serialized, ALWAYS triggers, including the reverse publication mutation path.
CREATE FUNCTION public.ka_gochara_authority_admissible(p_chart uuid, p_generation text)
RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog, public AS $$
  SELECT CASE WHEN p_generation !~ '^([5-9]|[1-9][0-9]+)\.[0-9]+$' THEN true ELSE EXISTS (
    SELECT 1 FROM public.kala_gochara_publication p
    JOIN public.ka_gochara_generation_seal s ON s.chart_id = p.chart_id
      AND s.generation = p.generation AND s.manifest_id = p.manifest_id
    WHERE p.chart_id = p_chart AND p.generation = p_generation AND p.status = 'published'
      AND coalesce(p.input_generation_vector ->> 'stored_scope', '') <> 'test_slice'
      AND NOT (p.input_generation_vector ? 'test_slice')
  ) END;
$$;
REVOKE ALL ON FUNCTION public.ka_gochara_authority_admissible(uuid,text) FROM PUBLIC;

CREATE FUNCTION public.ka_gochara_authority_sealed_guard()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, public AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    IF OLD.authoritative_generation ~ '^([5-9]|[1-9][0-9]+)\.[0-9]+$' THEN
      RAISE EXCEPTION 'gochara_authority_refused: rollback requires the explicit retained previous head, never DELETE'
        USING ERRCODE = 'check_violation';
    END IF;
    RETURN OLD;
  END IF;
  PERFORM public.ka_gochara_lock_chart(NEW.chart_id);
  IF NOT public.ka_gochara_authority_admissible(NEW.chart_id, NEW.authoritative_generation) THEN
    RAISE EXCEPTION 'gochara_authority_refused: governed head requires a published non-test-slice manifest and matching seal'
      USING ERRCODE = 'check_violation';
  END IF;
  RETURN NEW;
END;
$$;
REVOKE ALL ON FUNCTION public.ka_gochara_authority_sealed_guard() FROM PUBLIC;

CREATE TRIGGER kala_gochara_authority_0_statement_lock
  BEFORE UPDATE OR DELETE ON public.kala_gochara_authority
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_chart_statement_lock();
CREATE TRIGGER kala_gochara_authority_1_sealed_guard
  BEFORE INSERT OR UPDATE OR DELETE ON public.kala_gochara_authority
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_authority_sealed_guard();
ALTER TABLE public.kala_gochara_authority ENABLE ALWAYS TRIGGER kala_gochara_authority_0_statement_lock;
ALTER TABLE public.kala_gochara_authority ENABLE ALWAYS TRIGGER kala_gochara_authority_1_sealed_guard;

-- Keep admission true after the pointer is written too. Withdrawing or replacing
-- an authoritative manifest first requires switching/rolling back the authority.
CREATE FUNCTION public.ka_gochara_authoritative_manifest_guard()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, public AS $$
BEGIN
  IF OLD.generation ~ '^([5-9]|[1-9][0-9]+)\.[0-9]+$'
     AND EXISTS (SELECT 1 FROM public.kala_gochara_authority a
                 WHERE a.chart_id = OLD.chart_id AND a.authoritative_generation = OLD.generation)
     AND (TG_OP = 'DELETE' OR NEW IS DISTINCT FROM OLD) THEN
    RAISE EXCEPTION 'gochara_authority_refused: authoritative manifest is immutable; restore the previous head first'
      USING ERRCODE = 'check_violation';
  END IF;
  IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
  RETURN NEW;
END;
$$;
REVOKE ALL ON FUNCTION public.ka_gochara_authoritative_manifest_guard() FROM PUBLIC;
CREATE TRIGGER kala_gochara_publication_0_authority_statement_lock
  BEFORE UPDATE OR DELETE ON public.kala_gochara_publication
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_chart_statement_lock();
CREATE TRIGGER kala_gochara_publication_1_authority_guard
  BEFORE UPDATE OR DELETE ON public.kala_gochara_publication
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_authoritative_manifest_guard();
ALTER TABLE public.kala_gochara_publication ENABLE ALWAYS TRIGGER kala_gochara_publication_0_authority_statement_lock;
ALTER TABLE public.kala_gochara_publication ENABLE ALWAYS TRIGGER kala_gochara_publication_1_authority_guard;

-- Existing seal rows are permanent; guard the reverse path even in replica mode.
ALTER TABLE public.ka_gochara_generation_seal ENABLE ALWAYS TRIGGER ka_gochara_generation_seal_write_guard;
ALTER TABLE public.ka_gochara_generation_seal ENABLE ALWAYS TRIGGER ka_gochara_generation_seal_no_truncate;

-- Archived reader review 2: reject incompatible bounds on future writes. NOT VALID
-- avoids asserting that historical sealed rows were audited or rewriting them;
-- the reader independently refuses any historical non-half-open interval.
ALTER TABLE public.ka_gochara_eval_window ADD CONSTRAINT kgew_half_open_bounds_ck
  CHECK (lower_inc(interval) AND NOT upper_inc(interval)) NOT VALID;

-- CHECK evaluation uses the row writer's privileges. Grant just the predicate to
-- existing authority DML grantees (including the table owner), never schema CREATE.
DO $$
DECLARE r record;
BEGIN
  FOR r IN SELECT rolname FROM pg_roles
    WHERE has_table_privilege(oid, 'public.kala_gochara_authority', 'INSERT')
       OR has_table_privilege(oid, 'public.kala_gochara_authority', 'UPDATE')
  LOOP
    EXECUTE format('GRANT EXECUTE ON FUNCTION public.ka_gochara_authority_admissible(uuid,text) TO %I', r.rolname);
  END LOOP;
END;
$$;
ALTER TABLE public.kala_gochara_authority DROP CONSTRAINT kga_governed_generation_refused_ck;
ALTER TABLE public.kala_gochara_authority ADD CONSTRAINT kga_sealed_authority_ck
  CHECK (public.ka_gochara_authority_admissible(chart_id, authoritative_generation));
COMMENT ON CONSTRAINT kga_sealed_authority_ck ON public.kala_gochara_authority IS
  '1379: governed authority requires a published non-test-slice manifest and matching immutable seal. No flip is performed.';

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint
      WHERE conrelid = 'public.kala_gochara_authority'::regclass
        AND conname = 'kga_sealed_authority_ck' AND contype = 'c' AND convalidated)
     OR (SELECT count(*) FROM pg_trigger WHERE tgname IN (
       'kala_gochara_authority_0_statement_lock', 'kala_gochara_authority_1_sealed_guard',
       'kala_gochara_publication_0_authority_statement_lock', 'kala_gochara_publication_1_authority_guard')
       AND tgenabled = 'A') <> 4 THEN
    RAISE EXCEPTION '1379 postflight: validated CHECK and four ALWAYS triggers required';
  END IF;
END;
$$;
