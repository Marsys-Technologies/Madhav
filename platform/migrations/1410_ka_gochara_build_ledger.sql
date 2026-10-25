-- 1410_ka_gochara_build_ledger.sql
--
-- SR-RESUME-NOW (standing owner requirement OWNER-RESUMABLE-REQUIRED-20261025, "resumable substeps for heavy assets"), writer lane.
-- Allocated to item SR-RESUME-NOW writer lane in /Users/Dev/kalayantra/run/MIGRATION_ALLOCATION.json (branch kalayantra/century-resume-writer).
-- Transaction ownership belongs to platform/scripts/migrate.ts (no BEGIN/COMMIT here).
--
-- WHAT IT ADDS: ONE new table, public.ka_gochara_build_ledger — one row per COMMITTED substep of the ka_gochara_v5 CENTURY build, and the
-- grants on it. NOTHING ELSE: no existing table, function, trigger or row is touched; no applied migration is edited.
--
-- WHY. The orchestrator is FROZEN and never feeds `completed_keys` (migration 436 says so), so a failed 20-hour century build restarted from zero.
-- The writer itself now plans only what is not yet done (ka_sangam's pattern), and it needs a durable, auditable answer to "which substeps
-- committed, under which program, and what did each leave behind". The row is written by the writer INSIDE the substep's own savepoint /
-- transaction (the orchestrator commits after the substep), so a killed run can never leave a half-recorded substep: the substep's data and its
-- ledger row become durable together or not at all.
--
-- A ROW'S BINDING IDENTITY (what a resume must equal, else it REFUSES by name and never rebuilds):
--   implementation_digest  digest of the governed implementation modules (input_vector.IMPLEMENTATION_MODULES) of the program that ran the substep
--   writer_digest          get_writer_source_hash('ka_gochara_v5')
--   plan_digest            the full plan (ordered substep keys) and the staged config (rules profile, verify deferral, result policy, horizon)
--   horizon                the effective horizon
--   manifest_id / vector_sha256   the candidate manifest the substep was bound to (NULL for the substeps that run before the manifest exists)
-- WHAT IT LEFT BEHIND: rows_written (the WriterResult count) and, for chain substeps, `scope` (per owned table: row count and a content digest that
-- excludes write-time columns) with `scope_digest` over it. NULL scope = a GLOBAL idempotent substep (rules, convention, body:*) that owns no chart
-- x generation rows: an honest null, never a made-up digest. A resume recomputes every scope and refuses on any difference, naming the substep.
-- PROVENANCE: build_run_id and execution_id (CLOUD_RUN_EXECUTION, NULL when unset) of the run that produced the substep — the list of producer
-- executions of a generation. The sealer refuses a generation produced by more than one execution until the seal records that list.
--
-- No FOREIGN KEY to the manifest: the pre-manifest substeps are ledgered before the manifest exists. The century TEARDOWN lists this table in its
-- scope (platform/scripts/teardown_v5_small_test_job.py GENERATION_TABLES) and deletes it with the rest of the generation.
-- No write-guard triggers: this is bookkeeping, not an authority. Authority stays the chain and the manifest; every row is re-verified against
-- them at resume.
--
-- GRANTS (to the roles that EXIST; an absent role is NAMED in a NOTICE — never a grant to nobody passed off as done):
--   data_plane_builder   SELECT, INSERT, UPDATE, DELETE (the writer upserts; the century teardown, which runs as the builder, deletes)
--   gochara_verifier     SELECT only
--   gochara_sealer       SELECT only (the sealer reads the producer-execution list)
--   amjis_app            SELECT only (SR-RESUME-INTEGRATION: the app role reads the ledger for the century resume readback; the privilege is a stated fact,
--                        never inferred from table ownership)
--
-- ROUTE: public-schema DDL — a Kāla protected-window migration (derived automatically by governance/kala_protected_migrations.py).
-- IDEMPOTENT: CREATE TABLE / INDEX IF NOT EXISTS; GRANT of a held privilege is a no-op. FAIL-CLOSED: refuses when a prerequisite is missing,
-- and the post-apply block raises unless the table, its key and every grant are exactly as stated.
-- ROLLBACK (legal while no resume depends on it; loses only bookkeeping, never chain data): DROP TABLE public.ka_gochara_build_ledger;
-- the writer then refuses a century run by name (build_ledger_absent) until the table is back.

SET LOCAL lock_timeout = '5s';

-- ── 0. Prerequisites (fail-closed) ───────────────────────────────────────────
DO $$
DECLARE missing text;
BEGIN
  SELECT string_agg(x.name, ', ') INTO missing
  FROM (VALUES ('public.charts'), ('public.kala_gochara_publication')) AS x(name)
  WHERE to_regclass(x.name) IS NULL;
  IF missing IS NOT NULL THEN
    RAISE EXCEPTION 'migration 1410: prerequisite table(s) missing: %', missing;
  END IF;
END;
$$;

-- ── 1. The ledger ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.ka_gochara_build_ledger (
  chart_id              UUID        NOT NULL REFERENCES public.charts(id),
  generation            TEXT        NOT NULL,
  substep_key           TEXT        NOT NULL,
  ordinal               INTEGER     NOT NULL,
  manifest_id           UUID,
  vector_sha256         TEXT,
  implementation_digest TEXT        NOT NULL,
  writer_digest         TEXT        NOT NULL,
  plan_digest           TEXT        NOT NULL,
  horizon               TSTZRANGE   NOT NULL,
  build_run_id          TEXT        NOT NULL,
  execution_id          TEXT,
  rows_written          INTEGER     NOT NULL,
  scope                 JSONB,
  scope_digest          TEXT,
  committed_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

  PRIMARY KEY (chart_id, generation, substep_key),
  CONSTRAINT kgbl_ordinal_uq UNIQUE (chart_id, generation, ordinal),
  CONSTRAINT kgbl_key_ck CHECK (length(btrim(substep_key)) > 0),
  CONSTRAINT kgbl_ordinal_ck CHECK (ordinal >= 0),
  CONSTRAINT kgbl_rows_ck CHECK (rows_written >= 0),
  CONSTRAINT kgbl_digests_ck CHECK (
    implementation_digest ~ '^[0-9a-f]{64}$' AND writer_digest ~ '^[0-9a-f]{64}$' AND plan_digest ~ '^[0-9a-f]{64}$'
    AND (vector_sha256 IS NULL OR vector_sha256 ~ '^[0-9a-f]{64}$')
    AND (scope_digest IS NULL OR scope_digest ~ '^[0-9a-f]{64}$')),
  -- a manifest-bound row carries BOTH halves of the binding or neither
  CONSTRAINT kgbl_manifest_binding_ck CHECK ((manifest_id IS NULL) = (vector_sha256 IS NULL)),
  -- a scope and its digest travel together; NULL = a global idempotent substep
  CONSTRAINT kgbl_scope_ck CHECK ((scope IS NULL) = (scope_digest IS NULL)
    AND (scope IS NULL OR jsonb_typeof(scope) = 'object'))
);

COMMENT ON TABLE public.ka_gochara_build_ledger IS
  'SR-RESUME-NOW (OWNER-RESUMABLE-REQUIRED-20261025): one row per committed substep of the ka_gochara_v5 century build, written by the writer inside '
  'the substep''s own transaction. Binding identity (implementation/writer/plan digests, horizon, manifest) + what the substep left behind (scope: '
  'rows and content digest per owned table) + which execution produced it. A resume skips a recorded substep only after re-measuring its scope and '
  'proving the program is unchanged; any difference refuses by name. Bookkeeping only: the chain and the manifest stay the authority.';
COMMENT ON COLUMN public.ka_gochara_build_ledger.scope IS
  'Per owned table: {rows, digest} (content digest excluding write-time columns). NULL = a global idempotent substep that owns no chart x generation rows.';

-- ── 2. Grants ────────────────────────────────────────────────────────────────
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'data_plane_builder') THEN
    GRANT SELECT, INSERT, UPDATE, DELETE ON public.ka_gochara_build_ledger TO data_plane_builder;
    RAISE NOTICE 'migration 1410: builder grants issued to role data_plane_builder';
  ELSE
    RAISE NOTICE 'migration 1410: role data_plane_builder NOT FOUND — NO builder grant was issued; the century build cannot record its progress until it is provisioned and granted';
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gochara_verifier') THEN
    GRANT SELECT ON public.ka_gochara_build_ledger TO gochara_verifier;
    RAISE NOTICE 'migration 1410: verifier SELECT grant issued to role gochara_verifier';
  ELSE
    RAISE NOTICE 'migration 1410: role gochara_verifier NOT FOUND — NO verifier grant was issued';
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gochara_sealer') THEN
    GRANT SELECT ON public.ka_gochara_build_ledger TO gochara_sealer;
    RAISE NOTICE 'migration 1410: sealer SELECT grant issued to role gochara_sealer';
  ELSE
    RAISE NOTICE 'migration 1410: role gochara_sealer NOT FOUND — NO sealer grant was issued; the sealer cannot read the producer-execution list until it is provisioned and granted';
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'amjis_app') THEN
    GRANT SELECT ON public.ka_gochara_build_ledger TO amjis_app;
    RAISE NOTICE 'migration 1410: app SELECT grant issued to role amjis_app';
  ELSE
    RAISE NOTICE 'migration 1410: role amjis_app NOT FOUND — NO app grant was issued; the century resume readback cannot read the ledger until it is provisioned and granted';
  END IF;
END;
$$;

-- ── 3. Post-apply presence checks (raise, never a silent skip) ───────────────
DO $$
DECLARE r text; missing text;
BEGIN
  IF to_regclass('public.ka_gochara_build_ledger') IS NULL THEN
    RAISE EXCEPTION 'migration 1410 post-apply check failed: public.ka_gochara_build_ledger is missing';
  END IF;
  SELECT string_agg(x.name, ', ') INTO missing
  FROM (VALUES ('kgbl_ordinal_uq'), ('kgbl_key_ck'), ('kgbl_ordinal_ck'), ('kgbl_rows_ck'), ('kgbl_digests_ck'),
               ('kgbl_manifest_binding_ck'), ('kgbl_scope_ck')) AS x(name)
  WHERE NOT EXISTS (SELECT 1 FROM pg_constraint c WHERE c.conname = x.name AND c.convalidated
                    AND c.conrelid = 'public.ka_gochara_build_ledger'::regclass);
  IF missing IS NOT NULL THEN
    RAISE EXCEPTION 'migration 1410 post-apply check failed: missing or unvalidated constraint(s): %', missing;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint c WHERE c.contype = 'p' AND c.conrelid = 'public.ka_gochara_build_ledger'::regclass) THEN
    RAISE EXCEPTION 'migration 1410 post-apply check failed: the primary key (chart_id, generation, substep_key) is missing';
  END IF;
  IF to_regrole('data_plane_builder') IS NOT NULL
     AND NOT (has_table_privilege('data_plane_builder', 'public.ka_gochara_build_ledger', 'SELECT')
              AND has_table_privilege('data_plane_builder', 'public.ka_gochara_build_ledger', 'INSERT')
              AND has_table_privilege('data_plane_builder', 'public.ka_gochara_build_ledger', 'UPDATE')
              AND has_table_privilege('data_plane_builder', 'public.ka_gochara_build_ledger', 'DELETE')) THEN
    RAISE EXCEPTION 'migration 1410 post-apply check failed: the builder does not hold SELECT, INSERT, UPDATE and DELETE on the ledger';
  END IF;
  FOREACH r IN ARRAY ARRAY['gochara_verifier', 'gochara_sealer'] LOOP
    IF to_regrole(r) IS NOT NULL THEN
      IF NOT has_table_privilege(r, 'public.ka_gochara_build_ledger', 'SELECT') THEN
        RAISE EXCEPTION 'migration 1410 post-apply check failed: % cannot read the ledger', r;
      END IF;
      IF has_table_privilege(r, 'public.ka_gochara_build_ledger', 'INSERT') OR has_table_privilege(r, 'public.ka_gochara_build_ledger', 'UPDATE')
         OR has_table_privilege(r, 'public.ka_gochara_build_ledger', 'DELETE') OR has_table_privilege(r, 'public.ka_gochara_build_ledger', 'TRUNCATE')
         OR has_any_column_privilege(r, 'public.ka_gochara_build_ledger', 'INSERT') OR has_any_column_privilege(r, 'public.ka_gochara_build_ledger', 'UPDATE') THEN
        RAISE EXCEPTION 'migration 1410 post-apply check failed: % holds a WRITE privilege on the ledger (it reads only)', r;
      END IF;
    END IF;
  END LOOP;
  IF to_regrole('amjis_app') IS NOT NULL AND NOT has_table_privilege('amjis_app', 'public.ka_gochara_build_ledger', 'SELECT') THEN
    RAISE EXCEPTION 'migration 1410 post-apply check failed: amjis_app cannot read the ledger (SELECT is granted explicitly, never assumed from ownership)';
  END IF;
  RAISE NOTICE 'migration 1410: presence checks passed';
END;
$$;
