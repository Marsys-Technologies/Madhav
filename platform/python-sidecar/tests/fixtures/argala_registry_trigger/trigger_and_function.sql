-- The REAL serving-invalidation trigger of asset_registry, read from the live database as suvarna_reader on 2026-10-02
-- (pg_get_functiondef('nirmana_invalidate_registry_receipts'::regproc) and pg_get_triggerdef of nirmana_registry_receipt_invalidation).
-- Used verbatim by the argala migration tests (1219, 1221): the trigger fires only on UPDATE OF the listed columns.
CREATE OR REPLACE FUNCTION public.nirmana_invalidate_registry_receipts()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
  UPDATE asset_freshness
     SET freshness_state = 'stale',
         reasons = CASE
           WHEN reasons ? 'registry_changed' THEN reasons
           ELSE reasons || '["registry_changed"]'::jsonb
         END,
         observed_at = now()
   WHERE asset_id = NEW.asset_id;
  RETURN NEW;
END;
$function$
;
CREATE TRIGGER nirmana_registry_receipt_invalidation AFTER UPDATE OF depends_on, natural_key_partition, health_probe, integrity_check_sql, target_floor, asset_kind, asset_type, scope, has_writer, is_active, target_table ON public.asset_registry FOR EACH ROW WHEN ((old.* IS DISTINCT FROM new.*)) EXECUTE FUNCTION nirmana_invalidate_registry_receipts();
