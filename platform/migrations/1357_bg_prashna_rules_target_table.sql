-- 1357_bg_prashna_rules_target_table.sql
--
-- Certification registry fix (SS N-425, Exec Suvarna). ONE guarded UPDATE of ONE column (target_table) of ONE asset_registry row
-- (bg_prashna_rules); nothing else. Transaction ownership belongs to platform/scripts/migrate.ts (no BEGIN/COMMIT here). Data-only: no
-- table or function is created or altered, so it runs as amjis_app on the routine path (no CREATE on schema public needed).
-- Same shape as 1340 (target_table IS NULL guard in place of an md5 guard; post-check raises if the UPDATE did not take).
--
-- THE GAP. bg_prashna_rules has target_table NULL. The census cells Ldgr and Vocab.identity read only asset_registry.target_table
-- (asset_census.py measure()), so the asset reads as having no table at all. Its source declaration (read_table) names
-- bg_prashna_tajik_yogas (16 rows, unique key yoga_id, platform/migrations/261_bg_prashna_rules_schema.sql).
--
-- WHAT THIS COVERS, HONESTLY. The asset's registered writer (pipeline/orchestrator/writers/bg_prashna_rules.py ->
-- brahmagyan/l0_prashna.py seed_prashna_rules) writes FIVE tables: bg_prashna_lagna_methods, bg_prashna_tajik_yogas,
-- bg_prashna_significators, bg_prashna_fructification_rules, bg_prashna_special_techniques (5 + 16 + 12 + 5 + 3 = 41 rows, the
-- registered count_sql, which already sums all five and is NOT touched). target_table is a single-table field: it names the one
-- table the declaration identifies, which covers 1 of 5. Full coverage of the table set needs an engine form (the Engine's walk
-- of asset_declarations.json), not a registry column; that is out of scope here.
--
-- REVERSAL OF EARLIER RULING Q10 (SS 2026-10-01). Q10 accepted the elevation brief's disposition "keep (P)" for bg_prashna_rules and
-- dropped the carried "declare its table set" item, because the census then read Build.target PASS without a target_table
-- (00_ARCHITECTURE/briefs/suvarna/layers/L0/assets/bg_prashna_rules_ELEVATION_BRIEF_v1_0.md, INDEX.md item 10). This migration
-- reverses that to the extent of recording the one table the declaration names, because the Ldgr / Vocab.identity cells need it.
--
-- COUPLED CHANGE (same PR): platform/src/lib/cockpit/assetClearSpec.ts gets an EXPLICIT_CLEAR_OPS entry for bg_prashna_rules that
-- clears all five tables. Without it, once target_table is set, the generic fallback in api/cockpit/clear/execute/route.ts (and
-- src/lib/build/assetInvalidation.ts) would resolve to "DELETE FROM bg_prashna_tajik_yogas" and leave the other four tables behind
-- (before this migration the same asset resolved to no clear spec at all, because its summed count_sql cannot be auto-derived).
--
-- GUARD. The UPDATE runs only while target_table IS NULL. A row that already holds a value (this one or another) is left as is
-- with a NOTICE; an absent row (empty registry) is a no-op with a NOTICE. The ONE case that RAISES: the post-check finds the row
-- present and target_table still NULL (the UPDATE silently did nothing; never trust a silent no-op, CLAUDE.md N.4).
--
-- TRIGGER EFFECT (real, intended). target_table is one of the columns of nirmana_registry_receipt_invalidation (migration 596):
-- the UPDATE stales the asset_freshness rows of bg_prashna_rules ONLY (registry_changed), so bg_prashna_rules must be re-run, then
-- ga_prashna (its consumer) rebuilt. No other asset's freshness row changes. Setting target_table also changes the asset's
-- registry-contract fingerprint (its frozen manifest reads evidence_refresh_required until refreshed).
--
-- NOT CHANGED HERE: count_sql, size_sql, target_floor, volume_explanation, natural_key_partition, the TypeScript seed
-- (scripts/seed/asset_registry_seed.ts keeps target_table: null; its registry insert is ON CONFLICT DO NOTHING, so a re-seed never
-- reverts this, and a fresh database replaying the seed then the migrations holds NULL, matches the guard, and is set here), any
-- data row, the writer, asset_declarations.json.
--
-- VERIFICATION BY PRODUCTION STRUCTURE (never trust a deploy log). After the deploy, as the read-only role:
--   SELECT asset_id, target_table FROM asset_registry WHERE asset_id = 'bg_prashna_rules';   -- expect bg_prashna_tajik_yogas
--
-- ROLLBACK (not executed by migrate.ts): UPDATE asset_registry SET target_table = NULL
-- WHERE asset_id = 'bg_prashna_rules' AND target_table = 'bg_prashna_tajik_yogas';

SET LOCAL lock_timeout = '5s';

DO $pre$
DECLARE v_n int; v_tt text;
BEGIN
  SELECT count(*), max(target_table) INTO v_n, v_tt FROM asset_registry WHERE asset_id = 'bg_prashna_rules';
  IF v_n = 0 THEN
    RAISE NOTICE '1357: no bg_prashna_rules registry row (empty registry); nothing to do';
  ELSIF v_tt = 'bg_prashna_tajik_yogas' THEN
    RAISE NOTICE '1357: bg_prashna_rules target_table is already bg_prashna_tajik_yogas; nothing to do';
  ELSIF v_tt IS NOT NULL THEN
    RAISE NOTICE '1357: bg_prashna_rules target_table is already % (not NULL); NO-OP, target_table left as is', v_tt;
  END IF;
END
$pre$;

UPDATE asset_registry
SET target_table = 'bg_prashna_tajik_yogas'
WHERE asset_id = 'bg_prashna_rules'
  AND target_table IS NULL;

DO $post$
DECLARE v_n int; v_tt text;
BEGIN
  SELECT count(*), max(target_table) INTO v_n, v_tt FROM asset_registry WHERE asset_id = 'bg_prashna_rules';
  IF v_n = 1 AND v_tt IS NULL THEN
    RAISE EXCEPTION '1357: bg_prashna_rules target_table update did not take (still NULL)';
  END IF;
END
$post$;
