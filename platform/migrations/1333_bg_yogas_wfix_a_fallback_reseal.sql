-- Migration 1333: reseal bg_yogas' catalog and ontology content pins after WFIX-A removed two invented fallback texts from the corpus-extracted yoga rows
-- (CLAUDE.md N.7 item 6: an honest value or null beats an invented judgment).
--
-- DATA (seed edit, platform/python-sidecar/brahmagyan/l0_yogas.py, written by the next governed rebuild of bg_yogas), on the corpus-extracted rows whose source
-- chunk names a yoga without a defining clause (4 live rows: vajra_sar, yava_sar, vapi_sar, kedara_sar; all four are structured-template rows):
--   brahma_yoga_catalog.formation_text   was f"{name_en}: formation per {verse_ref} ({text_id} Ch.{chapter})" -- a sentence that claims a formation "per" a
--                                        verse while stating none (and names the chapter of a different text than the yoga's). It is now a deterministic
--                                        restatement of the row's own structured rule: 'Structured formation rule: ' || formation_rule_jsonb (the column is NOT NULL).
--   brahma_yoga_catalog.significations_text  was the yoga's NAME when the chunk states no result (3 live rows: vajra_sar, yava_sar, vapi_sar). It is now the empty
--                                        string (the column is NOT NULL), never a label presented as a signification.
--   brahma_ontology.description          (= significations_text[:150]) of those 3 rows was the same name; it is now NULL (the column is nullable).
-- No row is added or removed (233 / 233 / 233 / 85 unchanged) and no other column of any row changes.
--
-- WHY THIS RESEAL IS COMPUTED IN SQL: the pins hash ALL 233 rows, of which only the inline and detector rows come from this repository; the rest are extracted
-- from the corpus held in the database, so the new hashes cannot be derived offline from the seed alone (the same reason migration 1322 computes its pin in SQL).
-- Each pin is handled independently, under a precondition that makes the derivation exact: the live table must hash to the pin currently stored (VERIFIED
-- identical to the sealed content), and the new pin is the hash of that same content with the ONE decided substitution applied to the rows the fallback wrote
-- (matched by the fallback's own shape: formation_text LIKE '%: formation per % (% Ch.%)' / significations_text = name_en), which is by construction what a
-- rebuild that reproduces every other row writes. Verified read-only against the live tables on 2026-10-08: the catalog hashes to the stored pin
-- eb57c4dee246fb3289c8ea66ea088efb292ef4d2506645bcfdd4acb6ca80ea4e and the substitution yields 3b59e019d9b241153cc493f682b88e96b3e25d72303bcf684e27d07dc99ac978;
-- the ontology hashes to 7af1d138c492bd16bbca93b06faab6b3ff781d87aa91f8573fce6378f968fdab and yields cb5bb743235c3a32482bcaaa5e7a4e8106b68e840ef7a468583e270a109eedab.
-- tests/l0/test_bg_yogas_wfix_a_reseal.py proves the equivalence on a disposable Postgres: the pins this migration writes equal the hashes of the tables after the
-- REAL seed runs with the new texts.
--
-- WHAT IT DOES (registry metadata only; the reseal pattern of 701 / 1078 / 1221 / 1322): replaces the catalog pin and the ontology pin inside bg_yogas' stored
-- integrity_check_sql (each old pin must occur exactly once; the counts, the reference pin and the join check are untouched). IDEMPOTENT. A state it cannot
-- classify (the live table is neither the sealed pre-state nor the decided post-state, or the stored text no longer carries the sealed pin) is NOT overwritten: the
-- migration raises a WARNING and changes nothing, so an unrelated drift never blocks a deploy; the stored check then keeps describing the last sealed state and
-- the rebuild's own post-write check reports it.
--
-- RUNBOOK GATE (the skip paths leave the pins as stored and migrate.ts records the migration as applied, so it never re-runs: only a NEW migration would repair a
-- stale pin). BEFORE the deploy that carries this migration, confirm READ-ONLY that the live catalog and ontology hash to the old pins (the two queries in the
-- stored integrity_check_sql, SELECT integrity_check_sql FROM asset_registry WHERE asset_id = 'bg_yogas' \gexec, must read t). AFTER the governed rebuild, REQUIRE the
-- same check to read t; f means the migration skipped or the rebuild differs from the decided change: loud by design, never silently disabled.
--
-- SERVING EFFECT AT APPLY (binding for every migration PR). `UPDATE ... SET integrity_check_sql` fires the live trigger nirmana_registry_receipt_invalidation
-- (migration 596): AFTER UPDATE OF depends_on, natural_key_partition, health_probe, integrity_check_sql, target_floor, asset_kind, asset_type, scope, has_writer,
-- is_active, target_table, FOR EACH ROW WHEN (old.* IS DISTINCT FROM new.*), function nirmana_invalidate_registry_receipts(), which sets
-- asset_freshness.freshness_state = 'stale' (reason registry_changed) WHERE asset_id = NEW.asset_id. So applying this STALES bg_yogas' asset_freshness rows; the
-- rebuild that follows writes fresh receipts. No other asset is touched. A skip or a re-run updates nothing and does not fire the trigger.
--
-- ORDER: apply this migration, then run the governed rebuild of bg_yogas (dispatch tool, expected-change mode). Until the rebuild runs the stored check reads FALSE
-- (the pins describe rows not yet written); do NOT rebuild first. 701 and 1322 are applied and never edited (CLAUDE.md N.4).
-- Transaction ownership belongs to platform/scripts/migrate.ts.

SET LOCAL lock_timeout = '5s';

DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  old_catalog_pin constant text := 'eb57c4dee246fb3289c8ea66ea088efb292ef4d2506645bcfdd4acb6ca80ea4e';
  old_ontology_pin constant text := '7af1d138c492bd16bbca93b06faab6b3ff781d87aa91f8573fce6378f968fdab';
  live_catalog text;
  post_catalog text;
  live_ontology text;
  post_ontology text;
  new_catalog_pin text;
  new_ontology_pin text;
  stored text;
  hits integer;
BEGIN
  SELECT * INTO registry_row FROM asset_registry WHERE asset_id = 'bg_yogas' FOR UPDATE;
  IF NOT FOUND OR registry_row.integrity_check_sql IS NULL THEN
    RAISE EXCEPTION 'migration 1333 refuses: bg_yogas has no registry row / no integrity_check_sql';
  END IF;
  stored := registry_row.integrity_check_sql;
  IF NOT EXISTS (SELECT 1 FROM brahma_yoga_catalog LIMIT 1) THEN
    RAISE NOTICE 'migration 1333 skipped: brahma_yoga_catalog is empty (an empty L0 catalog); nothing to reseal';
    RETURN;
  END IF;

  -- ── catalog ────────────────────────────────────────────────────────────────────────────────────
  SELECT encode(sha256(convert_to(COALESCE(string_agg(
           jsonb_build_array(canonical_id,name_sa,name_en,category,formation_rule_jsonb,formation_text,significations_jsonb,significations_text,cancellation_conditions,classical_citations,source_chunk_ids,school,rare,computed_strength_formula,bhanga_rules_jsonb,partial_formation_threshold,strength_formula_ref,result_class)::text,
           E'\n' ORDER BY canonical_id COLLATE "C"),''),'UTF8')),'hex')
    INTO live_catalog
    FROM brahma_yoga_catalog;

  -- the same aggregate with the decided substitution applied to the rows the fallback wrote
  SELECT encode(sha256(convert_to(COALESCE(string_agg(
           jsonb_build_array(canonical_id,name_sa,name_en,category,formation_rule_jsonb,formation_text,significations_jsonb,significations_text,cancellation_conditions,classical_citations,source_chunk_ids,school,rare,computed_strength_formula,bhanga_rules_jsonb,partial_formation_threshold,strength_formula_ref,result_class)::text,
           E'\n' ORDER BY canonical_id COLLATE "C"),''),'UTF8')),'hex')
    INTO post_catalog
    FROM (
      SELECT canonical_id, name_sa, name_en, category, formation_rule_jsonb,
             CASE WHEN formation_text LIKE '%: formation per % (% Ch.%)'
                  THEN 'Structured formation rule: ' || formation_rule_jsonb::text
                  ELSE formation_text END AS formation_text,
             significations_jsonb,
             CASE WHEN significations_text = name_en THEN '' ELSE significations_text END AS significations_text,
             cancellation_conditions, classical_citations, source_chunk_ids, school, rare, computed_strength_formula,
             bhanga_rules_jsonb, partial_formation_threshold, strength_formula_ref, result_class
        FROM brahma_yoga_catalog
    ) AS after_rows;

  -- ── ontology (entity_class = 'yoga') ───────────────────────────────────────────────────────────
  SELECT encode(sha256(convert_to(COALESCE(string_agg(
           jsonb_build_array(entity_class,canonical_id,canonical_name_en,canonical_name_sa,synonyms,description,source_citation)::text,
           E'\n' ORDER BY entity_class COLLATE "C",canonical_id COLLATE "C"),''),'UTF8')),'hex')
    INTO live_ontology
    FROM brahma_ontology WHERE entity_class = 'yoga';

  SELECT encode(sha256(convert_to(COALESCE(string_agg(
           jsonb_build_array(entity_class,canonical_id,canonical_name_en,canonical_name_sa,synonyms,description,source_citation)::text,
           E'\n' ORDER BY entity_class COLLATE "C",canonical_id COLLATE "C"),''),'UTF8')),'hex')
    INTO post_ontology
    FROM (
      SELECT o.entity_class, o.canonical_id, o.canonical_name_en, o.canonical_name_sa, o.synonyms,
             CASE WHEN o.canonical_id IN (SELECT c.canonical_id FROM brahma_yoga_catalog c WHERE c.significations_text = c.name_en)
                  THEN NULL ELSE o.description END AS description,
             o.source_citation
        FROM brahma_ontology o WHERE o.entity_class = 'yoga'
    ) AS after_rows;

  -- ── classify each pin independently ───────────────────────────────────────────────────────────
  hits := (length(stored) - length(replace(stored, old_catalog_pin, ''))) / length(old_catalog_pin);
  IF hits = 1 THEN
    IF live_catalog = old_catalog_pin THEN
      new_catalog_pin := post_catalog;      -- the live catalog IS the sealed pre-state: the stored pin moves to the decided post-state
    ELSIF live_catalog = post_catalog THEN
      new_catalog_pin := live_catalog;      -- the catalog was already rebuilt before the reseal: the stored pin catches up
    ELSE
      RAISE WARNING 'migration 1333 skipped: the live brahma_yoga_catalog is neither the sealed content nor that content with the decided fallback-text change; bg_yogas integrity_check_sql left as stored';
      RETURN;
    END IF;
  ELSIF hits = 0 AND position(post_catalog IN stored) > 0 THEN
    new_catalog_pin := NULL;                -- already resealed
  ELSE
    RAISE WARNING 'migration 1333 skipped: the stored bg_yogas integrity_check_sql carries the sealed catalog pin % times (expected once) and not the post-change pin; left as stored', hits;
    RETURN;
  END IF;

  hits := (length(stored) - length(replace(stored, old_ontology_pin, ''))) / length(old_ontology_pin);
  IF hits = 1 THEN
    IF live_ontology = old_ontology_pin THEN
      new_ontology_pin := post_ontology;
    ELSIF live_ontology = post_ontology THEN
      new_ontology_pin := live_ontology;
    ELSE
      RAISE WARNING 'migration 1333 skipped: the live yoga rows of brahma_ontology are neither the sealed content nor that content with the decided description change; bg_yogas integrity_check_sql left as stored';
      RETURN;
    END IF;
  ELSIF hits = 0 AND position(post_ontology IN stored) > 0 THEN
    new_ontology_pin := NULL;               -- already resealed
  ELSE
    RAISE WARNING 'migration 1333 skipped: the stored bg_yogas integrity_check_sql carries the sealed ontology pin % times (expected once) and not the post-change pin; left as stored', hits;
    RETURN;
  END IF;

  IF new_catalog_pin IS NULL AND new_ontology_pin IS NULL THEN
    RETURN;                                 -- fully resealed already: nothing to update, the trigger does not fire
  END IF;

  -- a pin that did not change (the substitution touched no row) must not rewrite the registry either
  IF COALESCE(new_catalog_pin, old_catalog_pin) = old_catalog_pin AND COALESCE(new_ontology_pin, old_ontology_pin) = old_ontology_pin THEN
    RETURN;
  END IF;

  UPDATE asset_registry
     SET integrity_check_sql = replace(replace(integrity_check_sql, old_catalog_pin, COALESCE(new_catalog_pin, old_catalog_pin)),
                                       old_ontology_pin, COALESCE(new_ontology_pin, old_ontology_pin))
   WHERE asset_id = 'bg_yogas';

  IF NOT EXISTS (
    SELECT 1 FROM asset_registry
     WHERE asset_id = 'bg_yogas'
       AND position(COALESCE(new_catalog_pin, post_catalog) IN integrity_check_sql) > 0
       AND position(COALESCE(new_ontology_pin, post_ontology) IN integrity_check_sql) > 0
  ) THEN
    RAISE EXCEPTION 'migration 1333 postflight mismatch';
  END IF;
END $$;

-- VERIFY (after the rebuild): SELECT integrity_check_sql FROM asset_registry WHERE asset_id = 'bg_yogas' \gexec  -- expect t
--   SELECT canonical_id, formation_text, significations_text FROM brahma_yoga_catalog WHERE canonical_id IN ('vajra_sar','yava_sar','vapi_sar','kedara_sar');
--     -- expect 'Structured formation rule: {...}' and '' (kedara_sar keeps its verbatim result sentence)
-- DOWN (manual): replace(integrity_check_sql, <new catalog pin>, 'eb57c4dee246fb3289c8ea66ea088efb292ef4d2506645bcfdd4acb6ca80ea4e') and
--   replace(integrity_check_sql, <new ontology pin>, '7af1d138c492bd16bbca93b06faab6b3ff781d87aa91f8573fce6378f968fdab').
