-- 1325_bg_ontology_citation_pass2_integrity_reseal.sql
--
-- APPLY ORDER (SS ruling 2026-10-05; nothing queues before RELEASE + Pravaha's 90 minutes; rebuilds wait for S-L2):
--   (1) rebuild bg_doshas via the dispatch tool (accept bg_yogas, bg_dasha_systems and bg_ontology showing stale: they share the grp_brahma_ontology fingerprint this rebuild moves);
--   (2) rebuild bg_ontology in the DEFAULT (unchanged-content) mode; it has NO expected-change file (the rows already moved in step 1);
--   (3) rebuild ga_structural in the L1 refresh pass BEFORE the L2 refresh, so no dosha_label fact points at a removed catalog id when L2 reads it.
--   Merge order of the three citation PRs is free (the shared overlay files are byte-identical in the doshas and ontology branches).
--
-- CITATION-PASS2, role W4 (owner order; decision OS-2026-10-05-CITATIONS, ACHARYA/CITATION_PASS2/PASS2_DECISIONS.tsv): the dosha seed (platform/python-sidecar/brahmagyan/l0_doshas.py +
-- citation_pass2_doshas.py) removes 13 dosha nodes from brahma_ontology (the 12 Kala Sarpa named variants and vish_dosha) and re-cites / corrects the 40 others, so the shared ontology table
-- moves from 741 to 728 rows. bg_ontology's integrity check carries a FLOOR on the whole table (migration 606: COUNT(*) >= 737), which 728 would violate; this migration lowers that one term
-- to 728 and the registry floor and volume text with it. ONE md5-guarded UPDATE of ONE asset_registry row; no data row is read or changed here. Transaction ownership belongs to
-- platform/scripts/migrate.ts (no BEGIN/COMMIT here). Data-only: no table or function is created or altered.
--
-- WHO WRITES THE CHANGED ROWS. The entity_class='dosha' partition of brahma_ontology is written by the bg_doshas writer (seed_doshas), not by bg_ontology's own writer (l0_ontology.seed_ontology
-- treats 'dosha', 'yoga' and 'dasha_system' as co-writer classes: ON CONFLICT DO NOTHING, never deleted). So the 13 deletions and 40 edits land when bg_doshas is rebuilt (its fingerprint unit
-- includes the shared brahma_ontology); a bg_ontology rebuild alone changes nothing in them. Use the DEFAULT (unchanged-content) mode for a bg_ontology rebuild AFTER the bg_doshas rebuild.
-- There is NO expected-change file for bg_ontology: its changed rows move in the bg_doshas rebuild, so a bg_ontology expected-change dispatch could never be MET (SS 2026-10-05); rebuild it in the default mode afterwards.
--
-- NUMBER. The allotment 1300-1302 was stale (main already carries 1300, 1301, 1302); 1306 (bg_remedies), 1307 (bg_doshas) and 1325 (this) sit above W5's 1303-1305.
--
-- WHAT CHANGES IN THE CHECK (nothing else; a static test proves NEW = OLD with exactly this one replacement): `(SELECT COUNT(*) >= 737 FROM brahma_ontology)` becomes `>= 728`. The floor
-- is the achieved count after the bg_doshas rebuild (floors are aspirational, CLAUDE.md N.4: never a number the corpus does not hold). 741 is the production total read in the R4 Ldgr census
-- (E5.7/R4_LDGR_CLASSES_AND_CARRIAGE_PROPOSAL.md: bg_ontology.source_citation 688/741 rows); 741 - 13 = 728. NOT verified against production here (no production access): the guard below
-- makes a different live text a NOTICE-and-no-op, and the live total must be read after the bg_doshas rebuild. Every other conjunct (the four closed classical sets, the NOT NULL columns, the
-- uniqueness term) is BYTE-IDENTICAL.
--
--   OLD (migration 606's ontology_check; md5 5fc7ea8d12969043a8258696cebcc1bc, 1756 chars)
--   NEW (md5 dad6e9189baa2ccda4579aaf36e07bad, 1756 chars)
--
-- GUARD AND WHAT HAPPENS WHEN IT DOES NOT MATCH (precedents 1259, 1297, 1299). The UPDATE only replaces the exact OLD text (and the exact floor 737). A different live text matches 0 rows and the
-- migration is a NOTICE-and-NO-OP (the NOTICE names the md5 found); if the live text already equals NEW it is an idempotent no-op that does not fire the trigger. The one case that RAISES: the
-- post-check finds the row still carrying the OLD md5 (the UPDATE silently did nothing; never trust a silent no-op, CLAUDE.md N.4 / Trap 103).
--
-- ORDER OF OPERATIONS. Safe in either order with the bg_doshas rebuild: before it the live total (741) satisfies `>= 728`; after it the total (728) does too.
--
-- SERVING EFFECT AT APPLY (binding for every migration PR). UPDATE of integrity_check_sql / target_floor fires the live trigger nirmana_registry_receipt_invalidation (migration 596; WHEN old.* IS
-- DISTINCT FROM new.*): it sets asset_freshness.freshness_state = 'stale' (reason registry_changed) WHERE asset_id = NEW.asset_id. bg_ontology's freshness rows go stale until its next build writes
-- fresh receipts; no other asset is touched. A re-run updates 0 rows and does not fire it.
--
-- VERIFICATION BY PRODUCTION STRUCTURE (Trap 103). After the deploy, expect md5 dad6e9189baa2ccda4579aaf36e07bad, length 1756, target_floor 728:
--   SELECT asset_id, md5(integrity_check_sql), length(integrity_check_sql), target_floor FROM asset_registry WHERE asset_id = 'bg_ontology';
--
-- ROLLBACK (not executed by migrate.ts): UPDATE asset_registry SET integrity_check_sql = <migration 606's ontology_check>, target_floor = 737, volume_explanation = <migration 606's ontology_explanation>
-- WHERE asset_id = 'bg_ontology' AND md5(integrity_check_sql) = 'dad6e9189baa2ccda4579aaf36e07bad'; (fires the same trigger).

SET LOCAL lock_timeout = '5s';

DO $pre$
DECLARE v_n int; v_md5 text; v_floor bigint;
BEGIN
  SELECT count(*), max(md5(integrity_check_sql)), max(target_floor) INTO v_n, v_md5, v_floor FROM asset_registry WHERE asset_id = 'bg_ontology';
  IF v_n = 0 THEN
    RAISE NOTICE '1325: no bg_ontology registry row (empty registry); nothing to do';
  ELSIF v_md5 = 'dad6e9189baa2ccda4579aaf36e07bad' THEN
    RAISE NOTICE '1325: bg_ontology integrity_check_sql already carries the citation-pass-2 floor; nothing to do';
  ELSIF v_md5 IS DISTINCT FROM '5fc7ea8d12969043a8258696cebcc1bc' OR v_floor IS DISTINCT FROM 737 THEN
    RAISE NOTICE '1325: bg_ontology integrity_check_sql / target_floor is not the state this migration was written against (md5 %, floor %); NO-OP, left as is', v_md5, v_floor;
  END IF;
END
$pre$;

UPDATE asset_registry
   SET target_floor = 728,
       volume_explanation = '728 achieved ontology rows in the authoritative production corpus (741 before citation pass 2, OS-2026-10-05-CITATIONS, removed the 13 dosha nodes the bg_doshas writer owns); closed classical sets are enforced by integrity SQL while extensible classes may grow.',
       integrity_check_sql = $ic$
SELECT
  (SELECT COUNT(*) >= 728 FROM brahma_ontology)
  AND (SELECT ARRAY_AGG(canonical_id ORDER BY canonical_id) = ARRAY[
    'nak_01_ashwini','nak_02_bharani','nak_03_krittika','nak_04_rohini','nak_05_mrigasira',
    'nak_06_ardra','nak_07_punarvasu','nak_08_pushya','nak_09_ashlesha','nak_10_magha',
    'nak_11_purva_phalguni','nak_12_uttara_phalguni','nak_13_hasta','nak_14_chitra',
    'nak_15_swati','nak_16_vishakha','nak_17_anuradha','nak_18_jyeshtha','nak_19_moola',
    'nak_20_purva_ashadha','nak_21_uttara_ashadha','nak_22_shravana','nak_23_dhanishtha',
    'nak_24_shatabhisha','nak_25_purva_bhadrapada','nak_26_uttara_bhadrapada','nak_27_revati'
  ]::text[] FROM brahma_ontology WHERE entity_class='nakshatra')
  AND (SELECT ARRAY_AGG(canonical_id ORDER BY canonical_id) = ARRAY[
    'aquarius','aries','cancer','capricorn','gemini','leo','libra','pisces','sagittarius','scorpio','taurus','virgo'
  ]::text[] FROM brahma_ontology WHERE entity_class='sign')
  AND (SELECT ARRAY_AGG(canonical_id ORDER BY canonical_id) = ARRAY[
    'house_01','house_02','house_03','house_04','house_05','house_06',
    'house_07','house_08','house_09','house_10','house_11','house_12'
  ]::text[] FROM brahma_ontology WHERE entity_class='house')
  AND (SELECT ARRAY_AGG(canonical_id ORDER BY canonical_id) = ARRAY[
    'ascendant','jupiter','ketu','mars','mercury','midheaven','moon','rahu','saturn','sun','venus'
  ]::text[] FROM brahma_ontology WHERE entity_class='planet')
  AND NOT EXISTS (
    SELECT 1 FROM brahma_ontology
    WHERE canonical_id IS NULL OR canonical_name_en IS NULL OR entity_class IS NULL OR source_citation IS NULL
  )
  AND NOT EXISTS (
    SELECT 1 FROM brahma_ontology GROUP BY entity_class, canonical_id HAVING COUNT(*) > 1
  )
$ic$
 WHERE asset_id = 'bg_ontology'
   AND target_floor = 737
   AND md5(integrity_check_sql) = '5fc7ea8d12969043a8258696cebcc1bc';

DO $post$
DECLARE v_md5 text;
BEGIN
  SELECT max(md5(integrity_check_sql)) INTO v_md5 FROM asset_registry WHERE asset_id = 'bg_ontology';
  IF v_md5 = '5fc7ea8d12969043a8258696cebcc1bc' THEN
    RAISE EXCEPTION '1325: bg_ontology integrity_check_sql still carries the OLD md5 5fc7ea8d12969043a8258696cebcc1bc (update did not take)';
  END IF;
END
$post$;
