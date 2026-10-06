-- 1324_bg_doshas_citation_pass2_integrity_reseal.sql
--
-- APPLY ORDER (SS ruling 2026-10-05; nothing queues before RELEASE + Pravaha's 90 minutes; rebuilds wait for S-L2):
--   (1) rebuild bg_doshas via the dispatch tool (accept bg_yogas, bg_dasha_systems and bg_ontology showing stale: they share the grp_brahma_ontology fingerprint this rebuild moves);
--   (2) rebuild bg_ontology in the DEFAULT (unchanged-content) mode; it has NO expected-change file (the rows already moved in step 1);
--   (3) rebuild ga_structural in the L1 refresh pass BEFORE the L2 refresh, so no dosha_label fact points at a removed catalog id when L2 reads it.
--   Merge order of the three citation PRs is free (the shared overlay files are byte-identical in the doshas and ontology branches).
--
-- CITATION-PASS2, role W4 (owner order; decision OS-2026-10-05-CITATIONS, ACHARYA/CITATION_PASS2/PASS2_DECISIONS.tsv): the bg_doshas seed
-- (platform/python-sidecar/brahmagyan/l0_doshas.py + citation_pass2_doshas.py) now removes 13 dosha definitions (the 12 Kala Sarpa named variants and vish_dosha, merged into
-- punarphoo), renames kemadruma_compat_kuja to kuja_dosha_from_venus and rewrites the citation / school / content of 40 others, so each of the three projections the writer owns
-- (brahma_dosha_catalog, brahma_ontology[entity_class=dosha], reference_doshas) holds 66 rows, not 79. This migration RE-SEALS asset_registry.integrity_check_sql, target_floor and
-- volume_explanation of bg_doshas to that state. ONE md5-guarded UPDATE of ONE asset_registry row; no data row is read or changed here (rows change only when the governed rebuild
-- replays the writer, via the dispatch tool's expected-change mode: 00_ARCHITECTURE/control/expected_change/EXPECTED_CHANGE_bg_doshas_citation_pass2.json). Transaction ownership
-- belongs to platform/scripts/migrate.ts (no BEGIN/COMMIT here). Data-only: no table or function is created or altered.
--
-- NUMBER. The allotment 1300-1302 was stale (main already carries 1300, 1301, 1302); 1306 (bg_remedies), 1324 (this) and 1308 (bg_ontology) sit above W5's 1303-1305.
--
-- WHAT CHANGES IN THE CHECK (and nothing else; a static test proves NEW = OLD with exactly these seven replacements): the four row-count terms 79 -> 66 (catalog, ontology dosha
-- partition, reference_doshas, and the empty-array count), and the three content hashes (catalog, ontology dosha partition, reference_doshas). The FULL JOIN consistency term is
-- unchanged (it still compares the three projections' names and categories). The new pins were measured by replaying the REAL writer (seed_doshas) on a disposable local PostgreSQL;
-- the same replay of origin/main's seed reproduces migration 692's old pins exactly (79 rows, hashes cfb21a53..., ee5dedf6..., 3fd442d6...), so the method is the one that produced the live pins:
--   catalog   308ce2a6048c488eefcea3abe8fa9c9c90d383981f9133b667614ac31d94628b
--   ontology  ed74d67afa450fdbcc22940a155243e2dbd72a78bbc7f4c16585330de0cae72d
--   reference 29ff924c2627ff1d9f1f3036188249351ba51a46ef99757d3c271e55dd2c86b7
-- Registry fields: target_floor 237 -> 198 (66 x 3), volume_explanation reworded; count_sql is unchanged (it sums the three tables).
--
--   OLD (migration 692's check, = migration 622's with the join-scope fix; md5 681d6b26ff4e5816a3f08650cdb76b4b, 2206 chars)
--   NEW (md5 e4baff75780519cc4fdf76b6ce27c9fd, 2206 chars)
--
-- GUARD AND WHAT HAPPENS WHEN IT DOES NOT MATCH (precedents 1259, 1297, 1299). The UPDATE only replaces the exact OLD text (and the exact floor 237). A different live text matches 0
-- rows and the migration is a NOTICE-and-NO-OP (the NOTICE names the md5 found); if the live text already equals NEW it is an idempotent no-op that does not fire the trigger. The one
-- case that RAISES: the post-check finds the row still carrying the OLD md5 (the UPDATE silently did nothing; never trust a silent no-op, CLAUDE.md N.4 / Trap 103). NOT verified against
-- production here (no production access): the live md5 of bg_doshas.integrity_check_sql must be read as suvarna_reader after the deploy.
--
-- ORDER OF OPERATIONS. Applying this makes the check expect 66 rows and the new hashes while the live tables still hold 79, so the check reads FALSE until the governed rebuild
-- of bg_doshas runs (replay-verified TRUE afterwards). The ontology dosha partition is written by THIS writer, not by bg_ontology's, so one bg_doshas rebuild moves brahma_ontology
-- from 741 to 728 rows; migration 1308 re-seals bg_ontology's own floor for that.
--
-- SIDE EFFECT ON bg_parihara_rules (found by review; RESOLVED by SS 2026-10-05, no reseal): that writer reads brahma_dosha_catalog.classical_citations. The K1 source pass 2 verified for 14 doshas covers each
-- dosha's DEFINITION, not its cancellation conditions, so bg_parihara_rules declares those 14 out of its graph (PARIHARA_K1_SOURCE_CHECK_PENDING, 'source check pending') and ignores K1_ANALOGUE objects:
-- its row set stays the IDENTICAL 60 rows and migration 703's pin (count = 60 + content hash) is untouched. The 27 would-be rows are in ACHARYA/PARIHARA_27_PENDING.tsv for review.
--
-- SERVING EFFECT AT APPLY (binding for every migration PR). UPDATE of integrity_check_sql / target_floor fires the live trigger nirmana_registry_receipt_invalidation (migration 596;
-- WHEN old.* IS DISTINCT FROM new.*): it sets asset_freshness.freshness_state = 'stale' (reason registry_changed) WHERE asset_id = NEW.asset_id. bg_doshas' freshness rows go stale until
-- the rebuild writes fresh receipts; no other asset is touched. A re-run updates 0 rows and does not fire it.
--
-- VERIFICATION BY PRODUCTION STRUCTURE (Trap 103). After the deploy, expect md5 e4baff75780519cc4fdf76b6ce27c9fd, length 2206, target_floor 198:
--   SELECT asset_id, md5(integrity_check_sql), length(integrity_check_sql), target_floor FROM asset_registry WHERE asset_id = 'bg_doshas';
--
-- ROLLBACK (not executed by migrate.ts): UPDATE asset_registry SET integrity_check_sql = <migration 692's check>, target_floor = 237, volume_explanation = <migration 622's canonical_explanation>
-- WHERE asset_id = 'bg_doshas' AND md5(integrity_check_sql) = 'e4baff75780519cc4fdf76b6ce27c9fd'; (fires the same trigger; only meaningful together with restoring the 13 removed seed rows).

SET LOCAL lock_timeout = '5s';

DO $pre$
DECLARE v_n int; v_md5 text; v_floor bigint;
BEGIN
  SELECT count(*), max(md5(integrity_check_sql)), max(target_floor) INTO v_n, v_md5, v_floor FROM asset_registry WHERE asset_id = 'bg_doshas';
  IF v_n = 0 THEN
    RAISE NOTICE '1324: no bg_doshas registry row (empty registry); nothing to do';
  ELSIF v_md5 = 'e4baff75780519cc4fdf76b6ce27c9fd' THEN
    RAISE NOTICE '1324: bg_doshas integrity_check_sql already carries the citation-pass-2 pins; nothing to do';
  ELSIF v_md5 IS DISTINCT FROM '681d6b26ff4e5816a3f08650cdb76b4b' OR v_floor IS DISTINCT FROM 237 THEN
    RAISE NOTICE '1324: bg_doshas integrity_check_sql / target_floor is not the state this migration was written against (md5 %, floor %); NO-OP, left as is', v_md5, v_floor;
  END IF;
END
$pre$;

UPDATE asset_registry
   SET target_floor = 198,
       volume_explanation = '198 owned rows = 66 deterministic dosha definitions × 3 reconciled projections (catalog + dosha ontology partition + reference_doshas). Citation pass 2 (OS-2026-10-05-CITATIONS) removed 13 definitions: the 12 Kala Sarpa named variants and vish_dosha (merged into punarphoo).',
       integrity_check_sql = $ic$
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
    '308ce2a6048c488eefcea3abe8fa9c9c90d383981f9133b667614ac31d94628b'
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
   AND target_floor = 237
   AND md5(integrity_check_sql) = '681d6b26ff4e5816a3f08650cdb76b4b';

DO $post$
DECLARE v_md5 text;
BEGIN
  SELECT max(md5(integrity_check_sql)) INTO v_md5 FROM asset_registry WHERE asset_id = 'bg_doshas';
  IF v_md5 = '681d6b26ff4e5816a3f08650cdb76b4b' THEN
    RAISE EXCEPTION '1324: bg_doshas integrity_check_sql still carries the OLD md5 681d6b26ff4e5816a3f08650cdb76b4b (update did not take)';
  END IF;
END
$post$;
