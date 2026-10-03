-- 1265: L5 frozen-history guards -- OWNER-PATH SQL, NOT A MIGRATION. It lives in this executor package and must never be
-- placed under platform/migrations or platform/supabase/migrations (migrate.ts would pick it up and the routine runner,
-- which cannot CREATE in schema public, would fail the migrate job and block every deploy). The number 1265 is history only.
-- Run ONLY by l5_frozen_guard_exec.py (GATE_V2, plan hash, dry run then apply) as role amjis_app inside the executor's
-- transaction, after the executor has transiently granted amjis_app CREATE on schema public (and revokes it before COMMIT).
-- SS rulings N-104 and N-107 (HELD; applied after S-L1, before any L5 rebuild; after the append-only mi_bhavisya writer and
-- the assetClearSpec change are deployed).
--
-- WHAT IT DOES (one transaction, schema code only: no row of any table is written or kept)
--   A. CAPTURE the live-only trigger function public.mimamsa_predictions_builder_guard() and its trigger, byte for byte (body
--      md5 46c23854275c2712b30860a2b174adb2, 1084 bytes; read as suvarna_reader on production 2026-10-03, PostgreSQL 15.18; owner
--      amjis_app, proacl {amjis_app=X/amjis_app}, proconfig {search_path=pg_catalog, pg_temp}; trigger BEFORE INSERT OR DELETE
--      FOR EACH ROW, tgtype 15, enabled 'O'). Text identical, md5 for md5, to Part A2 of BUILDER_GRANT_PLAN v1.3 (docs-only
--      draft on branch suvarna/land/grant-plan-001, 2026-10-01); applied out of band, date not recorded. MD5 GUARD: a live
--      function of that name with another body or other attributes, or a trigger of another shape, makes this file REFUSE;
--      absent (a fresh replay) it is created; equal it is a no-op replace.
--   B. ASSERT-AND-RECORD the live-only builder grants: data_plane_builder holds exactly SELECT, INSERT, DELETE ('ard',
--      grantor amjis_app) on public.mimamsa_predictions and public.mimamsa_manifestation_sets (BUILDER_GRANT_PLAN, applied out
--      of band). No-op if present; RAISES if absent or different. This file never issues a GRANT. Also asserts that the repo
--      objects it builds beside are the repo's: bmpl_freeze_confirmed (md5 70c2ddb261d703fa6a33a4feaf39c99c) and its trigger,
--      brahma_prospective_ledger_enforce_shape (md5 acc7ec0121fa1fe0752ae938d9edfafe) and its trigger.
--   C. GUARDS (every role, owners and superusers included; ENABLE ALWAYS so session_replication_role = replica does not
--      bypass; SECURITY INVOKER; pinned search_path; no PUBLIC execute on a trigger function). TRUNCATE is refused on all four.
--      DELETE is refused on all four EXCEPT through TWO data-driven exceptions (SS N-107 and N-108). (i) the cascade of deleting the CHART
--      itself (charts(id) ON DELETE CASCADE, migration 1275): public.l5_frozen_chart_cascade_authorizes(chart) = no charts row with that id
--      (inside the RI cascade the parent is already deleted; SECURITY DEFINER because charts has RLS on; section C1b), checked BEFORE the consent sweep, public.l5_frozen_withdrawal_authorizes(chart):
--      the chart's subject has chart_subject_consent.consent_state = 'withdrawn' AND no chart_subject_deletion_disputes row in
--      open/reopened/escalated; that is exactly the condition of the consent sweep (consent/withdrawal.ts), which deletes
--      chart_id = $1 from every subject-scoped table (all four are) and leaves its own hash-chained event and per-table
--      tombstone; each authorized row delete also writes a RAISE LOG line. Fail closed if the consent tables are absent or the
--      invoker cannot read them. No setting, role name or session test opens anything. Break-glass is a reviewed owner-path
--      plan that DISABLEs a trigger inside its own transaction with a before/after digest; the table owner and a superuser CAN
--      disable a trigger (PostgreSQL cannot prevent it): the signature is tgenabled <> 'A'.
--      1. mimamsa_predictions (frozen = every row, pending included: all 195 live rows are pending): UPDATE allow-list
--         lifecycle_status (pending -> due/confirmed/denied/partial/expired; due -> confirmed/denied/partial/expired; a terminal
--         status never changes), chart_context_stale_at/_reason (set once, never changed or cleared),
--         chart_context_superseded_by_run_id (with the marker; afterwards only to NULL: FK ON DELETE SET NULL); all other
--         columns frozen, fail closed (to_jsonb(row) minus the allow-list), incl. source_pramana_id (migration 680's column).
--      2. brahma_prospective_ledger (filed standing predictions; writers: prospective_ledger.ts INSERT at filing, UPDATE
--         open -> matched with matched_event_id/matched_at/match_note at :828, the staleness marker): allow-list
--         lifecycle_status (open -> matched/lapsed_unobserved/withdrawn; matched -> confirmed/falsified/withdrawn; the other
--         four statuses terminal), the match record (only by open -> matched, always complete), the staleness trio (as above).
--         All else frozen: claim, falsifier, confidence, window, model, provenance, contact_id.
--      3. mimamsa_manifestation_sets (the freeze-id citations; mi_bhavisya writes INSERT only, no UPDATE exists anywhere): NO
--         column is mutable. A rebuild must never delete or rewrite them.
--      4. brahma_mimamsa_prediction_ledger: DELETE and TRUNCATE guard added beside its existing UPDATE-only trigger
--         trg_bmpl_freeze_confirmed, which is NOT touched (its UPDATE gaps are listed in the PR, not changed here).
--      NOT guarded by ruling: mimamsa_calibration and mimamsa_calibration_snapshot (computed and rebuildable).
--   D. SELF-TEST per table (rolled-back probe rows; the guard's own message is required, so a missing privilege cannot pass
--      for a refusal) and an asserting POST-CHECK that RAISES. The executor adds its own catalog accounting.
--
-- STANDING CONSTRAINT (SS): no FORCE ROW LEVEL SECURITY on public.charts without first revisiting the chart-deletion discriminator above (it relies on
-- a SECURITY DEFINER owner that bypasses row security on charts). Machine-checked: this file's gate and post-check RAISE if relforcerowsecurity is true on
-- public.charts, the discriminator RAISES at run time if it ever becomes true, the executor refuses (pre and post), and sql/verify_charts_rls_constraint.sql
-- reports it (run it in every dry run and W-step read-back).
--
-- ORDER: after S-L1 and after the append-only mi_bhavisya writer + assetClearSpec change are deployed (the executor checks the
-- commit named by --writer-commit). Once applied, the old pending/due DELETE of mi_bhavisya.py:230 and assetClearSpec.ts:149
-- fail loudly. RLS is NOT armed (recorded in the PR: unsound for the live role set). Rollback: the ROLLBACK sql of this
-- package (drops the 8 new triggers and 6 new functions; the captured builder guard stays).

SET LOCAL lock_timeout = '5s';

-- 0. GATE: say exactly what is missing instead of failing inside the first statement.
DO $gate$
DECLARE
  missing text[] := ARRAY[]::text[];
  rel_owner oid;
  t text;
  col text;
BEGIN
  FOREACH t IN ARRAY ARRAY['mimamsa_predictions', 'brahma_prospective_ledger', 'mimamsa_manifestation_sets', 'brahma_mimamsa_prediction_ledger'] LOOP
    IF to_regclass('public.' || t) IS NULL THEN
      RAISE EXCEPTION '1265: public.% does not exist', t;
    END IF;
    SELECT c.relowner INTO rel_owner FROM pg_class c WHERE c.oid = ('public.' || t)::regclass;
    IF NOT pg_has_role(current_user, rel_owner, 'MEMBER') THEN
      missing := missing || format('current_user %s is not a member of the owner %s of public.%s (CREATE TRIGGER / ENABLE ALWAYS TRIGGER need ownership)',
                                   current_user, pg_get_userbyid(rel_owner), t);
    END IF;
  END LOOP;
  IF to_regclass('public.charts') IS NOT NULL AND (SELECT relforcerowsecurity FROM pg_class WHERE oid = 'public.charts'::regclass) THEN
    RAISE EXCEPTION '1265: STANDING CONSTRAINT violated: FORCE ROW LEVEL SECURITY is set on public.charts. The chart-deletion discriminator (l5_frozen_chart_cascade_authorizes, SECURITY DEFINER) is unsafe under it; revisit the 1265 guard before keeping FORCE on charts.';
  END IF;
  IF NOT has_schema_privilege(current_user, 'public', 'CREATE') THEN
    missing := missing || format('current_user %s has no CREATE on schema public (this file creates functions there; run it only through l5_frozen_guard_exec.py, which grants and revokes the capability inside its transaction)',
                                 current_user);
  END IF;
  IF array_length(missing, 1) > 0 THEN
    RAISE EXCEPTION '1265: missing privilege: %', array_to_string(missing, '; ');
  END IF;
  FOREACH col IN ARRAY ARRAY['mimamsa_predictions.chart_id','mimamsa_predictions.prediction_id','mimamsa_predictions.source_pramana_id',
      'mimamsa_predictions.outcome_claim','mimamsa_predictions.domain','mimamsa_predictions.observation_window','mimamsa_predictions.eval_date',
      'mimamsa_predictions.confidence_band','mimamsa_predictions.magnitude_expected','mimamsa_predictions.falsifier_jsonb',
      'mimamsa_predictions.base_rate','mimamsa_predictions.emitted_at','mimamsa_predictions.lifecycle_status','mimamsa_predictions.driving_signals',
      'mimamsa_predictions.frozen_bundle_hash','mimamsa_predictions.bundle_formula_version','mimamsa_predictions.created_at','mimamsa_predictions.contact_id',
      'mimamsa_predictions.chart_context_stale_at','mimamsa_predictions.chart_context_stale_reason','mimamsa_predictions.chart_context_superseded_by_run_id',
      'brahma_prospective_ledger.prediction_id','brahma_prospective_ledger.chart_id','brahma_prospective_ledger.claim','brahma_prospective_ledger.event_class',
      'brahma_prospective_ledger.claim_shape','brahma_prospective_ledger.observation_window','brahma_prospective_ledger.milestone_set',
      'brahma_prospective_ledger.lifecycle_status','brahma_prospective_ledger.matched_event_id','brahma_prospective_ledger.matched_at',
      'brahma_prospective_ledger.match_note','brahma_prospective_ledger.chart_context_stale_at','brahma_prospective_ledger.chart_context_stale_reason',
      'brahma_prospective_ledger.chart_context_superseded_by_run_id',
      'mimamsa_manifestation_sets.chart_id','mimamsa_manifestation_sets.prediction_id','mimamsa_manifestation_sets.channel_id',
      'mimamsa_manifestation_sets.domain','mimamsa_manifestation_sets.source','mimamsa_manifestation_sets.citation_ref',
      'mimamsa_manifestation_sets.is_literal','mimamsa_manifestation_sets.frozen_at',
      'brahma_mimamsa_prediction_ledger.id','brahma_mimamsa_prediction_ledger.chart_id','brahma_mimamsa_prediction_ledger.lifecycle_status'] LOOP
    IF NOT EXISTS (SELECT 1 FROM pg_attribute WHERE attrelid = ('public.' || split_part(col, '.', 1))::regclass
                    AND attname = split_part(col, '.', 2) AND attnum > 0 AND NOT attisdropped) THEN
      RAISE EXCEPTION '1265: public.% has no column % (the guards were written against the live columns read 2026-10-03)',
        split_part(col, '.', 1), split_part(col, '.', 2);
    END IF;
  END LOOP;
END
$gate$;

-- A1. CAPTURE guard: refuse to overwrite a live function that is not the captured one.
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
      RAISE EXCEPTION '1265: live public.mimamsa_predictions_builder_guard() body is md5 % / % bytes, not the captured 46c23854275c2712b30860a2b174adb2 / 1084; refusing to overwrite it. Diff the live body, then update this file deliberately.',
        f.body_md5, f.body_len;
    END IF;
    IF f.prosecdef OR f.provolatile <> 'v' OR f.cfg IS DISTINCT FROM '{"search_path=pg_catalog, pg_temp"}'
       OR NOT f.is_plpgsql OR NOT f.ret_trigger OR f.pronargs <> 0 OR f.proisstrict OR f.proleakproof OR f.prokind <> 'f' THEN
      RAISE EXCEPTION '1265: live public.mimamsa_predictions_builder_guard() has the captured body but other attributes (security definer / volatility / proconfig / language) differ from the capture; refusing to overwrite.';
    END IF;
  END IF;
END
$capture_guard$;

-- A2. The captured function, byte for byte (the body between the dollar quotes starts with a newline and ends with one).
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

-- A3. The captured trigger: create when absent, otherwise it must have exactly the captured shape.
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

-- B. ASSERT-AND-RECORD the live-only builder grants and the repo objects this file builds beside. Raises; never grants.
DO $record$
DECLARE
  tbl text;
  privs text;
  grantor text;
  n int;
  f record;
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'data_plane_builder') THEN
    RAISE EXCEPTION '1265: role data_plane_builder does not exist; the recorded builder grants cannot hold';
  END IF;
  FOREACH tbl IN ARRAY ARRAY['mimamsa_predictions', 'mimamsa_manifestation_sets'] LOOP
    SELECT string_agg(a.privilege_type, ',' ORDER BY a.privilege_type), min(pg_get_userbyid(a.grantor)), count(DISTINCT a.grantor)
      INTO privs, grantor, n
      FROM pg_class c, aclexplode(c.relacl) a
     WHERE c.oid = ('public.' || tbl)::regclass AND a.grantee = 'data_plane_builder'::regrole;
    IF privs IS DISTINCT FROM 'DELETE,INSERT,SELECT' OR grantor IS DISTINCT FROM 'amjis_app' OR n <> 1 THEN
      RAISE EXCEPTION '1265: the recorded live grant "data_plane_builder=ard/amjis_app" on public.% is not present as recorded (found privileges %, grantor %); this file records it, it does not create it',
        tbl, COALESCE(privs, '<none>'), COALESCE(grantor, '<none>');
    END IF;
  END LOOP;

  SELECT md5(p.prosrc), pg_get_userbyid(p.proowner) AS owner INTO f FROM pg_proc p WHERE p.oid = to_regprocedure('public.bmpl_freeze_confirmed()');
  IF NOT FOUND OR f.md5 <> '70c2ddb261d703fa6a33a4feaf39c99c' THEN
    RAISE EXCEPTION '1265: public.bmpl_freeze_confirmed() is not the repo version (migration 470): md5 %', COALESCE(f.md5, '<absent>');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgrelid = 'public.brahma_mimamsa_prediction_ledger'::regclass AND tgname = 'trg_bmpl_freeze_confirmed'
                  AND tgtype = 19 AND tgenabled = 'O' AND tgfoid = 'public.bmpl_freeze_confirmed()'::regprocedure) THEN
    RAISE EXCEPTION '1265: trigger trg_bmpl_freeze_confirmed is not present as in migration 470 (BEFORE UPDATE FOR EACH ROW, enabled)';
  END IF;
  SELECT md5(p.prosrc) INTO f FROM pg_proc p WHERE p.oid = to_regprocedure('public.brahma_prospective_ledger_enforce_shape()');
  IF NOT FOUND OR f.md5 <> 'acc7ec0121fa1fe0752ae938d9edfafe' THEN
    RAISE EXCEPTION '1265: public.brahma_prospective_ledger_enforce_shape() is not the repo version (migration 458): md5 %', COALESCE(f.md5, '<absent>');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgrelid = 'public.brahma_prospective_ledger'::regclass
                  AND tgname = 'trg_brahma_prospective_ledger_enforce_shape' AND tgtype = 23 AND tgenabled = 'O') THEN
    RAISE EXCEPTION '1265: trigger trg_brahma_prospective_ledger_enforce_shape is not present as in migration 458 (BEFORE INSERT OR UPDATE OF claim_shape, event_class)';
  END IF;
END
$record$;

-- C0. Refuse to overwrite a changed live copy of any new function (idempotent re-run: the exact body is replaced quietly).
DO $new_check$
DECLARE
  rec record;
BEGIN
  FOR rec IN SELECT * FROM (VALUES
      ('l5_frozen_withdrawal_authorizes(uuid)', '3ec94f3a5b54fdb701e56db53cb59ca3'),
      ('l5_frozen_chart_cascade_authorizes(uuid)', 'da32591b1be1a66b6a44cc79c851485b'),
      ('mimamsa_predictions_frozen_row_guard()', 'c70f89cc3be0ce3891e59d4b10f1852d'),
      ('brahma_prospective_ledger_frozen_row_guard()', '0e2abf47bc0b16acfdde5783e9689941'),
      ('mimamsa_manifestation_sets_frozen_row_guard()', 'e362add1186640c49dc4700dfd94c670'),
      ('brahma_mimamsa_prediction_ledger_delete_guard()', '53bd3d5578281090adee5b253346dc17')) AS v(sig, want) LOOP
    IF EXISTS (SELECT 1 FROM pg_proc p WHERE p.oid = to_regprocedure('public.' || rec.sig) AND md5(p.prosrc) <> rec.want) THEN
      RAISE EXCEPTION '1265: live public.% differs from this file''s body (md5 %); refusing to overwrite a changed live guard', rec.sig, rec.want;
    END IF;
  END LOOP;
END
$new_check$;

-- C1. The shared, data-driven withdrawal exception. SECURITY INVOKER, so a role that cannot read the consent tables gets false.
CREATE OR REPLACE FUNCTION public.l5_frozen_withdrawal_authorizes(p_chart uuid)
 RETURNS boolean
 LANGUAGE plpgsql
 STABLE
 SECURITY INVOKER
 SET search_path = pg_catalog, pg_temp
AS $helper$
DECLARE
  v_authorized boolean := false;
BEGIN
  IF p_chart IS NULL
     OR to_regclass('public.chart_subject_consent') IS NULL
     OR to_regclass('public.chart_subject_deletion_disputes') IS NULL THEN
    RETURN false;
  END IF;
  BEGIN
    SELECT EXISTS (SELECT 1 FROM public.chart_subject_consent c
                    WHERE c.chart_id = p_chart AND c.consent_state = 'withdrawn')
       AND NOT EXISTS (SELECT 1 FROM public.chart_subject_deletion_disputes d
                        WHERE d.chart_id = p_chart AND d.status IN ('open', 'reopened', 'escalated'))
      INTO v_authorized;
  EXCEPTION WHEN insufficient_privilege THEN
    v_authorized := false;
  END;
  RETURN COALESCE(v_authorized, false);
END
$helper$;

COMMENT ON FUNCTION public.l5_frozen_withdrawal_authorizes(uuid) IS
  'N-104/N-107 / 1265: true only when the chart''s subject has withdrawn consent (chart_subject_consent) and no deletion dispute is open/reopened/escalated. The single exception to the L5 frozen-history DELETE guards. Fails closed (false) when the consent tables are absent or unreadable by the invoker.';

-- C1b. The chart-deletion allowance (SS N-108): deleting a CHART is the strongest form of consent withdrawal, so the RI cascade of
-- charts(id) ON DELETE CASCADE (migration 1275) may remove the rows of that chart; every other DELETE stays refused. Discriminator:
-- the chart row is gone (inside the RI cascade the parent is already deleted; for a direct delete of a row whose chart exists it never is). SECURITY
-- DEFINER on purpose: public.charts has row-level security ON, so under the invoker's rights a role no policy lets see the chart would read "absent".
-- NOT pg_trigger_depth(): it is 2 in the cascade and in any trigger a role can create. Proved on PostgreSQL 15 and 17 by the tests; reusable: any guard
-- calls public.l5_frozen_chart_cascade_authorizes(OLD.chart_id), before the consent-withdrawal exception.
CREATE OR REPLACE FUNCTION public.l5_frozen_chart_cascade_authorizes(p_chart uuid)
 RETURNS boolean
 LANGUAGE plpgsql
 STABLE
 SECURITY DEFINER
 SET search_path = pg_catalog, pg_temp
AS $cascade$
DECLARE
  v_gone boolean := false;
BEGIN
  -- The discriminator of the chart-deletion allowance (SS N-108): inside the RI cascade of "DELETE FROM charts" the parent row is already deleted,
  -- so the chart is not there; for a DIRECT delete of a row whose chart exists it always is. This function is SECURITY DEFINER (owner = the owner
  -- of public.charts, which bypasses row security): charts has row-level security ON, and under the INVOKER's rights a role that no policy lets
  -- see the chart would read "no such chart" and be authorized. It reads nothing but the existence of one id and returns a boolean.
  -- No setting, role name or session state is consulted. pg_trigger_depth() is deliberately NOT used (it is 2 in the cascade AND in any trigger a
  -- role can create).
  IF p_chart IS NULL OR to_regclass('public.charts') IS NULL THEN
    RETURN false;
  END IF;
  -- STANDING CONSTRAINT (SS): no FORCE ROW LEVEL SECURITY on public.charts without first revisiting this guard. With FORCE, row security applies to the
  -- owner too, this definer would not see the chart, and every direct delete would read "chart absent" and be authorized. So the guard checks it
  -- itself and refuses LOUDLY (the chart delete or the direct delete fails with this message) instead of failing open.
  IF EXISTS (SELECT 1 FROM pg_catalog.pg_class k WHERE k.oid = 'public.charts'::regclass AND k.relforcerowsecurity) THEN
    RAISE EXCEPTION 'l5_frozen_chart_cascade_authorizes: FORCE ROW LEVEL SECURITY is set on public.charts; the 1265 chart-deletion discriminator is unsafe under it (a definer owner would no longer see the chart). Revisit the 1265 guard before keeping FORCE on charts.'
      USING ERRCODE = '42501';
  END IF;
  BEGIN
    SELECT NOT EXISTS (SELECT 1 FROM public.charts c WHERE c.id = p_chart) INTO v_gone;
  EXCEPTION WHEN insufficient_privilege THEN
    v_gone := false;
  END;
  RETURN COALESCE(v_gone, false);
END
$cascade$;

COMMENT ON FUNCTION public.l5_frozen_chart_cascade_authorizes(uuid) IS
  'N-108 / 1265: true when no row of public.charts has that id, i.e. inside the RI cascade of deleting the chart itself (the parent is already deleted). SECURITY DEFINER so row-level security on charts cannot make an existing chart look absent. Residual: orphan rows (chart never existed / deleted without the cascade) and rows of a chart deleted earlier in the same transaction are deletable.';

-- C2. mimamsa_predictions
CREATE OR REPLACE FUNCTION public.mimamsa_predictions_frozen_row_guard()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY INVOKER
 SET search_path = pg_catalog, pg_temp
AS $predictions$
DECLARE
  c_mutable    CONSTANT text[] := ARRAY['lifecycle_status', 'chart_context_stale_at',
                                        'chart_context_stale_reason', 'chart_context_superseded_by_run_id'];
  v_old        jsonb;
  v_new        jsonb;
  v_changed    text[];
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

  -- DELETE. The one exception: the chart's subject has withdrawn consent and no deletion dispute is open (see
  -- public.l5_frozen_withdrawal_authorizes; the consent sweep records the withdrawal and a per-table tombstone).
  IF public.l5_frozen_chart_cascade_authorizes(OLD.chart_id) THEN
    RAISE LOG 'mimamsa_predictions_frozen_row_guard: DELETE authorized as the cascade of deleting the chart itself; chart_id=%, prediction_id=%, user=%',
      OLD.chart_id, OLD.prediction_id, session_user;
    RETURN OLD;
  END IF;
  IF public.l5_frozen_withdrawal_authorizes(OLD.chart_id) THEN
    RAISE LOG 'mimamsa_predictions_frozen_row_guard: DELETE authorized by subject withdrawal (consent withdrawn, no open dispute); chart_id=%, prediction_id=%, user=%',
      OLD.chart_id, OLD.prediction_id, session_user;
    RETURN OLD;
  END IF;

  RAISE EXCEPTION 'mimamsa_predictions_frozen_row_guard: frozen predictions cannot be deleted (a rebuild must not remove or replace them); refusing chart_id=%, prediction_id=%, lifecycle_status=%',
    OLD.chart_id, OLD.prediction_id, COALESCE(OLD.lifecycle_status, '<NULL>')
    USING ERRCODE = '42501';
END
$predictions$;

-- C3. brahma_prospective_ledger
CREATE OR REPLACE FUNCTION public.brahma_prospective_ledger_frozen_row_guard()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY INVOKER
 SET search_path = pg_catalog, pg_temp
AS $prospective$
DECLARE
  c_mutable CONSTANT text[] := ARRAY['lifecycle_status', 'matched_event_id', 'matched_at', 'match_note',
                                     'chart_context_stale_at', 'chart_context_stale_reason',
                                     'chart_context_superseded_by_run_id'];
  v_old     jsonb;
  v_new     jsonb;
  v_changed text[];
BEGIN
  IF TG_OP = 'TRUNCATE' THEN
    RAISE EXCEPTION 'brahma_prospective_ledger_frozen_row_guard: TRUNCATE of public.brahma_prospective_ledger is refused; its rows are filed standing predictions. A subject-withdrawal erasure deletes row by row under the consent gate.'
      USING ERRCODE = '42501';
  END IF;

  IF TG_OP = 'UPDATE' THEN
    -- Fail closed: everything that is not on the allow-list is frozen (the filed claim, falsifier, confidence, window, model, provenance).
    v_old := to_jsonb(OLD) - c_mutable;
    v_new := to_jsonb(NEW) - c_mutable;
    IF v_new IS DISTINCT FROM v_old THEN
      SELECT array_agg(k ORDER BY k) INTO v_changed
        FROM jsonb_object_keys(v_old || v_new) AS k
       WHERE (v_old -> k) IS DISTINCT FROM (v_new -> k);
      RAISE EXCEPTION 'brahma_prospective_ledger_frozen_row_guard: frozen column(s) % cannot be updated; refusing prediction_id=%',
        array_to_string(v_changed, ', '), OLD.prediction_id
        USING ERRCODE = '42501';
    END IF;

    IF NEW.lifecycle_status IS DISTINCT FROM OLD.lifecycle_status THEN
      IF NOT COALESCE(
           (OLD.lifecycle_status = 'open'    AND NEW.lifecycle_status IN ('matched', 'lapsed_unobserved', 'withdrawn'))
        OR (OLD.lifecycle_status = 'matched' AND NEW.lifecycle_status IN ('confirmed', 'falsified', 'withdrawn')),
           false)
      THEN
        RAISE EXCEPTION 'brahma_prospective_ledger_frozen_row_guard: lifecycle_status transition % -> % is not allowed (open -> matched/lapsed_unobserved/withdrawn, matched -> confirmed/falsified/withdrawn); refusing prediction_id=%',
          COALESCE(OLD.lifecycle_status, '<NULL>'), COALESCE(NEW.lifecycle_status, '<NULL>'), OLD.prediction_id
          USING ERRCODE = '42501';
      END IF;
    END IF;

    -- The match record is written once, by the open -> matched transition, and always complete.
    IF (NEW.matched_event_id, NEW.matched_at, NEW.match_note)
         IS DISTINCT FROM (OLD.matched_event_id, OLD.matched_at, OLD.match_note)
       AND NOT COALESCE(OLD.lifecycle_status = 'open' AND NEW.lifecycle_status = 'matched', false) THEN
      RAISE EXCEPTION 'brahma_prospective_ledger_frozen_row_guard: the match record (matched_event_id, matched_at, match_note) can be written only by the open -> matched transition; refusing prediction_id=%',
        OLD.prediction_id
        USING ERRCODE = '42501';
    END IF;
    IF NEW.lifecycle_status = 'matched' AND OLD.lifecycle_status IS DISTINCT FROM 'matched'
       AND (NEW.matched_event_id IS NULL OR NEW.matched_at IS NULL) THEN
      RAISE EXCEPTION 'brahma_prospective_ledger_frozen_row_guard: a matched row must carry matched_event_id and matched_at; refusing prediction_id=%',
        OLD.prediction_id
        USING ERRCODE = '42501';
    END IF;

    -- The staleness marker is additive and set once; the run link may later be cleared (FK ON DELETE SET NULL).
    IF OLD.chart_context_stale_at IS NOT NULL
       AND (NEW.chart_context_stale_at IS DISTINCT FROM OLD.chart_context_stale_at
            OR NEW.chart_context_stale_reason IS DISTINCT FROM OLD.chart_context_stale_reason) THEN
      RAISE EXCEPTION 'brahma_prospective_ledger_frozen_row_guard: the chart-context staleness marker is set once and cannot be changed or cleared; refusing prediction_id=%',
        OLD.prediction_id
        USING ERRCODE = '42501';
    END IF;
    IF NEW.chart_context_superseded_by_run_id IS DISTINCT FROM OLD.chart_context_superseded_by_run_id
       AND NEW.chart_context_superseded_by_run_id IS NOT NULL
       AND (OLD.chart_context_stale_at IS NOT NULL OR NEW.chart_context_stale_at IS NULL) THEN
      RAISE EXCEPTION 'brahma_prospective_ledger_frozen_row_guard: chart_context_superseded_by_run_id can be set only together with the staleness marker; refusing prediction_id=%',
        OLD.prediction_id
        USING ERRCODE = '42501';
    END IF;
    RETURN NEW;
  END IF;

  -- DELETE. Two exceptions: the cascade of deleting the chart itself (the chart row is gone), and a recorded subject withdrawal with no open dispute.
  IF public.l5_frozen_chart_cascade_authorizes(OLD.chart_id) THEN
    RAISE LOG 'brahma_prospective_ledger_frozen_row_guard: DELETE authorized as the cascade of deleting the chart itself; chart_id=%, prediction_id=%, user=%',
      OLD.chart_id, OLD.prediction_id, session_user;
    RETURN OLD;
  END IF;
  IF public.l5_frozen_withdrawal_authorizes(OLD.chart_id) THEN
    RAISE LOG 'brahma_prospective_ledger_frozen_row_guard: DELETE authorized by subject withdrawal (consent withdrawn, no open dispute); chart_id=%, prediction_id=%, user=%',
      OLD.chart_id, OLD.prediction_id, session_user;
    RETURN OLD;
  END IF;

  RAISE EXCEPTION 'brahma_prospective_ledger_frozen_row_guard: filed standing predictions cannot be deleted; refusing prediction_id=%, lifecycle_status=%',
    OLD.prediction_id, COALESCE(OLD.lifecycle_status, '<NULL>')
    USING ERRCODE = '42501';
END
$prospective$;

-- C4. mimamsa_manifestation_sets
CREATE OR REPLACE FUNCTION public.mimamsa_manifestation_sets_frozen_row_guard()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY INVOKER
 SET search_path = pg_catalog, pg_temp
AS $manifestation$
DECLARE
  v_changed text[];
BEGIN
  IF TG_OP = 'TRUNCATE' THEN
    RAISE EXCEPTION 'mimamsa_manifestation_sets_frozen_row_guard: TRUNCATE of public.mimamsa_manifestation_sets is refused; its rows are the frozen citations of the frozen predictions. A subject-withdrawal erasure deletes row by row under the consent gate.'
      USING ERRCODE = '42501';
  END IF;

  IF TG_OP = 'UPDATE' THEN
    -- No column is mutable: a manifestation set row is written once, at freeze, by mi_bhavisya (INSERT only; no UPDATE exists anywhere).
    IF to_jsonb(NEW) IS DISTINCT FROM to_jsonb(OLD) THEN
      SELECT array_agg(k ORDER BY k) INTO v_changed
        FROM jsonb_object_keys(to_jsonb(OLD) || to_jsonb(NEW)) AS k
       WHERE (to_jsonb(OLD) -> k) IS DISTINCT FROM (to_jsonb(NEW) -> k);
      RAISE EXCEPTION 'mimamsa_manifestation_sets_frozen_row_guard: frozen column(s) % cannot be updated; refusing chart_id=%, prediction_id=%, channel_id=%',
        array_to_string(v_changed, ', '), OLD.chart_id, OLD.prediction_id, OLD.channel_id
        USING ERRCODE = '42501';
    END IF;
    RETURN NEW;
  END IF;

  -- DELETE. Two exceptions: the cascade of deleting the chart itself (the chart row is gone), and a recorded subject withdrawal with no open dispute.
  IF public.l5_frozen_chart_cascade_authorizes(OLD.chart_id) THEN
    RAISE LOG 'mimamsa_manifestation_sets_frozen_row_guard: DELETE authorized as the cascade of deleting the chart itself; chart_id=%, prediction_id=%, channel_id=%, user=%',
      OLD.chart_id, OLD.prediction_id, OLD.channel_id, session_user;
    RETURN OLD;
  END IF;
  IF public.l5_frozen_withdrawal_authorizes(OLD.chart_id) THEN
    RAISE LOG 'mimamsa_manifestation_sets_frozen_row_guard: DELETE authorized by subject withdrawal (consent withdrawn, no open dispute); chart_id=%, prediction_id=%, channel_id=%, user=%',
      OLD.chart_id, OLD.prediction_id, OLD.channel_id, session_user;
    RETURN OLD;
  END IF;

  RAISE EXCEPTION 'mimamsa_manifestation_sets_frozen_row_guard: frozen manifestation sets cannot be deleted (a rebuild must not remove or replace them); refusing chart_id=%, prediction_id=%, channel_id=%',
    OLD.chart_id, OLD.prediction_id, OLD.channel_id
    USING ERRCODE = '42501';
END
$manifestation$;

-- C5. brahma_mimamsa_prediction_ledger (DELETE / TRUNCATE; its UPDATE trigger is left as migration 470 made it)
CREATE OR REPLACE FUNCTION public.brahma_mimamsa_prediction_ledger_delete_guard()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY INVOKER
 SET search_path = pg_catalog, pg_temp
AS $bmpl$
BEGIN
  IF TG_OP = 'TRUNCATE' THEN
    RAISE EXCEPTION 'brahma_mimamsa_prediction_ledger_delete_guard: TRUNCATE of public.brahma_mimamsa_prediction_ledger is refused; its rows are the confirmed human claims and their recorded outcomes. A subject-withdrawal erasure deletes row by row under the consent gate.'
      USING ERRCODE = '42501';
  END IF;

  -- DELETE. Two exceptions: the cascade of deleting the chart itself (the chart row is gone), and a recorded subject withdrawal with no open dispute.
  IF public.l5_frozen_chart_cascade_authorizes(OLD.chart_id) THEN
    RAISE LOG 'brahma_mimamsa_prediction_ledger_delete_guard: DELETE authorized as the cascade of deleting the chart itself; chart_id=%, id=%, user=%',
      OLD.chart_id, OLD.id, session_user;
    RETURN OLD;
  END IF;
  IF public.l5_frozen_withdrawal_authorizes(OLD.chart_id) THEN
    RAISE LOG 'brahma_mimamsa_prediction_ledger_delete_guard: DELETE authorized by subject withdrawal (consent withdrawn, no open dispute); chart_id=%, id=%, user=%',
      OLD.chart_id, OLD.id, session_user;
    RETURN OLD;
  END IF;

  RAISE EXCEPTION 'brahma_mimamsa_prediction_ledger_delete_guard: ledger rows cannot be deleted; refusing chart_id=%, id=%, lifecycle_status=%',
    OLD.chart_id, OLD.id, COALESCE(OLD.lifecycle_status, '<NULL>')
    USING ERRCODE = '42501';
END
$bmpl$;

REVOKE ALL ON FUNCTION public.mimamsa_predictions_frozen_row_guard() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.brahma_prospective_ledger_frozen_row_guard() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.mimamsa_manifestation_sets_frozen_row_guard() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.brahma_mimamsa_prediction_ledger_delete_guard() FROM PUBLIC;

COMMENT ON FUNCTION public.mimamsa_predictions_frozen_row_guard() IS
  'N-104/N-107 / 1265: every mimamsa_predictions row is a frozen prediction. UPDATE allows only lifecycle_status (pending->due/confirmed/denied/partial/expired, due->confirmed/denied/partial/expired) and the set-once chart-context staleness marker; DELETE is refused except after a recorded subject withdrawal with no open dispute; TRUNCATE is refused. Applies to every role.';
COMMENT ON FUNCTION public.brahma_prospective_ledger_frozen_row_guard() IS
  'N-107 / 1265: filed standing predictions are frozen. UPDATE allows only the lifecycle (open->matched/lapsed_unobserved/withdrawn, matched->confirmed/falsified/withdrawn), the match record written by open->matched, and the set-once staleness marker; DELETE only after a recorded subject withdrawal; TRUNCATE refused.';
COMMENT ON FUNCTION public.mimamsa_manifestation_sets_frozen_row_guard() IS
  'N-107 / 1265: manifestation sets are the freeze-id citations of the frozen predictions: no UPDATE of any column, DELETE only after a recorded subject withdrawal, TRUNCATE refused.';
COMMENT ON FUNCTION public.brahma_mimamsa_prediction_ledger_delete_guard() IS
  'N-107 / 1265: ledger rows cannot be deleted (only after a recorded subject withdrawal) or truncated. UPDATE freezing stays with trg_bmpl_freeze_confirmed (migration 470).';

-- C6. Triggers (create when absent; a present one must have the expected shape). ENABLE ALWAYS below.
DO $triggers$
DECLARE
  rec record;
  t record;
BEGIN
  FOR rec IN SELECT * FROM (VALUES
      ('mimamsa_predictions', 'mimamsa_predictions_frozen_row_guard', 27, 'mimamsa_predictions_frozen_row_guard'),
      ('mimamsa_predictions', 'mimamsa_predictions_frozen_row_guard_truncate', 34, 'mimamsa_predictions_frozen_row_guard'),
      ('brahma_prospective_ledger', 'brahma_prospective_ledger_frozen_row_guard', 27, 'brahma_prospective_ledger_frozen_row_guard'),
      ('brahma_prospective_ledger', 'brahma_prospective_ledger_frozen_row_guard_truncate', 34, 'brahma_prospective_ledger_frozen_row_guard'),
      ('mimamsa_manifestation_sets', 'mimamsa_manifestation_sets_frozen_row_guard', 27, 'mimamsa_manifestation_sets_frozen_row_guard'),
      ('mimamsa_manifestation_sets', 'mimamsa_manifestation_sets_frozen_row_guard_truncate', 34, 'mimamsa_manifestation_sets_frozen_row_guard'),
      ('brahma_mimamsa_prediction_ledger', 'brahma_mimamsa_prediction_ledger_delete_guard', 11, 'brahma_mimamsa_prediction_ledger_delete_guard'),
      ('brahma_mimamsa_prediction_ledger', 'brahma_mimamsa_prediction_ledger_delete_guard_truncate', 34, 'brahma_mimamsa_prediction_ledger_delete_guard')
    ) AS v(tbl, trg, ttype, fn) LOOP
    SELECT tgtype, tgfoid, tgisinternal INTO t FROM pg_trigger
     WHERE tgrelid = ('public.' || rec.tbl)::regclass AND tgname = rec.trg;
    IF NOT FOUND THEN
      IF rec.ttype = 27 THEN
        EXECUTE format('CREATE TRIGGER %I BEFORE UPDATE OR DELETE ON public.%I FOR EACH ROW EXECUTE FUNCTION public.%I()', rec.trg, rec.tbl, rec.fn);
      ELSIF rec.ttype = 11 THEN
        EXECUTE format('CREATE TRIGGER %I BEFORE DELETE ON public.%I FOR EACH ROW EXECUTE FUNCTION public.%I()', rec.trg, rec.tbl, rec.fn);
      ELSE
        EXECUTE format('CREATE TRIGGER %I BEFORE TRUNCATE ON public.%I FOR EACH STATEMENT EXECUTE FUNCTION public.%I()', rec.trg, rec.tbl, rec.fn);
      END IF;
    ELSIF t.tgtype <> rec.ttype OR t.tgfoid <> ('public.' || rec.fn || '()')::regprocedure OR t.tgisinternal THEN
      RAISE EXCEPTION '1265: existing trigger % on public.% has another shape (tgtype %); refusing', rec.trg, rec.tbl, t.tgtype;
    END IF;
    EXECUTE format('ALTER TABLE public.%I ENABLE ALWAYS TRIGGER %I', rec.tbl, rec.trg);
  END LOOP;
END
$triggers$;

-- D1. SELF-TEST helpers (session-local, dropped below): run a statement and require that THE GUARD refused it.
CREATE FUNCTION pg_temp.m1265_refused(stmt text, prefix text) RETURNS text LANGUAGE plpgsql AS $h$
DECLARE msg text;
BEGIN
  BEGIN
    EXECUTE stmt;
    RETURN format('not refused: %s', left(stmt, 120));
  EXCEPTION WHEN insufficient_privilege THEN
    GET STACKED DIAGNOSTICS msg = MESSAGE_TEXT;
    IF msg NOT LIKE prefix || '%' THEN
      RETURN format('refused by something else (%s): %s', left(msg, 100), left(stmt, 80));
    END IF;
    RETURN NULL;
  WHEN OTHERS THEN
    GET STACKED DIAGNOSTICS msg = MESSAGE_TEXT;
    RETURN format('unexpected error (%s): %s', left(msg, 100), left(stmt, 80));
  END;
END
$h$;

CREATE FUNCTION pg_temp.m1265_passes(stmt text) RETURNS text LANGUAGE plpgsql AS $h$
DECLARE msg text;
BEGIN
  BEGIN
    EXECUTE stmt;
    RETURN NULL;
  EXCEPTION WHEN OTHERS THEN
    GET STACKED DIAGNOSTICS msg = MESSAGE_TEXT;
    RETURN format('legal statement refused (%s): %s', left(msg, 100), left(stmt, 80));
  END;
END
$h$;

-- D2. SELF-TEST: every probe row is rolled back by the final sentinel exception; any unrefused / wrongly refused action fails the file.
-- The probes hang on ONE EXISTING chart when there is one (the chart_id -> charts(id) foreign keys of migration 1275 would reject a random id) and every
-- statement is scoped to the probe row's own key, so no real row of that chart is touched even for a moment beyond the rolled-back probes.
DO $selftest$
DECLARE
  failures text[] := ARRAY[]::text[];
  r text;
  pc uuid;
  ppid CONSTANT uuid := gen_random_uuid();
  bid CONSTANT uuid := gen_random_uuid();
  ev text;
  shp text;
  win text;
  mil text;
BEGIN
  IF to_regclass('public.charts') IS NOT NULL THEN
    EXECUTE 'SELECT id FROM public.charts ORDER BY id LIMIT 1' INTO pc;
    IF pc IS NULL THEN
      RAISE EXCEPTION '1265 self-test cannot run: public.charts has no row to hang the probes on (a probe whose chart is missing would be deletable by the chart-deletion allowance, and with the 1275 foreign keys it could not be inserted)';
    END IF;
  ELSE
    pc := gen_random_uuid();
  END IF;
  BEGIN
    -- ---- mimamsa_predictions
    INSERT INTO public.mimamsa_predictions
      (chart_id, prediction_id, source_pramana_id, outcome_claim, domain, observation_window, eval_date,
       confidence_band, magnitude_expected, falsifier_jsonb, emitted_at, lifecycle_status, driving_signals,
       frozen_bundle_hash, bundle_formula_version)
    VALUES (pc, 'm1265_probe', 'm1265_probe_src', 'm1265 probe', 'm1265', daterange(current_date, current_date + 1), current_date,
            numrange(0.1, 0.9), 'm1265', '{}'::jsonb, now(), 'pending', '[]'::jsonb, 'm1265', 'm1265');
    FOREACH r IN ARRAY ARRAY[
      pg_temp.m1265_refused(format('UPDATE public.mimamsa_predictions SET source_pramana_id = %L WHERE chart_id = %L AND prediction_id = %L', 'changed', pc, 'm1265_probe'), 'mimamsa_predictions_frozen_row_guard:'),
      pg_temp.m1265_refused(format('UPDATE public.mimamsa_predictions SET lifecycle_status = %L WHERE chart_id = %L AND prediction_id = %L', 'bogus', pc, 'm1265_probe'), 'mimamsa_predictions_frozen_row_guard:'),
      pg_temp.m1265_refused(format('DELETE FROM public.mimamsa_predictions WHERE chart_id = %L AND prediction_id = %L', pc, 'm1265_probe'), 'mimamsa_predictions_frozen_row_guard:'),
      pg_temp.m1265_passes(format('UPDATE public.mimamsa_predictions SET lifecycle_status = %L WHERE chart_id = %L AND prediction_id = %L', 'confirmed', pc, 'm1265_probe')),
      pg_temp.m1265_refused(format('UPDATE public.mimamsa_predictions SET lifecycle_status = %L WHERE chart_id = %L AND prediction_id = %L', 'pending', pc, 'm1265_probe'), 'mimamsa_predictions_frozen_row_guard:'),
      pg_temp.m1265_refused(format('UPDATE public.mimamsa_predictions SET outcome_claim = %L WHERE chart_id = %L AND prediction_id = %L', 'changed', pc, 'm1265_probe'), 'mimamsa_predictions_frozen_row_guard:'),
      pg_temp.m1265_passes(format('UPDATE public.mimamsa_predictions SET chart_context_stale_at = now(), chart_context_stale_reason = %L WHERE chart_id = %L AND prediction_id = %L', 'chart_details_changed', pc, 'm1265_probe'))
    ] LOOP
      IF r IS NOT NULL THEN failures := array_append(failures, 'mimamsa_predictions: ' || r); END IF;
    END LOOP;
    IF has_table_privilege(current_user, 'public.mimamsa_predictions', 'TRUNCATE') THEN
      r := pg_temp.m1265_refused('TRUNCATE public.mimamsa_predictions', 'mimamsa_predictions_frozen_row_guard:');
      IF r IS NOT NULL THEN failures := array_append(failures, 'mimamsa_predictions: ' || r); END IF;
    ELSE
      RAISE NOTICE '1265 self-test: TRUNCATE branch skipped for mimamsa_predictions, % holds no TRUNCATE privilege (the mirrored-role tests cover it)', current_user;
    END IF;

    -- ---- mimamsa_manifestation_sets
    INSERT INTO public.mimamsa_manifestation_sets (chart_id, prediction_id, channel_id, domain, source, citation_ref, is_literal, frozen_at)
    VALUES (pc, 'm1265_probe', 'ch_m1265', 'm1265', 'm1265', '{"k": 1}'::jsonb, true, now());
    FOREACH r IN ARRAY ARRAY[
      pg_temp.m1265_refused(format('UPDATE public.mimamsa_manifestation_sets SET domain = %L WHERE chart_id = %L AND prediction_id = %L AND channel_id = %L', 'changed', pc, 'm1265_probe', 'ch_m1265'), 'mimamsa_manifestation_sets_frozen_row_guard:'),
      pg_temp.m1265_refused(format('UPDATE public.mimamsa_manifestation_sets SET citation_ref = %L::jsonb WHERE chart_id = %L AND prediction_id = %L AND channel_id = %L', '{"k": 2}', pc, 'm1265_probe', 'ch_m1265'), 'mimamsa_manifestation_sets_frozen_row_guard:'),
      pg_temp.m1265_refused(format('DELETE FROM public.mimamsa_manifestation_sets WHERE chart_id = %L AND prediction_id = %L AND channel_id = %L', pc, 'm1265_probe', 'ch_m1265'), 'mimamsa_manifestation_sets_frozen_row_guard:'),
      pg_temp.m1265_passes(format('UPDATE public.mimamsa_manifestation_sets SET domain = domain WHERE chart_id = %L AND prediction_id = %L AND channel_id = %L', pc, 'm1265_probe', 'ch_m1265'))
    ] LOOP
      IF r IS NOT NULL THEN failures := array_append(failures, 'mimamsa_manifestation_sets: ' || r); END IF;
    END LOOP;
    IF has_table_privilege(current_user, 'public.mimamsa_manifestation_sets', 'TRUNCATE') THEN
      r := pg_temp.m1265_refused('TRUNCATE public.mimamsa_manifestation_sets', 'mimamsa_manifestation_sets_frozen_row_guard:');
      IF r IS NOT NULL THEN failures := array_append(failures, 'mimamsa_manifestation_sets: ' || r); END IF;
    END IF;

    -- ---- brahma_mimamsa_prediction_ledger
    INSERT INTO public.brahma_mimamsa_prediction_ledger (id, chart_id, claim_text) VALUES (bid, pc, 'm1265 probe');
    r := pg_temp.m1265_refused(format('DELETE FROM public.brahma_mimamsa_prediction_ledger WHERE id = %L', bid), 'brahma_mimamsa_prediction_ledger_delete_guard:');
    IF r IS NOT NULL THEN failures := array_append(failures, 'brahma_mimamsa_prediction_ledger: ' || r); END IF;
    IF has_table_privilege(current_user, 'public.brahma_mimamsa_prediction_ledger', 'TRUNCATE') THEN
      r := pg_temp.m1265_refused('TRUNCATE public.brahma_mimamsa_prediction_ledger', 'brahma_mimamsa_prediction_ledger_delete_guard:');
      IF r IS NOT NULL THEN failures := array_append(failures, 'brahma_mimamsa_prediction_ledger: ' || r); END IF;
    END IF;
    -- the existing UPDATE freeze is not ours to change: a detected row may be edited
    r := pg_temp.m1265_passes(format('UPDATE public.brahma_mimamsa_prediction_ledger SET claim_text = %L WHERE id = %L', 'edited while detected', bid));
    IF r IS NOT NULL THEN failures := array_append(failures, 'brahma_mimamsa_prediction_ledger: ' || r); END IF;

    -- ---- brahma_prospective_ledger (needs one ontology class; the shape trigger ties claim_shape to it)
    SELECT event_class_id, temporal_shape INTO ev, shp FROM public.brahma_event_ontology ORDER BY event_class_id LIMIT 1;
    IF ev IS NULL THEN
      RAISE EXCEPTION '1265 self-test cannot run: brahma_event_ontology has no row to file a probe prediction against';
    END IF;
    win := CASE shp WHEN 'point' THEN format('daterange(%L, %L)', current_date, current_date + 1)
                    WHEN 'interval' THEN format('daterange(%L, %L)', current_date, current_date + 5) ELSE 'NULL' END;
    mil := CASE shp WHEN 'chain' THEN '''[{"milestone_id": "m1265"}]''::jsonb' ELSE 'NULL' END;
    EXECUTE format('INSERT INTO public.brahma_prospective_ledger (prediction_id, chart_id, claim, event_class, claim_shape, observation_window, milestone_set, model, formula_version, confidence, falsifier, generator_class, filed_by, source_citation) '
                   'VALUES (%L, %L, %L, %L, %L, %s, %s, %L, %L, 0.5, %L, %L, %L, %L)',
                   ppid, pc, 'm1265 probe', ev, shp, win, mil, 'm1265', 'm1265', 'm1265 falsifier', 'engine', 'm1265', 'm1265');
    FOREACH r IN ARRAY ARRAY[
      pg_temp.m1265_refused(format('UPDATE public.brahma_prospective_ledger SET claim = %L WHERE prediction_id = %L', 'changed', ppid), 'brahma_prospective_ledger_frozen_row_guard:'),
      pg_temp.m1265_refused(format('UPDATE public.brahma_prospective_ledger SET confidence = 0.9 WHERE prediction_id = %L', ppid), 'brahma_prospective_ledger_frozen_row_guard:'),
      pg_temp.m1265_refused(format('UPDATE public.brahma_prospective_ledger SET lifecycle_status = %L WHERE prediction_id = %L', 'confirmed', ppid), 'brahma_prospective_ledger_frozen_row_guard:'),
      pg_temp.m1265_refused(format('UPDATE public.brahma_prospective_ledger SET match_note = %L WHERE prediction_id = %L', 'note', ppid), 'brahma_prospective_ledger_frozen_row_guard:'),
      pg_temp.m1265_refused(format('UPDATE public.brahma_prospective_ledger SET lifecycle_status = %L WHERE prediction_id = %L', 'matched', ppid), 'brahma_prospective_ledger_frozen_row_guard:'),
      pg_temp.m1265_refused(format('DELETE FROM public.brahma_prospective_ledger WHERE prediction_id = %L', ppid), 'brahma_prospective_ledger_frozen_row_guard:'),
      pg_temp.m1265_passes(format('UPDATE public.brahma_prospective_ledger SET lifecycle_status = %L WHERE prediction_id = %L', 'withdrawn', ppid)),
      pg_temp.m1265_refused(format('UPDATE public.brahma_prospective_ledger SET lifecycle_status = %L WHERE prediction_id = %L', 'open', ppid), 'brahma_prospective_ledger_frozen_row_guard:'),
      pg_temp.m1265_passes(format('UPDATE public.brahma_prospective_ledger SET chart_context_stale_at = now(), chart_context_stale_reason = %L WHERE prediction_id = %L', 'chart_details_changed', ppid))
    ] LOOP
      IF r IS NOT NULL THEN failures := array_append(failures, 'brahma_prospective_ledger: ' || r); END IF;
    END LOOP;
    IF has_table_privilege(current_user, 'public.brahma_prospective_ledger', 'TRUNCATE') THEN
      r := pg_temp.m1265_refused('TRUNCATE public.brahma_prospective_ledger', 'brahma_prospective_ledger_frozen_row_guard:');
      IF r IS NOT NULL THEN failures := array_append(failures, 'brahma_prospective_ledger: ' || r); END IF;
    END IF;

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

DROP FUNCTION pg_temp.m1265_refused(text, text);
DROP FUNCTION pg_temp.m1265_passes(text);

-- E. POST-CHECK (asserting: RAISES). The final catalog state is exactly what this file describes.
DO $post$
DECLARE
  rec record;
  bad int;
BEGIN
  FOR rec IN SELECT * FROM (VALUES
      ('mimamsa_predictions_builder_guard()', '46c23854275c2712b30860a2b174adb2'),
      ('l5_frozen_withdrawal_authorizes(uuid)', '3ec94f3a5b54fdb701e56db53cb59ca3'),
      ('l5_frozen_chart_cascade_authorizes(uuid)', 'da32591b1be1a66b6a44cc79c851485b'),
      ('mimamsa_predictions_frozen_row_guard()', 'c70f89cc3be0ce3891e59d4b10f1852d'),
      ('brahma_prospective_ledger_frozen_row_guard()', '0e2abf47bc0b16acfdde5783e9689941'),
      ('mimamsa_manifestation_sets_frozen_row_guard()', 'e362add1186640c49dc4700dfd94c670'),
      ('brahma_mimamsa_prediction_ledger_delete_guard()', '53bd3d5578281090adee5b253346dc17')) AS v(sig, want) LOOP
    IF (SELECT md5(prosrc) FROM pg_proc WHERE oid = to_regprocedure('public.' || rec.sig)) IS DISTINCT FROM rec.want THEN
      RAISE EXCEPTION '1265 post-check: public.% is not this file''s body', rec.sig;
    END IF;
  END LOOP;
  SELECT count(*) INTO bad FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid
   WHERE c.relnamespace = 'public'::regnamespace AND NOT t.tgisinternal
     AND c.relname IN ('mimamsa_predictions', 'brahma_prospective_ledger', 'mimamsa_manifestation_sets', 'brahma_mimamsa_prediction_ledger')
     AND ((t.tgname = 'mimamsa_predictions_builder_guard' AND t.tgenabled = 'O')
       OR (t.tgname IN ('mimamsa_predictions_frozen_row_guard', 'mimamsa_predictions_frozen_row_guard_truncate',
                        'brahma_prospective_ledger_frozen_row_guard', 'brahma_prospective_ledger_frozen_row_guard_truncate',
                        'mimamsa_manifestation_sets_frozen_row_guard', 'mimamsa_manifestation_sets_frozen_row_guard_truncate',
                        'brahma_mimamsa_prediction_ledger_delete_guard', 'brahma_mimamsa_prediction_ledger_delete_guard_truncate') AND t.tgenabled = 'A')
       OR (t.tgname IN ('trg_bmpl_freeze_confirmed', 'trg_brahma_prospective_ledger_enforce_shape') AND t.tgenabled = 'O'));
  IF bad <> 11 THEN
    RAISE EXCEPTION '1265 post-check: expected 11 guard/existing triggers with the right enablement, found %', bad;
  END IF;
  IF EXISTS (SELECT 1 FROM pg_proc WHERE oid IN (
        to_regprocedure('public.mimamsa_predictions_builder_guard()'), to_regprocedure('public.mimamsa_predictions_frozen_row_guard()'),
        to_regprocedure('public.brahma_prospective_ledger_frozen_row_guard()'), to_regprocedure('public.mimamsa_manifestation_sets_frozen_row_guard()'),
        to_regprocedure('public.brahma_mimamsa_prediction_ledger_delete_guard()'))
       AND (prosecdef OR has_function_privilege('public', oid, 'EXECUTE'))) THEN
    RAISE EXCEPTION '1265 post-check: a trigger guard function is SECURITY DEFINER or executable by PUBLIC';
  END IF;
  IF (SELECT prosecdef FROM pg_proc WHERE oid = to_regprocedure('public.l5_frozen_withdrawal_authorizes(uuid)')) THEN
    RAISE EXCEPTION '1265 post-check: the withdrawal helper is SECURITY DEFINER';
  END IF;
  IF to_regclass('public.charts') IS NOT NULL AND (SELECT relforcerowsecurity FROM pg_class WHERE oid = 'public.charts'::regclass) THEN
    RAISE EXCEPTION '1265 post-check: STANDING CONSTRAINT violated: public.charts has FORCE ROW LEVEL SECURITY';
  END IF;
  IF NOT (SELECT prosecdef FROM pg_proc WHERE oid = to_regprocedure('public.l5_frozen_chart_cascade_authorizes(uuid)')) THEN
    RAISE EXCEPTION '1265 post-check: the chart-cascade helper must be SECURITY DEFINER (row-level security on charts)';
  END IF;
  IF to_regclass('public.charts') IS NOT NULL AND NOT EXISTS (
       SELECT 1 FROM pg_proc p JOIN pg_class c ON c.oid = 'public.charts'::regclass JOIN pg_roles r ON r.oid = p.proowner
        WHERE p.oid = to_regprocedure('public.l5_frozen_chart_cascade_authorizes(uuid)')
          AND (p.proowner = c.relowner OR r.rolsuper OR r.rolbypassrls)) THEN
    RAISE EXCEPTION '1265 post-check: the chart-cascade helper is not owned by the owner of public.charts (or a role that bypasses row security), so row-level security could hide a chart from it';
  END IF;
END
$post$;
