-- Migration 1322: reseal bg_yogas' catalog content pin after Citation Pass 2 (decision OS-2026-10-05-CITATIONS;
-- PASS2_DECISIONS.tsv, one row: brahma_yoga_catalog canonical_id = kala_sarpa_yoga).
--
-- DATA (seed edit, platform/python-sidecar/brahmagyan/l0_yogas.py, written by the next governed rebuild of bg_yogas): the row kala_sarpa_yoga had
-- classical_citations = [{"text_id": "classical_tradition"}] (a bare tradition label, not a citation). Pass 2 found no classical locus in 16 texts and
-- decided: classical_citations = one K2 object (modern practice / project judgment, ratified OS-2026-10-05-CITATIONS), school = 'modern', and a note in
-- cancellation_conditions that the relation duplicates the dosha-form kala_sarpa and is not fired by ga_yoga_writer (R6A.2). No row is added or removed
-- (233 / 233 / 233 unchanged) and no other column of any other row changes. (Retiring the relation is recommended to the yoga-catalog owner, not done.)
--
-- WHY THIS RESEAL IS COMPUTED IN SQL: the catalog pin hashes ALL 233 rows, of which only the inline and detector rows come from this repository; the rest are
-- extracted from the corpus held in the database, so the new hash cannot be derived offline from the seed alone. This migration therefore derives it from the
-- live table, under a precondition that makes the derivation exact: it only runs while the live catalog hashes to the pin sealed by migration 701 (so the live
-- content is VERIFIED identical to the sealed content), and the new pin is the hash of that same content with the ONE decided substitution applied to the
-- ONE row (kala_sarpa_yoga: school, cancellation_conditions, classical_citations; every other column and row as stored). That is by construction what a
-- rebuild that reproduces the other 232 rows writes. tests/l0/test_citation_pass2_yogas.py proves the equivalence on a disposable Postgres: the pin this
-- migration writes equals the hash of the catalog after the real seed runs with the new row.
--
-- WHAT IT DOES (registry metadata only; the reseal pattern of 701 / 1078 / 1221): replaces the catalog pin inside bg_yogas' stored integrity_check_sql
-- (the old pin must occur exactly once; the counts, the ontology pin, the reference pin and the join check are untouched). IDEMPOTENT. A state it cannot
-- classify (the live catalog is neither the sealed pre-state nor the decided post-state, or the stored text no longer carries the sealed pin) is NOT
-- overwritten: the migration raises a WARNING and changes nothing, so an unrelated drift never blocks a deploy; the stored check then keeps describing the
-- last sealed state and the rebuild's own post-write check reports it.
--
-- RUNBOOK GATE (the skip paths below leave the pin as stored, and migrate.ts records the migration as applied, so it never re-runs: only a NEW migration
-- would repair a stale pin). BEFORE the deploy that carries this migration, confirm READ-ONLY that the live catalog hashes to the old pin:
--   SELECT encode(sha256(convert_to(COALESCE(string_agg(jsonb_build_array(canonical_id,name_sa,name_en,category,formation_rule_jsonb,formation_text,
--     significations_jsonb,significations_text,cancellation_conditions,classical_citations,source_chunk_ids,school,rare,computed_strength_formula,
--     bhanga_rules_jsonb,partial_formation_threshold,strength_formula_ref,result_class)::text, E'\n' ORDER BY canonical_id COLLATE "C"),''),'UTF8')),'hex')
--     FROM brahma_yoga_catalog;     -- expect 4d4cd60f7cffe728f2d01c3146f9bf54279e5c747973ab60b2e69b7921023fa8
-- (if it does not, STOP and ask: the migration would skip with a WARNING and the pin would stay stale). AFTER the governed rebuild, REQUIRE the stored
-- integrity check to return t (SELECT integrity_check_sql FROM asset_registry WHERE asset_id = 'bg_yogas' \gexec); a stored check that reads FALSE after the
-- rebuild means the migration skipped or the rebuild differs from the decided change: loud by design, never silently disabled.
--
-- SERVING EFFECT AT APPLY (binding for every migration PR). `UPDATE ... SET integrity_check_sql` fires the live trigger
-- nirmana_registry_receipt_invalidation (migration 596): AFTER UPDATE OF depends_on, natural_key_partition, health_probe, integrity_check_sql,
-- target_floor, asset_kind, asset_type, scope, has_writer, is_active, target_table, FOR EACH ROW WHEN (old.* IS DISTINCT FROM new.*), function
-- nirmana_invalidate_registry_receipts(), which sets asset_freshness.freshness_state = 'stale' (reason registry_changed) WHERE asset_id = NEW.asset_id.
-- So applying this STALES bg_yogas' asset_freshness rows (whatever rows exist for that asset id); the rebuild that follows writes fresh receipts.
-- No other asset is touched. A skip or a re-run updates nothing and does not fire the trigger.
--
-- ORDER: apply this migration, then run the governed rebuild of bg_yogas (dispatch tool, expected-change mode). Until the rebuild runs the stored check
-- reads FALSE (the pin describes rows not yet written); do NOT rebuild first. 701 is applied and never edited (CLAUDE.md N.4).
-- Transaction ownership belongs to platform/scripts/migrate.ts.

SET LOCAL lock_timeout = '5s';

DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  old_pin constant text := '4d4cd60f7cffe728f2d01c3146f9bf54279e5c747973ab60b2e69b7921023fa8';
  live_hash text;
  post_hash text;
  new_pin text;
  hits integer;
BEGIN
  SELECT * INTO registry_row FROM asset_registry WHERE asset_id = 'bg_yogas' FOR UPDATE;
  IF NOT FOUND OR registry_row.integrity_check_sql IS NULL THEN
    RAISE EXCEPTION 'migration 1322 refuses: bg_yogas has no registry row / no integrity_check_sql';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM brahma_yoga_catalog WHERE canonical_id = 'kala_sarpa_yoga') THEN
    RAISE NOTICE 'migration 1322 skipped: brahma_yoga_catalog has no kala_sarpa_yoga row (an empty L0 catalog); nothing to reseal';
    RETURN;
  END IF;

  SELECT encode(sha256(convert_to(COALESCE(string_agg(
           jsonb_build_array(canonical_id,name_sa,name_en,category,formation_rule_jsonb,formation_text,significations_jsonb,significations_text,cancellation_conditions,classical_citations,source_chunk_ids,school,rare,computed_strength_formula,bhanga_rules_jsonb,partial_formation_threshold,strength_formula_ref,result_class)::text,
           E'\n' ORDER BY canonical_id COLLATE "C"),''),'UTF8')),'hex')
    INTO live_hash
    FROM brahma_yoga_catalog;

  -- the same aggregate with the one decided substitution applied to the one row
  SELECT encode(sha256(convert_to(COALESCE(string_agg(
           jsonb_build_array(canonical_id,name_sa,name_en,category,formation_rule_jsonb,formation_text,significations_jsonb,significations_text,cancellation_conditions,classical_citations,source_chunk_ids,school,rare,computed_strength_formula,bhanga_rules_jsonb,partial_formation_threshold,strength_formula_ref,result_class)::text,
           E'\n' ORDER BY canonical_id COLLATE "C"),''),'UTF8')),'hex')
    INTO post_hash
    FROM (
      SELECT canonical_id, name_sa, name_en, category, formation_rule_jsonb, formation_text, significations_jsonb, significations_text,
             CASE WHEN canonical_id = 'kala_sarpa_yoga'
                  THEN jsonb_set(COALESCE(cancellation_conditions, '{}'::jsonb), '{notes}', to_jsonb('duplicate of dosha kala_sarpa; not fired by ga_yoga_writer (R6A.2)'::text))
                  ELSE cancellation_conditions END AS cancellation_conditions,
             CASE WHEN canonical_id = 'kala_sarpa_yoga'
                  THEN '[{"kind": "K2", "decision_id": "OS-2026-10-05-CITATIONS", "label": "modern practice / project judgment", "note": "not a classical source; duplicate authority: ga_yoga_writer deliberately does not fire this relation; the dosha-form kala_sarpa in ga_structural_writer is the single authority (R6A.2)"}]'::jsonb
                  ELSE classical_citations END AS classical_citations,
             source_chunk_ids,
             CASE WHEN canonical_id = 'kala_sarpa_yoga' THEN 'modern' ELSE school END AS school,
             rare, computed_strength_formula, bhanga_rules_jsonb, partial_formation_threshold, strength_formula_ref, result_class
        FROM brahma_yoga_catalog
    ) AS after_rows;

  hits := (length(registry_row.integrity_check_sql) - length(replace(registry_row.integrity_check_sql, old_pin, ''))) / length(old_pin);
  IF hits = 1 THEN
    IF live_hash = old_pin THEN
      new_pin := post_hash;               -- the live catalog IS the sealed pre-state: the stored pin moves to the decided post-state
    ELSIF live_hash = post_hash THEN
      new_pin := live_hash;               -- the catalog was already rebuilt before the reseal: the stored pin catches up
    ELSE
      RAISE WARNING 'migration 1322 skipped: the live brahma_yoga_catalog is neither the content sealed by migration 701 nor that content with the decided kala_sarpa_yoga change; bg_yogas integrity_check_sql left as stored';
      RETURN;
    END IF;
    UPDATE asset_registry SET integrity_check_sql = replace(integrity_check_sql, old_pin, new_pin) WHERE asset_id = 'bg_yogas';
  ELSIF hits = 0 AND position(post_hash IN registry_row.integrity_check_sql) > 0 THEN
    RETURN;                               -- already resealed
  ELSE
    RAISE WARNING 'migration 1322 skipped: the stored bg_yogas integrity_check_sql carries the sealed catalog pin % times (expected once) and not the post-change pin; left as stored', hits;
    RETURN;
  END IF;

  IF NOT EXISTS (SELECT 1 FROM asset_registry WHERE asset_id = 'bg_yogas' AND position(old_pin IN integrity_check_sql) = 0 AND position(new_pin IN integrity_check_sql) > 0) THEN
    RAISE EXCEPTION 'migration 1322 postflight mismatch';
  END IF;
END $$;

-- VERIFY (after the rebuild): SELECT integrity_check_sql FROM asset_registry WHERE asset_id = 'bg_yogas' \gexec  -- expect t
--   SELECT school, classical_citations->0->>'kind' FROM brahma_yoga_catalog WHERE canonical_id = 'kala_sarpa_yoga';  -- expect modern | K2
-- DOWN (manual): replace(integrity_check_sql, <new pin>, '4d4cd60f7cffe728f2d01c3146f9bf54279e5c747973ab60b2e69b7921023fa8').
