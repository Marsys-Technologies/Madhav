-- K5-G1a follow-up, cockpit allocation R-2026-10-16-01.
-- NEEDS-PROTECTED-WINDOW. Forward-only repair of 1385's LIKE copy:
-- INCLUDING DEFAULTS does not copy GENERATED AS IDENTITY (legacy 490/496).
-- No legacy DDL/DML, serving switch or grants. Candidate IDs stay independent.
SET LOCAL lock_timeout = '5s';

DO $identity$
DECLARE source text; target text; next_id bigint;
BEGIN
  FOREACH source IN ARRAY ARRAY[
    'kala_field_clocks', 'kala_field_boundaries', 'kala_timeline_spec'
  ] LOOP
    target := source || '_candidate';
    -- Lock before inspecting identity as well, so concurrent reapplication
    -- observes the first repair after waiting for its DDL transaction.
    EXECUTE format('LOCK TABLE public.%I IN ACCESS EXCLUSIVE MODE', target);
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_schema='public' AND table_name=target AND column_name='id'
        AND is_identity='YES'
    ) THEN
      -- Hold the table across MAX and ADD IDENTITY so an explicit-ID insert
      -- cannot race the initial sequence value. Preserve any existing rows.
      EXECUTE format('SELECT greatest(coalesce(max(id), 0) + 1, 1) FROM public.%I', target) INTO next_id;
      EXECUTE format('ALTER TABLE public.%I ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (START WITH %s)', target, next_id);
    END IF;
  END LOOP;
END $identity$;
