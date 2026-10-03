-- 1265 ROLLBACK: OWNER-PATH SQL (executor package only; never under platform/migrations). Run ONLY by l5_frozen_guard_exec.py
-- (--rollback-dry-run / --rollback) as role amjis_app inside the executor's transaction. The exact inverse of 1265_l5_frozen_row_guards.sql:
-- drops the 8 new triggers and the 6 new functions. The captured builder guard (live before 1265, live-only) and the pre-existing
-- repo triggers stay; no schema CREATE capability is needed to DROP, so the executor does not open one. No row is touched.

SET LOCAL lock_timeout = '5s';

DO $rb_pre$
DECLARE
  rec record;
BEGIN
  FOR rec IN SELECT * FROM (VALUES
      ('l5_frozen_withdrawal_authorizes(uuid)', '3ec94f3a5b54fdb701e56db53cb59ca3'),
      ('l5_frozen_chart_cascade_authorizes(uuid)', '1c2fb1d0e8d0acfa39b3554f1ea37377'),
      ('mimamsa_predictions_frozen_row_guard()', '5f55fe7cf0df358060a35920274aab64'),
      ('brahma_prospective_ledger_frozen_row_guard()', '534824492a0e7e33890052513d12b8e1'),
      ('mimamsa_manifestation_sets_frozen_row_guard()', 'dff9cfbc1d10df4f427b9a7379e6ff51'),
      ('brahma_mimamsa_prediction_ledger_delete_guard()', '9250b082084b156828dd97a9c264888b'),
      ('mimamsa_predictions_builder_guard()', '46c23854275c2712b30860a2b174adb2')) AS v(sig, want) LOOP
    IF (SELECT md5(prosrc) FROM pg_proc WHERE oid = to_regprocedure('public.' || rec.sig)) IS DISTINCT FROM rec.want THEN
      RAISE EXCEPTION '1265 rollback: public.% is absent or not the body this plan installed; refusing', rec.sig;
    END IF;
  END LOOP;
  IF (SELECT count(*) FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid
       WHERE c.relnamespace = 'public'::regnamespace AND NOT t.tgisinternal AND t.tgenabled = 'A'
         AND t.tgname IN ('mimamsa_predictions_frozen_row_guard', 'mimamsa_predictions_frozen_row_guard_truncate',
                          'brahma_prospective_ledger_frozen_row_guard', 'brahma_prospective_ledger_frozen_row_guard_truncate',
                          'mimamsa_manifestation_sets_frozen_row_guard', 'mimamsa_manifestation_sets_frozen_row_guard_truncate',
                          'brahma_mimamsa_prediction_ledger_delete_guard', 'brahma_mimamsa_prediction_ledger_delete_guard_truncate')) <> 8 THEN
    RAISE EXCEPTION '1265 rollback: the 8 installed triggers are not all present and enabled ALWAYS; refusing';
  END IF;
END
$rb_pre$;

DROP TRIGGER mimamsa_predictions_frozen_row_guard_truncate ON public.mimamsa_predictions;
DROP TRIGGER mimamsa_predictions_frozen_row_guard ON public.mimamsa_predictions;
DROP TRIGGER brahma_prospective_ledger_frozen_row_guard_truncate ON public.brahma_prospective_ledger;
DROP TRIGGER brahma_prospective_ledger_frozen_row_guard ON public.brahma_prospective_ledger;
DROP TRIGGER mimamsa_manifestation_sets_frozen_row_guard_truncate ON public.mimamsa_manifestation_sets;
DROP TRIGGER mimamsa_manifestation_sets_frozen_row_guard ON public.mimamsa_manifestation_sets;
DROP TRIGGER brahma_mimamsa_prediction_ledger_delete_guard_truncate ON public.brahma_mimamsa_prediction_ledger;
DROP TRIGGER brahma_mimamsa_prediction_ledger_delete_guard ON public.brahma_mimamsa_prediction_ledger;

DROP FUNCTION public.mimamsa_predictions_frozen_row_guard();
DROP FUNCTION public.brahma_prospective_ledger_frozen_row_guard();
DROP FUNCTION public.mimamsa_manifestation_sets_frozen_row_guard();
DROP FUNCTION public.brahma_mimamsa_prediction_ledger_delete_guard();
DROP FUNCTION public.l5_frozen_chart_cascade_authorizes(uuid);
DROP FUNCTION public.l5_frozen_withdrawal_authorizes(uuid);

DO $rb_post$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_proc WHERE proname IN ('l5_frozen_withdrawal_authorizes', 'l5_frozen_chart_cascade_authorizes', 'mimamsa_predictions_frozen_row_guard',
        'brahma_prospective_ledger_frozen_row_guard', 'mimamsa_manifestation_sets_frozen_row_guard', 'brahma_mimamsa_prediction_ledger_delete_guard')) THEN
    RAISE EXCEPTION '1265 rollback post-check: a 1265 function is still present';
  END IF;
  IF EXISTS (SELECT 1 FROM pg_trigger WHERE tgname LIKE '%frozen_row_guard%' OR tgname LIKE 'brahma_mimamsa_prediction_ledger_delete_guard%') THEN
    RAISE EXCEPTION '1265 rollback post-check: a 1265 trigger is still present';
  END IF;
  IF (SELECT md5(prosrc) FROM pg_proc WHERE oid = to_regprocedure('public.mimamsa_predictions_builder_guard()')) IS DISTINCT FROM '46c23854275c2712b30860a2b174adb2'
     OR NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgrelid = 'public.mimamsa_predictions'::regclass AND tgname = 'mimamsa_predictions_builder_guard' AND tgenabled = 'O')
     OR NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgrelid = 'public.brahma_mimamsa_prediction_ledger'::regclass AND tgname = 'trg_bmpl_freeze_confirmed' AND tgenabled = 'O')
     OR NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgrelid = 'public.brahma_prospective_ledger'::regclass AND tgname = 'trg_brahma_prospective_ledger_enforce_shape' AND tgenabled = 'O') THEN
    RAISE EXCEPTION '1265 rollback post-check: the captured builder guard or an existing repo trigger is not intact';
  END IF;
END
$rb_post$;
