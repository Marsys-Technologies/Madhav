-- Migration 1265: L5 frozen-prediction guard -- capture the live builder guard into the repo and add the
-- UPDATE/DELETE/TRUNCATE guard on frozen mimamsa_predictions rows (Suvarna, SS ruling N-104).
-- Created: 2026-10-03
--
-- HELD: own draft PR, merges only on SS's review, AFTER S-L1, and (see PRIVILEGE) only into a protected window.
-- It must be in place BEFORE any L5 (mi_bhavisya) rebuild. Do not arm / auto-merge.
--
-- RULING (SS N-104): "DB-enforced immutability: YES. Capture the live guard function into the repo (live-only DB
-- code is drift) and add an UPDATE/DELETE guard on frozen rows. Migration 1265. Before any L5 rebuild."
--
-- WHAT IT DOES (three parts, one transaction, schema/code only: no row of any table is written or kept)
--   1. CAPTURE. public.mimamsa_predictions_builder_guard() and its trigger exist in the live database and in no
--      file of main (applied out of band; the text is identical, md5 for md5, to Part A2 of BUILDER_GRANT_PLAN v1.3,
--      a docs-only draft on branch suvarna/land/grant-plan-001 dated 2026-10-01; the application date is not
--      recorded in the repo).
--      This migration holds the function EXACTLY as it is live (body bytes below; md5 + length asserted), the
--      attributes (plpgsql, SECURITY INVOKER, search_path = pg_catalog, pg_temp, VOLATILE, no PUBLIC EXECUTE) and
--      the trigger shape (BEFORE INSERT OR DELETE, FOR EACH ROW, enabled 'O'). Provenance: read as suvarna_reader on
--      production on 2026-10-03 (PostgreSQL 15.18): prosrc md5 46c23854275c2712b30860a2b174adb2, length 1084 bytes,
--      proowner amjis_app, proacl {amjis_app=X/amjis_app}, proconfig {search_path=pg_catalog, pg_temp};
--      pg_get_triggerdef: CREATE TRIGGER mimamsa_predictions_builder_guard BEFORE INSERT OR DELETE ON
--      public.mimamsa_predictions FOR EACH ROW EXECUTE FUNCTION mimamsa_predictions_builder_guard(); tgtype 15,
--      tgenabled 'O', tgnargs 0. MD5 GUARD: if a function of that name exists and its body (or attributes) is not
--      the captured one, the migration REFUSES (it will not overwrite a hand-edited live function); if the trigger
--      exists with another shape it refuses; if either is absent (a fresh replay) it creates them.
--   2. GUARD. New function public.mimamsa_predictions_frozen_row_guard() and two triggers:
--        mimamsa_predictions_frozen_row_guard           BEFORE UPDATE OR DELETE FOR EACH ROW  (ENABLE ALWAYS)
--        mimamsa_predictions_frozen_row_guard_truncate  BEFORE TRUNCATE FOR EACH STATEMENT    (ENABLE ALWAYS)
--      It applies to EVERY role, owners and superusers included, and (ENABLE ALWAYS) also when
--      session_replication_role = replica. DEFINITION OF "FROZEN": every row of this table. Each row is written once
--      at freeze (frozen_bundle_hash, emitted_at are NOT NULL) and the table has no "unfrozen" state: the 195 live
--      rows are all lifecycle_status 'pending', i.e. frozen AND awaiting an outcome. A guard that protected only
--      confirmed/denied/partial rows would protect none of them, so PENDING rows are protected too.
--      UPDATE: allow-list. Only these columns may change, nothing else (also not a column added later: the test is
--      to_jsonb(row) minus the allow-list, fail closed):
--        lifecycle_status                   only pending -> due/confirmed/denied/partial/expired and
--                                           due -> confirmed/denied/partial/expired (writers: mi_abhilekha.py:70
--                                           pending -> confirmed/denied; prediction_lifecycle_sweep.ts:348 -> expired).
--                                           A terminal status never changes again; a no-op update is allowed.
--        chart_context_stale_at / _reason   NULL -> value once (the birth-details-correction marker, migration 1122,
--                                           chartContextStaleness.ts); never changed or cleared afterwards.
--        chart_context_superseded_by_run_id set together with the marker; afterwards only -> NULL (the FK to
--                                           build_runs is ON DELETE SET NULL, which is an UPDATE of this table).
--      Frozen (any status, pending included): chart_id, prediction_id, source_pramana_id, outcome_claim, domain,
--      observation_window, eval_date, confidence_band, magnitude_expected, falsifier_jsonb, base_rate, emitted_at,
--      driving_signals, frozen_bundle_hash, bundle_formula_version, created_at, contact_id. This is the column
--      migration 680 rewrote on 191 of 195 rows (source_pramana_id): that is now refused.
--      DELETE: refused for every row and every role, pending and due included (the live mi_bhavisya writer and the
--      cockpit clear spec delete pending/due rows: both must be changed first, see ORDER). ONE exception, narrowly
--      defined and data-driven (no setting, no role, no password): the row's chart has a chart_subject_consent row
--      with consent_state = 'withdrawn' AND no chart_subject_deletion_disputes row in open/reopened/escalated. That
--      is exactly the condition under which the consent sweep (consent/withdrawal.ts) deletes subject-scoped rows,
--      and the sweep leaves its own record (hash-chained 'withdrawn' consent event, per-table tombstone with row
--      count and content hash); each authorized row delete also writes a server-log line (RAISE LOG). If the consent
--      tables are absent or unreadable by the invoker the exception does not apply (fail closed).
--      TRUNCATE: refused always.
--      Break-glass (not a feature): a reviewed migration may ALTER TABLE ... DISABLE TRIGGER mimamsa_predictions_
--      frozen_row_guard inside its own transaction, with a before/after frozen-set digest in the same file; no
--      setting turns the guard off. The table owner (and a superuser) CAN disable a trigger: PostgreSQL has no
--      mechanism that prevents it. tgenabled <> 'A' is the visible signature (see VERIFICATION).
--   3. SELF-TEST. A live detector inside the migration: a throwaway probe row (random chart, rolled back by an
--      exception) is inserted, then an update of a frozen column, a delete, a bad status transition and a truncate
--      must each be REFUSED while a legal transition passes; if any is not refused the migration fails and rolls back.
--
-- PRIVILEGE (determined, not assumed; mirrored-role test in tests, evidence in the PR)
--   This file creates a function in schema public. The routine migration role amjis_app has USAGE but NOT CREATE
--   on schema public (owner data_plane_schema_owner), so run by the ROUTINE runner it fails at the first
--   CREATE FUNCTION with "permission denied for schema public" (CREATE OR REPLACE FUNCTION of an EXISTING function
--   needs schema CREATE too). amjis_app owns mimamsa_predictions and the existing function, so inside a window that
--   grants it CREATE on public temporarily everything else succeeds and the new function/triggers end up owned by
--   amjis_app, like the captured one. The sanctioned path is the protected public-schema window
--   (deploy.yml jataka-protected-migrations: scripts/jataka-schema-capability.ts grant -> migrate.ts --only
--   1265_l5_predictions_frozen_row_guard.sql -> revoke), which needs 1265 added to PROTECTED_PUBLIC_SCHEMA_MIGRATIONS
--   in scripts/migrate.ts and an exact-set input/step in deploy.yml. THAT WIRING IS NOT IN THIS PR: until it exists
--   the file must not reach main (the routine runner would fail the migrate job on it). The file starts with an
--   explicit gate that states the missing privilege. Fallback: a D6-style owner-role executor (postgres admin,
--   transient GRANT of amjis_app and CREATE) running the same file.
--
-- ORDER (hard preconditions)
--   a. The mi_bhavisya writer must stop deleting pending/due rows (mi_bhavisya.py:230) and the cockpit clear spec
--      (assetClearSpec.ts:149) must stop deleting them, in their own PRs; otherwise the next rebuild or clear
--      FAILS (loudly, rolled back, nothing lost) on this guard. That failure is the intended safety, not a bug.
--   b. data_plane_builder: its pending/due DELETE (allowed by mimamsa_predictions_builder_guard) is now refused too.
--   c. RLS is NOT armed here (see RLS).
--
-- RLS (assessed, NOT done here)
--   The g1c policies of migration 576 exist live (pg_policy) but RLS is off (relrowsecurity false). They cover only
--   role_web_serve/role_sidecar (chart-pinned through a client-settable GUC) and role_orchestrator/
--   role_ledger_write/role_jobs (USING true). Arming now would hide every row from data_plane_builder,
--   suvarna_reader, retrieval_census_ro and nirmana_evidence_ingress_writer (no policy for them) and would not bind
--   the owner. Arming is a separate step after policies for those roles exist. Immutability here does not depend
--   on RLS.
--
-- SERVING EFFECT AT APPLY: none expected. No asset_registry column is touched (nirmana_registry_receipt_invalidation
-- does not fire), no row is written or kept (the self-test probe is rolled back), no grant or ACL of any table
-- changes, no column/index/constraint changes. Behaviour after apply: UPDATE/DELETE/TRUNCATE that the guard refuses
-- raise SQLSTATE 42501 with a message starting "mimamsa_predictions_frozen_row_guard:".
--
-- NOT DONE HERE: arming RLS; the mi_bhavisya / assetClearSpec writer changes; the wiring for the protected window;
-- guards on mimamsa_calibration_snapshot / brahma_* ledgers (they already carry their own freeze triggers, or none:
-- listed in the PR); the schema pin baseline; any rebuild.
--
-- ROLLBACK: DROP TRIGGER mimamsa_predictions_frozen_row_guard_truncate ON public.mimamsa_predictions;
--   DROP TRIGGER mimamsa_predictions_frozen_row_guard ON public.mimamsa_predictions;
--   DROP FUNCTION public.mimamsa_predictions_frozen_row_guard();  (the captured builder guard stays)
--
-- VERIFICATION BY PRODUCTION STRUCTURE after apply (Trap 103):
--   SELECT tgname, tgenabled FROM pg_trigger WHERE tgrelid = 'public.mimamsa_predictions'::regclass AND NOT tgisinternal;
--     -- mimamsa_predictions_builder_guard O ; mimamsa_predictions_frozen_row_guard A ; ..._truncate A
--   SELECT md5(prosrc) FROM pg_proc WHERE proname = 'mimamsa_predictions_frozen_row_guard';  -- 70dcc9d662869bad9c535968100ab0ed
--   SELECT md5(prosrc) FROM pg_proc WHERE proname = 'mimamsa_predictions_builder_guard';     -- 46c23854275c2712b30860a2b174adb2

SET LOCAL lock_timeout = '5s';

-- 0. GATE: say exactly what is missing instead of failing inside the first statement.
DO $gate$
DECLARE
  missing text[] := ARRAY[]::text[];
  rel_owner oid;
  col text;
BEGIN
  IF to_regclass('public.mimamsa_predictions') IS NULL THEN
    RAISE EXCEPTION '1265: public.mimamsa_predictions does not exist';
  END IF;
  SELECT c.relowner INTO rel_owner FROM pg_class c WHERE c.oid = 'public.mimamsa_predictions'::regclass;
  IF NOT pg_has_role(current_user, rel_owner, 'MEMBER') THEN
    missing := missing || format('current_user %s is not a member of the table owner %s (ALTER TABLE ... ENABLE ALWAYS TRIGGER needs ownership)',
                                 current_user, pg_get_userbyid(rel_owner));
  END IF;
  IF NOT has_schema_privilege(current_user, 'public', 'CREATE') THEN
    missing := missing || format('current_user %s has no CREATE on schema public (this migration creates a function there; run it only inside the protected public-schema window, never the routine runner)',
                                 current_user);
  END IF;
  IF array_length(missing, 1) > 0 THEN
    RAISE EXCEPTION '1265: missing privilege: %', array_to_string(missing, '; ');
  END IF;
  FOREACH col IN ARRAY ARRAY['chart_id','prediction_id','source_pramana_id','outcome_claim','domain','observation_window',
      'eval_date','confidence_band','magnitude_expected','falsifier_jsonb','base_rate','emitted_at','lifecycle_status',
      'driving_signals','frozen_bundle_hash','bundle_formula_version','created_at','contact_id',
      'chart_context_stale_at','chart_context_stale_reason','chart_context_superseded_by_run_id'] LOOP
    IF NOT EXISTS (SELECT 1 FROM pg_attribute WHERE attrelid = 'public.mimamsa_predictions'::regclass
                    AND attname = col AND attnum > 0 AND NOT attisdropped) THEN
      RAISE EXCEPTION '1265: public.mimamsa_predictions has no column % (the guard was written against the 21-column table)', col;
    END IF;
  END LOOP;
END
$gate$;

-- 1a. CAPTURE guard: refuse to overwrite a live function that is not the captured one.
DO $capture_guard$
DECLARE
  f record;
BEGIN
  SELECT p.oid, md5(p.prosrc) AS body_md5, length(convert_to(p.prosrc, 'UTF8')) AS body_len, p.prosecdef,
         p.provolatile, p.proconfig::text AS cfg, p.prolang = (SELECT oid FROM pg_language WHERE lanname = 'plpgsql') AS is_plpgsql,
         p.prorettype = 'trigger'::regtype AS ret_trigger, p.pronargs, p.proisstrict, p.proleakproof, p.prokind
    INTO f
    FROM pg_proc p WHERE p.oid = to_regprocedure('public.mimamsa_predictions_builder_guard()');
  IF FOUND THEN
    IF f.body_md5 <> '46c23854275c2712b30860a2b174adb2' OR f.body_len <> 1084 THEN
      RAISE EXCEPTION '1265: live public.mimamsa_predictions_builder_guard() body is md5 % / % bytes, not the captured 46c23854275c2712b30860a2b174adb2 / 1084; refusing to overwrite it. Diff the live body, then update this migration deliberately.',
        f.body_md5, f.body_len;
    END IF;
    IF f.prosecdef OR f.provolatile <> 'v' OR f.cfg IS DISTINCT FROM '{"search_path=pg_catalog, pg_temp"}'
       OR NOT f.is_plpgsql OR NOT f.ret_trigger OR f.pronargs <> 0 OR f.proisstrict OR f.proleakproof OR f.prokind <> 'f' THEN
      RAISE EXCEPTION '1265: live public.mimamsa_predictions_builder_guard() has the captured body but other attributes (security definer / volatility / proconfig / language) differ from the capture; refusing to overwrite.';
    END IF;
  END IF;
END
$capture_guard$;

-- 1b. The captured function, byte for byte (body between the dollar quotes starts with a newline and ends with one).
CREATE OR REPLACE FUNCTION public.mimamsa_predictions_builder_guard()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY INVOKER
 SET search_path = pg_catalog, pg_temp
AS $guard$
BEGIN
  IF current_user = 'data_plane_builder' OR session_user = 'data_plane_builder' THEN
    IF TG_OP = 'INSERT' THEN
      IF NEW.lifecycle_status IS NULL OR NEW.lifecycle_status NOT IN ('pending', 'due') THEN
        RAISE EXCEPTION 'mimamsa_predictions_builder_guard: data_plane_builder may insert only pending/due (regenerable) predictions; refusing chart_id=%, prediction_id=%, lifecycle_status=%',
          NEW.chart_id, NEW.prediction_id, COALESCE(NEW.lifecycle_status, '<NULL>')
          USING ERRCODE = '42501';
      END IF;
    ELSIF TG_OP = 'DELETE' THEN
      IF OLD.lifecycle_status IS NULL OR OLD.lifecycle_status NOT IN ('pending', 'due') THEN
        RAISE EXCEPTION 'mimamsa_predictions_builder_guard: data_plane_builder may delete only pending/due (regenerable) predictions; refusing chart_id=%, prediction_id=%, lifecycle_status=%',
          OLD.chart_id, OLD.prediction_id, COALESCE(OLD.lifecycle_status, '<NULL>')
          USING ERRCODE = '42501';
      END IF;
    END IF;
  END IF;
  IF TG_OP = 'DELETE' THEN
    RETURN OLD;
  END IF;
  RETURN NEW;
END
$guard$;

REVOKE ALL ON FUNCTION public.mimamsa_predictions_builder_guard() FROM PUBLIC;

-- 1c. The captured trigger: create when absent, otherwise it must have exactly the captured shape.
DO $capture_trigger$
DECLARE
  t record;
BEGIN
  SELECT tgtype, tgfoid, tgenabled, tgnargs, tgisinternal, tgconstraint
    INTO t
    FROM pg_trigger
   WHERE tgrelid = 'public.mimamsa_predictions'::regclass AND tgname = 'mimamsa_predictions_builder_guard';
  IF NOT FOUND THEN
    CREATE TRIGGER mimamsa_predictions_builder_guard
      BEFORE INSERT OR DELETE ON public.mimamsa_predictions
      FOR EACH ROW EXECUTE FUNCTION public.mimamsa_predictions_builder_guard();
  ELSIF t.tgtype <> 15 OR t.tgfoid <> 'public.mimamsa_predictions_builder_guard()'::regprocedure OR t.tgenabled <> 'O'
        OR t.tgnargs <> 0 OR t.tgisinternal OR t.tgconstraint <> 0 THEN
    RAISE EXCEPTION '1265: live trigger mimamsa_predictions_builder_guard is not the captured one (tgtype %, enabled %); refusing to continue',
      t.tgtype, t.tgenabled;
  END IF;
END
$capture_trigger$;

-- 2a. The new guard function: refuse to overwrite a different live body of the same name.
DO $frozen_check$
DECLARE
  live_md5 text;
BEGIN
  SELECT md5(p.prosrc) INTO live_md5 FROM pg_proc p
   WHERE p.oid = to_regprocedure('public.mimamsa_predictions_frozen_row_guard()');
  IF live_md5 IS NOT NULL AND live_md5 <> '70dcc9d662869bad9c535968100ab0ed' THEN
    RAISE EXCEPTION '1265: live public.mimamsa_predictions_frozen_row_guard() has body md5 %, not this migration''s 70dcc9d662869bad9c535968100ab0ed; refusing to overwrite a changed live guard',
      live_md5;
  END IF;
END
$frozen_check$;

CREATE OR REPLACE FUNCTION public.mimamsa_predictions_frozen_row_guard()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY INVOKER
 SET search_path = pg_catalog, pg_temp
AS $frozen$
DECLARE
  c_mutable    CONSTANT text[] := ARRAY['lifecycle_status', 'chart_context_stale_at',
                                        'chart_context_stale_reason', 'chart_context_superseded_by_run_id'];
  v_old        jsonb;
  v_new        jsonb;
  v_changed    text[];
  v_authorized boolean := false;
BEGIN
  IF TG_OP = 'TRUNCATE' THEN
    RAISE EXCEPTION 'mimamsa_predictions_frozen_row_guard: TRUNCATE of public.mimamsa_predictions is refused; its rows are frozen predictions. A subject-withdrawal erasure deletes row by row under the consent gate.'
      USING ERRCODE = '42501';
  END IF;

  IF TG_OP = 'UPDATE' THEN
    -- Fail closed: everything that is not on the allow-list is frozen, including any column added later.
    v_old := to_jsonb(OLD) - c_mutable;
    v_new := to_jsonb(NEW) - c_mutable;
    IF v_new IS DISTINCT FROM v_old THEN
      SELECT array_agg(k ORDER BY k) INTO v_changed
        FROM jsonb_object_keys(v_old || v_new) AS k
       WHERE (v_old -> k) IS DISTINCT FROM (v_new -> k);
      RAISE EXCEPTION 'mimamsa_predictions_frozen_row_guard: frozen column(s) % cannot be updated; refusing chart_id=%, prediction_id=%',
        array_to_string(v_changed, ', '), OLD.chart_id, OLD.prediction_id
        USING ERRCODE = '42501';
    END IF;

    IF NEW.lifecycle_status IS DISTINCT FROM OLD.lifecycle_status THEN
      IF NOT COALESCE(
           (OLD.lifecycle_status = 'pending' AND NEW.lifecycle_status IN ('due', 'confirmed', 'denied', 'partial', 'expired'))
        OR (OLD.lifecycle_status = 'due'     AND NEW.lifecycle_status IN ('confirmed', 'denied', 'partial', 'expired')),
           false)
      THEN
        RAISE EXCEPTION 'mimamsa_predictions_frozen_row_guard: lifecycle_status transition % -> % is not allowed (only pending -> due/confirmed/denied/partial/expired and due -> confirmed/denied/partial/expired); refusing chart_id=%, prediction_id=%',
          COALESCE(OLD.lifecycle_status, '<NULL>'), COALESCE(NEW.lifecycle_status, '<NULL>'), OLD.chart_id, OLD.prediction_id
          USING ERRCODE = '42501';
      END IF;
    END IF;

    -- The staleness marker is additive and set once; the run link may later be cleared (FK ON DELETE SET NULL).
    IF OLD.chart_context_stale_at IS NOT NULL
       AND (NEW.chart_context_stale_at IS DISTINCT FROM OLD.chart_context_stale_at
            OR NEW.chart_context_stale_reason IS DISTINCT FROM OLD.chart_context_stale_reason) THEN
      RAISE EXCEPTION 'mimamsa_predictions_frozen_row_guard: the chart-context staleness marker is set once and cannot be changed or cleared; refusing chart_id=%, prediction_id=%',
        OLD.chart_id, OLD.prediction_id
        USING ERRCODE = '42501';
    END IF;
    IF NEW.chart_context_superseded_by_run_id IS DISTINCT FROM OLD.chart_context_superseded_by_run_id
       AND NEW.chart_context_superseded_by_run_id IS NOT NULL
       AND (OLD.chart_context_stale_at IS NOT NULL OR NEW.chart_context_stale_at IS NULL) THEN
      RAISE EXCEPTION 'mimamsa_predictions_frozen_row_guard: chart_context_superseded_by_run_id can be set only together with the staleness marker; refusing chart_id=%, prediction_id=%',
        OLD.chart_id, OLD.prediction_id
        USING ERRCODE = '42501';
    END IF;
    RETURN NEW;
  END IF;

  -- DELETE. The one exception: the chart's subject has withdrawn consent and no deletion dispute is open.
  -- The withdrawal sweep (platform/src/lib/pariprashna/consent/withdrawal.ts) records the withdrawn state and a
  -- hash-chained consent event first and writes a tombstone (row count, content hash) per table after.
  IF to_regclass('public.chart_subject_consent') IS NOT NULL
     AND to_regclass('public.chart_subject_deletion_disputes') IS NOT NULL THEN
    BEGIN
      SELECT EXISTS (SELECT 1 FROM public.chart_subject_consent c
                      WHERE c.chart_id = OLD.chart_id AND c.consent_state = 'withdrawn')
         AND NOT EXISTS (SELECT 1 FROM public.chart_subject_deletion_disputes d
                          WHERE d.chart_id = OLD.chart_id AND d.status IN ('open', 'reopened', 'escalated'))
        INTO v_authorized;
    EXCEPTION WHEN insufficient_privilege THEN
      v_authorized := false;
    END;
    IF v_authorized THEN
      RAISE LOG 'mimamsa_predictions_frozen_row_guard: DELETE authorized by subject withdrawal (consent withdrawn, no open dispute); chart_id=%, prediction_id=%, user=%',
        OLD.chart_id, OLD.prediction_id, session_user;
      RETURN OLD;
    END IF;
  END IF;

  RAISE EXCEPTION 'mimamsa_predictions_frozen_row_guard: frozen predictions cannot be deleted (a rebuild must not remove or replace them); refusing chart_id=%, prediction_id=%, lifecycle_status=%',
    OLD.chart_id, OLD.prediction_id, COALESCE(OLD.lifecycle_status, '<NULL>')
    USING ERRCODE = '42501';
END
$frozen$;

REVOKE ALL ON FUNCTION public.mimamsa_predictions_frozen_row_guard() FROM PUBLIC;

COMMENT ON FUNCTION public.mimamsa_predictions_frozen_row_guard() IS
  'N-104 / migration 1265: every mimamsa_predictions row is a frozen prediction. UPDATE allows only lifecycle_status (pending->due/confirmed/denied/partial/expired, due->confirmed/denied/partial/expired) and the set-once chart-context staleness marker; DELETE is refused except after a recorded subject withdrawal with no open dispute; TRUNCATE is refused. Applies to every role.';

-- 2b. Triggers (create when absent; a present one must have the expected shape). ENABLE ALWAYS so that
--     session_replication_role = replica does not bypass them.
DO $frozen_triggers$
DECLARE
  t record;
BEGIN
  SELECT tgtype, tgfoid, tgisinternal INTO t FROM pg_trigger
   WHERE tgrelid = 'public.mimamsa_predictions'::regclass AND tgname = 'mimamsa_predictions_frozen_row_guard';
  IF NOT FOUND THEN
    CREATE TRIGGER mimamsa_predictions_frozen_row_guard
      BEFORE UPDATE OR DELETE ON public.mimamsa_predictions
      FOR EACH ROW EXECUTE FUNCTION public.mimamsa_predictions_frozen_row_guard();
  ELSIF t.tgtype <> 27 OR t.tgfoid <> 'public.mimamsa_predictions_frozen_row_guard()'::regprocedure OR t.tgisinternal THEN
    RAISE EXCEPTION '1265: existing trigger mimamsa_predictions_frozen_row_guard has another shape (tgtype %); refusing', t.tgtype;
  END IF;

  SELECT tgtype, tgfoid, tgisinternal INTO t FROM pg_trigger
   WHERE tgrelid = 'public.mimamsa_predictions'::regclass AND tgname = 'mimamsa_predictions_frozen_row_guard_truncate';
  IF NOT FOUND THEN
    CREATE TRIGGER mimamsa_predictions_frozen_row_guard_truncate
      BEFORE TRUNCATE ON public.mimamsa_predictions
      FOR EACH STATEMENT EXECUTE FUNCTION public.mimamsa_predictions_frozen_row_guard();
  ELSIF t.tgtype <> 34 OR t.tgfoid <> 'public.mimamsa_predictions_frozen_row_guard()'::regprocedure OR t.tgisinternal THEN
    RAISE EXCEPTION '1265: existing trigger mimamsa_predictions_frozen_row_guard_truncate has another shape (tgtype %); refusing', t.tgtype;
  END IF;
END
$frozen_triggers$;

ALTER TABLE public.mimamsa_predictions ENABLE ALWAYS TRIGGER mimamsa_predictions_frozen_row_guard;
ALTER TABLE public.mimamsa_predictions ENABLE ALWAYS TRIGGER mimamsa_predictions_frozen_row_guard_truncate;

-- 3. SELF-TEST: the guard must refuse what it claims to refuse, and for ITS reason (message prefix), not because the
--    invoker lacked a privilege. Everything inside is rolled back by the final sentinel exception (the probe row never
--    survives); any unrefused or wrongly refused action fails the migration.
DO $selftest$
DECLARE
  probe_chart CONSTANT uuid := gen_random_uuid();
  failures text[] := ARRAY[]::text[];
  msg text;
BEGIN
  BEGIN
    INSERT INTO public.mimamsa_predictions
      (chart_id, prediction_id, source_pramana_id, outcome_claim, domain, observation_window, eval_date,
       confidence_band, magnitude_expected, falsifier_jsonb, emitted_at, lifecycle_status, driving_signals,
       frozen_bundle_hash, bundle_formula_version)
    VALUES (probe_chart, 'm1265_probe', 'm1265_probe_src', 'm1265 probe', 'm1265', daterange(current_date, current_date + 1), current_date,
            numrange(0.1, 0.9), 'm1265', '{}'::jsonb, now(), 'pending', '[]'::jsonb, 'm1265', 'm1265');

    BEGIN
      UPDATE public.mimamsa_predictions SET source_pramana_id = 'changed' WHERE chart_id = probe_chart;
      failures := array_append(failures, 'UPDATE of a frozen column on a pending row was not refused'::text);
    EXCEPTION WHEN insufficient_privilege THEN
      GET STACKED DIAGNOSTICS msg = MESSAGE_TEXT;
      IF msg NOT LIKE 'mimamsa_predictions_frozen_row_guard:%' THEN failures := array_append(failures, format('frozen-column UPDATE refused by something else: %s', msg)); END IF;
    END;
    BEGIN
      UPDATE public.mimamsa_predictions SET lifecycle_status = 'bogus' WHERE chart_id = probe_chart;
      failures := array_append(failures, 'UPDATE to an unknown lifecycle_status was not refused'::text);
    EXCEPTION WHEN insufficient_privilege THEN
      GET STACKED DIAGNOSTICS msg = MESSAGE_TEXT;
      IF msg NOT LIKE 'mimamsa_predictions_frozen_row_guard:%' THEN failures := array_append(failures, format('bad-status UPDATE refused by something else: %s', msg)); END IF;
    END;
    BEGIN
      DELETE FROM public.mimamsa_predictions WHERE chart_id = probe_chart;
      failures := array_append(failures, 'DELETE of a pending row was not refused'::text);
    EXCEPTION WHEN insufficient_privilege THEN
      GET STACKED DIAGNOSTICS msg = MESSAGE_TEXT;
      IF msg NOT LIKE 'mimamsa_predictions_frozen_row_guard:%' THEN failures := array_append(failures, format('DELETE refused by something else: %s', msg)); END IF;
    END;
    IF has_table_privilege(current_user, 'public.mimamsa_predictions', 'TRUNCATE') THEN
      BEGIN
        TRUNCATE public.mimamsa_predictions;
        failures := array_append(failures, 'TRUNCATE was not refused'::text);
      EXCEPTION WHEN insufficient_privilege THEN
        GET STACKED DIAGNOSTICS msg = MESSAGE_TEXT;
        IF msg NOT LIKE 'mimamsa_predictions_frozen_row_guard:%' THEN failures := array_append(failures, format('TRUNCATE refused by something else: %s', msg)); END IF;
      END;
    ELSE
      RAISE NOTICE '1265 self-test: TRUNCATE branch skipped, % holds no TRUNCATE privilege on mimamsa_predictions (the mirrored-role tests cover it)', current_user;
    END IF;

    BEGIN
      UPDATE public.mimamsa_predictions SET lifecycle_status = 'confirmed' WHERE chart_id = probe_chart;
    EXCEPTION WHEN OTHERS THEN
      failures := array_append(failures, 'the legal transition pending -> confirmed was refused'::text);
    END;
    BEGIN
      UPDATE public.mimamsa_predictions SET lifecycle_status = 'pending' WHERE chart_id = probe_chart;
      failures := array_append(failures, 'UPDATE of a terminal status (confirmed -> pending) was not refused'::text);
    EXCEPTION WHEN insufficient_privilege THEN
      GET STACKED DIAGNOSTICS msg = MESSAGE_TEXT;
      IF msg NOT LIKE 'mimamsa_predictions_frozen_row_guard:%' THEN failures := array_append(failures, format('terminal-status UPDATE refused by something else: %s', msg)); END IF;
    END;
    BEGIN
      UPDATE public.mimamsa_predictions SET outcome_claim = 'changed' WHERE chart_id = probe_chart;
      failures := array_append(failures, 'UPDATE of a frozen column on a terminal row was not refused'::text);
    EXCEPTION WHEN insufficient_privilege THEN
      GET STACKED DIAGNOSTICS msg = MESSAGE_TEXT;
      IF msg NOT LIKE 'mimamsa_predictions_frozen_row_guard:%' THEN failures := array_append(failures, format('terminal-row UPDATE refused by something else: %s', msg)); END IF;
    END;
    BEGIN
      UPDATE public.mimamsa_predictions SET chart_context_stale_at = now(), chart_context_stale_reason = 'chart_details_changed'
       WHERE chart_id = probe_chart;
    EXCEPTION WHEN OTHERS THEN
      failures := array_append(failures, 'the legal staleness marking was refused'::text);
    END;

    IF array_length(failures, 1) > 0 THEN
      RAISE EXCEPTION '1265 self-test FAILED: %', array_to_string(failures, '; ');
    END IF;
    RAISE EXCEPTION '1265_selftest_ok' USING ERRCODE = 'P0001';
  EXCEPTION WHEN raise_exception THEN
    IF SQLERRM <> '1265_selftest_ok' THEN
      RAISE;
    END IF;
  END;
END
$selftest$;

-- 4. POST-CHECK: the final catalog state is exactly what this migration describes.
DO $post$
BEGIN
  IF (SELECT md5(prosrc) FROM pg_proc WHERE oid = 'public.mimamsa_predictions_builder_guard()'::regprocedure) <> '46c23854275c2712b30860a2b174adb2' THEN
    RAISE EXCEPTION '1265 post-check: builder guard body is not the captured one';
  END IF;
  IF (SELECT md5(prosrc) FROM pg_proc WHERE oid = 'public.mimamsa_predictions_frozen_row_guard()'::regprocedure) <> '70dcc9d662869bad9c535968100ab0ed' THEN
    RAISE EXCEPTION '1265 post-check: frozen row guard body is not this migration''s';
  END IF;
  IF (SELECT count(*) FROM pg_trigger WHERE tgrelid = 'public.mimamsa_predictions'::regclass AND NOT tgisinternal
         AND ((tgname = 'mimamsa_predictions_builder_guard' AND tgenabled = 'O')
           OR (tgname = 'mimamsa_predictions_frozen_row_guard' AND tgenabled = 'A')
           OR (tgname = 'mimamsa_predictions_frozen_row_guard_truncate' AND tgenabled = 'A'))) <> 3 THEN
    RAISE EXCEPTION '1265 post-check: the three triggers are not all present with the expected enablement';
  END IF;
  IF EXISTS (SELECT 1 FROM pg_proc WHERE oid IN ('public.mimamsa_predictions_builder_guard()'::regprocedure,
                                                 'public.mimamsa_predictions_frozen_row_guard()'::regprocedure)
                AND (prosecdef OR has_function_privilege('public', oid, 'EXECUTE'))) THEN
    RAISE EXCEPTION '1265 post-check: a guard function is SECURITY DEFINER or executable by PUBLIC';
  END IF;
END
$post$;
