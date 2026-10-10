-- 1361_bg_doshas_formation_rule_one_spelling_family_reseal.sql
--
-- APPLY ORDER (rebuilds are governed, nothing here queues one):
--   (1) merge + deploy this migration AFTER 1324 (it only matches the state 1324 leaves: md5 e4baff75780519cc4fdf76b6ce27c9fd, target_floor 198);
--   (2) rebuild bg_doshas via the dispatch tool in expected-change mode (00_ARCHITECTURE/control/expected_change/EXPECTED_CHANGE_bg_doshas_formation_spelling.json);
--   (3) THEN rebuild bg_ontology (default, unchanged-content mode): the bg_doshas rebuild moves the shared grp_brahma_ontology fingerprint, so bg_ontology (and bg_yogas, bg_dasha_systems)
--       read stale until it is rebuilt AFTER bg_doshas, never before;
--   (4) ga_structural does NOT need a rebuild for this change: no dosha_label fact carries the rule (the L1 evaluator reads only requires[].planet, case-insensitively via .title(); see the PR trace).
--
-- WHAT THIS IS. The Vocab.alias census cell of bg_doshas (brahma_dosha_catalog.formation_rule_jsonb) read MIXED canonical spelling families: the graha leaves were lowercase ontology ids
-- ("planet":"mars", "reference":["lagna","moon","venus"], "conjunction":["moon","rahu"]) while the nakshatra leaves were display names, six of them non-canonical-but-registered aliases
-- (Ashvini, Mrigashira, Mula, Svati, Uttaraphalguni, Uttarashadha) and four unrecognised spellings (Purvaphalguni, Purvashadha, Purvabhadrapada, Uttarabhadrapada). The seed
-- (platform/python-sidecar/brahmagyan/l0_doshas.py + citation_pass2_doshas.py) now writes ONE family, the display names the L1 facts use: Sun Moon Mars Mercury Jupiter Venus Saturn Rahu Ketu Lagna
-- (brahmagyan/graha_vocabulary released canonical labels) and the bg_ontology canonical_name_en of each nakshatra (Ashwini, Mrigasira, Moola, Swati, Uttara Phalguni, Uttara Ashadha,
-- Purva Phalguni, Purva Ashadha, Purva Bhadrapada, Uttara Bhadrapada). Only string LEAVES change (25 of the 66 rows); no JSON key, no other column, no row count changes.
-- The bg_doshas integrity check hashes formation_rule_jsonb (catalog content hash), so its pin moves; this migration RE-SEALS asset_registry.integrity_check_sql of bg_doshas.
-- ONE md5-guarded UPDATE of ONE asset_registry row; no data row is read or changed here (rows change only when the governed rebuild replays the writer). Transaction ownership belongs to
-- platform/scripts/migrate.ts (no BEGIN/COMMIT here). Data-only: no table or function is created or altered.
--
-- NUMBER. 1361: highest on main is 1349; open PRs claim up to 1356; 1357, 1358 and 1360 are taken by other workers (re-checked before opening).
--
-- WHAT CHANGES IN THE CHECK (and nothing else; a static test proves NEW = OLD with exactly this one replacement): the catalog content hash
--   OLD 308ce2a6048c488eefcea3abe8fa9c9c90d383981f9133b667614ac31d94628b  (migration 1324)
--   NEW 5c5182366bdfcc36e5f56951ba3eedbf9a2b527d5d02875ddf8a12d162c9dc7e
-- The ontology dosha-partition hash (ed74d67a...) and the reference_doshas hash (29ff924c...) and the 66-row counts are UNCHANGED (the ontology / reference projections carry no formation rule).
-- The new pin was measured by replaying the REAL writer (seed_doshas) on a disposable local PostgreSQL, the method that produced migration 1324's pins (its replay of the previous seed
-- reproduces 308ce2a6...). target_floor (198) and volume_explanation are unchanged.
--
--   OLD (migration 1324's check; md5 e4baff75780519cc4fdf76b6ce27c9fd, 2206 chars)
--   NEW (md5 58a572d44f8baf80884e4e581dae7d7d, 2206 chars)
--
-- GUARD AND WHAT HAPPENS WHEN IT DOES NOT MATCH (precedents 1259, 1297, 1299, 1324). The UPDATE only replaces the exact OLD text (and the exact floor 198). A different live text matches 0 rows
-- and the migration is a NOTICE-and-NO-OP (the NOTICE names the md5 found); if the live text already equals NEW it is an idempotent no-op that does not fire the trigger. The case that RAISES:
-- the post-check finds the row still carrying the OLD md5 (the UPDATE silently did nothing; never trust a silent no-op, CLAUDE.md N.4 / Trap 103), or finds the NEW md5 without the new pin inside the text.
-- NOT verified against production here (no production access): the live md5 of bg_doshas.integrity_check_sql must be read as suvarna_reader after the deploy.
--
-- ORDER OF OPERATIONS. Applying this makes the check expect the new catalog hash while the live catalog still holds the old leaf spellings, so the check reads FALSE until the governed rebuild of
-- bg_doshas runs (replay-verified TRUE afterwards). If the rebuild of 1324's state has not run yet, run it from THIS seed (one rebuild reaches both states).
--
-- SERVING EFFECT AT APPLY (binding for every migration PR). UPDATE of integrity_check_sql fires the live trigger nirmana_registry_receipt_invalidation (migration 596; WHEN old.* IS DISTINCT FROM new.*):
-- it sets asset_freshness.freshness_state = 'stale' (reason registry_changed) WHERE asset_id = NEW.asset_id. bg_doshas' freshness rows go stale until the rebuild writes fresh receipts; no other asset
-- is touched. A re-run updates 0 rows and does not fire it. After the rebuild, ref_doshas_get / query_dosha_catalog (SELECT *) serve the new leaf spellings; no reader parses them (see the PR trace).
--
-- VERIFICATION BY PRODUCTION STRUCTURE (Trap 103). After the deploy, expect md5 58a572d44f8baf80884e4e581dae7d7d, length 2206, target_floor 198:
--   SELECT asset_id, md5(integrity_check_sql), length(integrity_check_sql), target_floor FROM asset_registry WHERE asset_id = 'bg_doshas';
--
-- ROLLBACK (not executed by migrate.ts): UPDATE asset_registry SET integrity_check_sql = <migration 1324's check> WHERE asset_id = 'bg_doshas' AND md5(integrity_check_sql) = '58a572d44f8baf80884e4e581dae7d7d';
-- (fires the same trigger; only meaningful together with restoring the previous seed leaves).

SET LOCAL lock_timeout = '5s';

DO $pre$
DECLARE v_n int; v_md5 text; v_floor bigint;
BEGIN
  SELECT count(*), max(md5(integrity_check_sql)), max(target_floor) INTO v_n, v_md5, v_floor FROM asset_registry WHERE asset_id = 'bg_doshas';
  IF v_n = 0 THEN
    RAISE NOTICE '1361: no bg_doshas registry row (empty registry); nothing to do';
  ELSIF v_md5 = '58a572d44f8baf80884e4e581dae7d7d' THEN
    RAISE NOTICE '1361: bg_doshas integrity_check_sql already carries the one-spelling-family catalog pin; nothing to do';
  ELSIF v_md5 IS DISTINCT FROM 'e4baff75780519cc4fdf76b6ce27c9fd' OR v_floor IS DISTINCT FROM 198 THEN
    RAISE NOTICE '1361: bg_doshas integrity_check_sql / target_floor is not the state this migration was written against (md5 %, floor %); NO-OP, left as is', v_md5, v_floor;
  END IF;
END
$pre$;

UPDATE asset_registry
   SET integrity_check_sql = $ic$
SELECT
  (SELECT count(*) = 66 FROM brahma_dosha_catalog)
  AND (SELECT count(*) = 66 FROM brahma_ontology WHERE entity_class='dosha')
  AND (SELECT count(*) = 66 FROM reference_doshas)
  AND (SELECT count(*) FILTER (WHERE cardinality(source_chunk_ids)=0
    AND cardinality(associated_remedies)=0) = 66 FROM brahma_dosha_catalog)
  AND NOT EXISTS (
    SELECT 1 FROM brahma_dosha_catalog AS catalog
    FULL JOIN (SELECT * FROM brahma_ontology WHERE entity_class='dosha') AS ontology
      ON ontology.canonical_id=catalog.canonical_id
    FULL JOIN reference_doshas AS reference
      ON reference.canonical_id=COALESCE(catalog.canonical_id,ontology.canonical_id)
    WHERE catalog.canonical_id IS NULL OR ontology.canonical_id IS NULL
       OR reference.canonical_id IS NULL
       OR ontology.canonical_name_en IS DISTINCT FROM catalog.name_en
       OR ontology.canonical_name_sa IS DISTINCT FROM catalog.name_sa
       OR reference.name_en IS DISTINCT FROM catalog.name_en
       OR reference.category IS DISTINCT FROM catalog.category
  )
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(canonical_id,name_sa,name_en,category,formation_rule_jsonb,
      formation_text,effects_text,severity_grades,cancellation_conditions,
      classical_citations,source_chunk_ids,associated_remedies,school)::text,
    E'\n' ORDER BY canonical_id COLLATE "C"),''),'UTF8')),'hex') =
    '5c5182366bdfcc36e5f56951ba3eedbf9a2b527d5d02875ddf8a12d162c9dc7e'
   FROM brahma_dosha_catalog)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(entity_class,canonical_id,canonical_name_en,
      canonical_name_sa,synonyms,description,source_citation)::text,
    E'\n' ORDER BY entity_class COLLATE "C",canonical_id COLLATE "C"),''),'UTF8')),'hex') =
    'ed74d67afa450fdbcc22940a155243e2dbd72a78bbc7f4c16585330de0cae72d'
   FROM brahma_ontology WHERE entity_class='dosha')
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(canonical_id,name_en,category)::text,
    E'\n' ORDER BY canonical_id COLLATE "C"),''),'UTF8')),'hex') =
    '29ff924c2627ff1d9f1f3036188249351ba51a46ef99757d3c271e55dd2c86b7'
   FROM reference_doshas)
$ic$
 WHERE asset_id = 'bg_doshas'
   AND target_floor = 198
   AND md5(integrity_check_sql) = 'e4baff75780519cc4fdf76b6ce27c9fd';

DO $post$
DECLARE v_md5 text; v_text text;
BEGIN
  SELECT max(md5(integrity_check_sql)), max(integrity_check_sql) INTO v_md5, v_text FROM asset_registry WHERE asset_id = 'bg_doshas';
  IF v_md5 = 'e4baff75780519cc4fdf76b6ce27c9fd' THEN
    RAISE EXCEPTION '1361: bg_doshas integrity_check_sql still carries the OLD md5 e4baff75780519cc4fdf76b6ce27c9fd (update did not take)';
  END IF;
  IF v_md5 = '58a572d44f8baf80884e4e581dae7d7d' AND (position('5c5182366bdfcc36e5f56951ba3eedbf9a2b527d5d02875ddf8a12d162c9dc7e' IN v_text) = 0
                                                   OR position('308ce2a6048c488eefcea3abe8fa9c9c90d383981f9133b667614ac31d94628b' IN v_text) > 0) THEN
    RAISE EXCEPTION '1361: bg_doshas integrity_check_sql carries the NEW md5 but not exactly the new catalog pin';
  END IF;
END
$post$;
