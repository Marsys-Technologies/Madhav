-- DRAFT — NOT A MIGRATION YET. Do not move this file into platform/migrations and do not apply it.
--
-- Purpose (Codex round 3 on PR 3110, steward SLICE-CONSOLIDATED-3): the unconditional DATABASE guarantee that a TEST SLICE manifest
-- can never become `published`. Today the refusals are in code: the writer, `ledger.publish` (lock first, conditional flip), the
-- verification job, the seal flow and the contact-ledger reader. The builder role still holds UPDATE on the publication table
-- (migration 1216, line 104: GRANT SELECT, INSERT, UPDATE ON public.kala_gochara_publication TO data_plane_builder) and the 1240
-- guard refuses a flip only when a seal exists, so a direct UPDATE by that role is the one path code cannot close.
--
-- For the NEXT protected migration window. Needs native/steward approval and a version-bumped migration number; the number is
-- deliberately not assigned here.
--
-- A CHECK constraint, not a trigger: a trigger does not fire under session_replication_role = replica (a superuser can bypass it),
-- a CHECK does. The predicate is the one the code uses: either marker alone is enough.

-- PRE-FLIGHT (read-only; must return 0 before the constraint is added):
--   SELECT count(*) FROM public.kala_gochara_publication
--    WHERE status = 'published'
--      AND (COALESCE(input_generation_vector->>'stored_scope', '') = 'test_slice'
--           OR COALESCE(input_generation_vector ? 'test_slice', false));

BEGIN;

-- NOT VALID first: new and changed rows are checked immediately, existing rows are validated in the next statement (a short lock).
ALTER TABLE public.kala_gochara_publication
  ADD CONSTRAINT kala_gochara_publication_no_published_test_slice
  CHECK (
    status <> 'published'
    OR (COALESCE(input_generation_vector->>'stored_scope', '') <> 'test_slice'
        AND NOT COALESCE(input_generation_vector ? 'test_slice', false))
  ) NOT VALID;

ALTER TABLE public.kala_gochara_publication
  VALIDATE CONSTRAINT kala_gochara_publication_no_published_test_slice;

COMMENT ON CONSTRAINT kala_gochara_publication_no_published_test_slice ON public.kala_gochara_publication IS
  'A test-slice manifest (stored_scope test_slice, or a test_slice component in the input vector) may never be published. '
  'Pravaha C46 / A5.5g; the same predicate as ledger.publish.';

-- Post-check (inside the transaction): the constraint exists, is validated, and refuses the case it exists for.
DO $$
DECLARE ok boolean;
BEGIN
  SELECT convalidated INTO ok FROM pg_constraint
   WHERE conname = 'kala_gochara_publication_no_published_test_slice'
     AND conrelid = 'public.kala_gochara_publication'::regclass;
  IF ok IS DISTINCT FROM true THEN
    RAISE EXCEPTION 'kala_gochara_publication_no_published_test_slice is missing or not validated';
  END IF;
END
$$;

COMMIT;

-- NOT PART OF THIS DRAFT, to be decided with the team: narrowing the builder's grant from table-level UPDATE to the columns the
-- writer actually updates (publish_candidate replaces convention_id, input_generation_vector, ephemeris_backend, horizon,
-- row_counts, content_digest on a CANDIDATE row; only the seal flow and `ledger.publish` need `status`, `published_at`). A
-- column-level GRANT is only effective after the table-level one is revoked, and the writers and the seal flow must be re-tested
-- against it; that is its own change and its own review.
--
-- ROLLBACK:
--   ALTER TABLE public.kala_gochara_publication DROP CONSTRAINT IF EXISTS kala_gochara_publication_no_published_test_slice;
