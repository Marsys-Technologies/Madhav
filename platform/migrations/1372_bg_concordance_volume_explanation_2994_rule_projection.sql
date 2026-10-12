-- 1372_bg_concordance_volume_explanation_2994_rule_projection.sql   (documentation fix)
--
-- Documentation fix, ONE column of ONE registry row (volume_explanation): the registered prose says "canonical 3,002-rule projection"; since the rules table dropped 8 consequence-less rules
-- (3,002 -> 2,994; migration 1368) and the projection was rebuilt (migration 1370 re-sealed its check, run 45c8b3b1), the registered explanation must name the current size. The stored check never
-- reads this column; the three places that carry the prose move together in the same release: this row, scripts/seed/asset_registry_seed.ts, and the constant of the contract test
-- tests/unit/migrations/nirmana_l0_concordance_integrity_contract.test.ts. The old prose is kept as history in migration 1370's text (never edited; the 619 constant inside the contract test is the test's own history).
-- GUARD: the UPDATE replaces only the exact old explanation (and the exact floor 721 and partition key); a different live text is a NOTICE-and-NO-OP; a row already at the new text is an idempotent
-- no-op; a silent no-op of an UPDATE that should have matched RAISES. Transaction ownership belongs to platform/scripts/migrate.ts (no BEGIN/COMMIT here). Data-only.
-- TRIGGER EFFECT: nirmana_registry_receipt_invalidation fires on an UPDATE of volume_explanation only if that column is in its watched list; if it fires, this asset's freshness becomes 'stale'
-- (registry_changed) until its next build (the follow-up rebuild of this asset). VERIFY after deploy: SELECT md5(volume_explanation) FROM asset_registry WHERE asset_id = 'bg_concordance';

SET LOCAL lock_timeout = '5s';

DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  changed_rows integer := 0;
  old_explanation constant text := $oldexpl$721 deterministic topic×school concordance rows from the frozen 10,651-chunk topic index and canonical 3,002-rule projection. The convergent rebuild repairs stale pointers and includes lord_1st_in_11th, whose tagged chunks existed in production while its historical concordance row was absent.$oldexpl$;
  new_explanation constant text := $newexpl$721 deterministic topic×school concordance rows from the frozen 10,651-chunk topic index and canonical 2,994-rule projection. The convergent rebuild repairs stale pointers and includes lord_1st_in_11th, whose tagged chunks existed in production while its historical concordance row was absent.$newexpl$;
BEGIN
  SELECT * INTO registry_row FROM asset_registry WHERE asset_id = 'bg_concordance' FOR UPDATE;
  IF NOT FOUND THEN
    RAISE NOTICE '1372: no bg_concordance registry row (empty registry); nothing to do';
    RETURN;
  END IF;
  IF registry_row.volume_explanation IS NOT DISTINCT FROM new_explanation THEN
    RAISE NOTICE '1372: bg_concordance volume_explanation already names the 2,994-rule projection; nothing to do';
    RETURN;
  END IF;
  IF registry_row.volume_explanation IS DISTINCT FROM old_explanation OR registry_row.target_floor IS DISTINCT FROM 721 THEN
    RAISE NOTICE '1372: bg_concordance volume_explanation / floor is not the state this migration was written against (floor %); NO-OP, left as is', registry_row.target_floor;
    RETURN;
  END IF;
  UPDATE asset_registry SET volume_explanation = new_explanation
   WHERE asset_id = 'bg_concordance' AND volume_explanation = old_explanation AND target_floor = 721;
  GET DIAGNOSTICS changed_rows = ROW_COUNT;
  IF changed_rows <> 1 THEN
    RAISE EXCEPTION '1372: bg_concordance volume_explanation update did not take (rows %)', changed_rows;
  END IF;
END $$;
