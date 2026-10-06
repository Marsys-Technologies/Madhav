-- 1323_bg_remedies_citation_pass2_integrity_reseal.sql
--
-- CITATION-PASS2, role W4 (owner order; decision OS-2026-10-05-CITATIONS, ACHARYA/CITATION_PASS2/PASS2_DECISIONS.tsv): the bg_remedies seed
-- (platform/python-sidecar/brahmagyan/l0_remedy_corpus.py + citation_pass2_remedies.py) now removes 25 unsourced remedy rows, so the
-- deterministic corpus is 316 rows, not 341. This migration RE-SEALS asset_registry.integrity_check_sql, target_floor and volume_explanation
-- of bg_remedies to that count. ONE md5-guarded UPDATE of ONE asset_registry row; no corpus row is read or changed here (the rows
-- change only when the governed rebuild replays the writer, via the dispatch tool's expected-change mode: file
-- 00_ARCHITECTURE/control/expected_change/EXPECTED_CHANGE_bg_remedies_citation_pass2.json). Transaction ownership belongs to
-- platform/scripts/migrate.ts (no BEGIN/COMMIT here). Data-only: no table or function is created or altered.
--
-- DELIBERATE, NOT A DEFECT (SS ruling 2026-10-05): mars_matrix_japa keeps its stored count of 10,000 and is flagged 'count under verification: corpus scan reads "I 1000" (10,000 or 11,000);
-- row keeps 10,000 until the page image is checked'; the K1 excerpt quotes the scan literally ('Mars I 1000'). Seed row text, not this migration; stated here so the review does not re-flag it.
--
-- NUMBER. The allotment 1300-1302 was stale (main already carries 1300, 1301, 1302); 1323 is the first free number above Worker A's
-- 1303-1305. migration_number_guard.ts holds the uniqueness.
--
-- WHAT CHANGES IN THE CHECK (and nothing else; a static test proves NEW = OLD with exactly these eight replacements):
--   total / distinct ids   341 -> 316          id_md5 '8bac868a1b9708eedee44a7266237d08' -> '476de921a54acbbfaae093a66121da48'
--   planet counts          sun 53->52, moon 50->46, mars 33->32, jupiter 40->37, venus 32->29, saturn 39->38, rahu 42->30 (mercury 26, ketu 26 unchanged)
--   domain counts          general 260->249, health 18->17, marriage 29->16 (the 11 kuta puja rows, vish_kanya_puja, and the Punarphoo row now 'general')
--   type counts            mantra 68->65, puja 76->54
--   uncategorized 256->231, live rows 302->277. Sweep (54: 15 live / 39 review), tantric (4), nakshatra (27), review (39) are UNCHANGED.
--   The not-blank conjuncts are unchanged: every surviving row still carries a non-blank source_canonical_id, source_citation and classical_ref.
-- The new pins were measured by replaying the REAL writer (seed_remedy_corpus + the tantric loader) on a disposable local PostgreSQL with
-- the 54-chunk source snapshot of the 608 contract test; the same replay with the overlay switched off reproduces migration 608's old pins
-- exactly (341 rows, id_md5 8bac868a..., the old planet/domain/type counts), so the method is the one that produced the live pins.
--
--   OLD (migration 608's remedy_check; md5 8c521f10b57f6b06eb1a73e49e0c6b25, 4601 chars)
--   NEW (md5 d1d7fecb877612f948c09373cefd2ce6, 4601 chars)
--
-- GUARD AND WHAT HAPPENS WHEN IT DOES NOT MATCH (precedents 1259, 1297, 1299). The UPDATE only replaces the exact OLD text (and the exact
-- floor 341). A different live text matches 0 rows and the migration is a NOTICE-and-NO-OP (the NOTICE names the md5 found); if the live
-- text already equals NEW it is an idempotent no-op that does not fire the trigger. The one case that RAISES: the post-check finds the row
-- still carrying the OLD md5 (the UPDATE silently did nothing; never trust a silent no-op, CLAUDE.md N.4 / Trap 103). NOT verified against
-- production here (no production access): the live md5 of bg_remedies.integrity_check_sql must be read as suvarna_reader after the deploy.
--
-- ORDER OF OPERATIONS. Applying this makes the integrity check expect 316 rows while the live corpus still holds 341, so the check reads
-- FALSE until the governed rebuild runs, exactly as migration 608 documented for its own install (the corpus is rebuilt, never edited, by it).
-- Run the expected-change rebuild after the deploy; the post-rebuild check is TRUE (replay-verified).
--
-- SERVING EFFECT AT APPLY (binding for every migration PR). UPDATE of integrity_check_sql / target_floor fires the live trigger
-- nirmana_registry_receipt_invalidation (migration 596; WHEN old.* IS DISTINCT FROM new.*): it sets asset_freshness.freshness_state = 'stale'
-- (reason registry_changed) WHERE asset_id = NEW.asset_id. bg_remedies' freshness rows go stale until the rebuild writes fresh receipts;
-- no other asset is touched. A re-run updates 0 rows and does not fire it.
--
-- VERIFICATION BY PRODUCTION STRUCTURE (Trap 103). After the deploy, expect md5 d1d7fecb877612f948c09373cefd2ce6, length 4601, target_floor 316:
--   SELECT asset_id, md5(integrity_check_sql), length(integrity_check_sql), target_floor FROM asset_registry WHERE asset_id = 'bg_remedies';
--
-- ROLLBACK (not executed by migrate.ts): UPDATE asset_registry SET integrity_check_sql = <migration 608's remedy_check>, target_floor = 341,
-- volume_explanation = <migration 608's canonical_volume> WHERE asset_id = 'bg_remedies' AND md5(integrity_check_sql) = 'd1d7fecb877612f948c09373cefd2ce6';
-- (fires the same trigger; only meaningful together with restoring the 25 removed seed rows).

SET LOCAL lock_timeout = '5s';

DO $pre$
DECLARE v_n int; v_md5 text; v_floor bigint;
BEGIN
  SELECT count(*), max(md5(integrity_check_sql)), max(target_floor) INTO v_n, v_md5, v_floor FROM asset_registry WHERE asset_id = 'bg_remedies';
  IF v_n = 0 THEN
    RAISE NOTICE '1323: no bg_remedies registry row (empty registry); nothing to do';
  ELSIF v_md5 = 'd1d7fecb877612f948c09373cefd2ce6' THEN
    RAISE NOTICE '1323: bg_remedies integrity_check_sql already carries the citation-pass-2 pins; nothing to do';
  ELSIF v_md5 IS DISTINCT FROM '8c521f10b57f6b06eb1a73e49e0c6b25' OR v_floor IS DISTINCT FROM 341 THEN
    RAISE NOTICE '1323: bg_remedies integrity_check_sql / target_floor is not the state this migration was written against (md5 %, floor %); NO-OP, left as is', v_md5, v_floor;
  END IF;
END
$pre$;

UPDATE asset_registry
   SET target_floor = 316,
       volume_explanation = '316 achieved remedies from the frozen deterministic build: 258 static writer rows + 54 bg_texts-derived sweep rows + 4 accepted tantric rows. The 258 static rows are the earlier 283 minus the 25 rows removed by citation decision OS-2026-10-05-CITATIONS (migration 1323). Integrity enforces exact source-derived identity and closed taxonomies; ZERO LLM and ZERO fabrication.',
       integrity_check_sql = $ic$
WITH summary AS (
  SELECT
    count(*) AS total,
    count(DISTINCT remedy_id) AS distinct_ids,
    md5(string_agg(remedy_id, E'\n' ORDER BY remedy_id COLLATE "C")) AS id_md5,
    array_agg(DISTINCT planet ORDER BY planet) AS planets,
    array_agg(DISTINCT domain ORDER BY domain) AS domains,
    array_agg(DISTINCT remedy_type ORDER BY remedy_type) AS remedy_types,
    count(*) FILTER (WHERE category IS NULL) AS uncategorized_rows,
    count(*) FILTER (WHERE category = 'corpus_sweep') AS sweep_rows,
    count(*) FILTER (WHERE category = 'corpus_sweep' AND scaffold_status = 'live') AS sweep_live,
    count(*) FILTER (WHERE category = 'corpus_sweep' AND scaffold_status = 'review') AS sweep_review,
    count(*) FILTER (WHERE category = 'tantric') AS tantric_rows,
    count(*) FILTER (WHERE category = 'nakshatra_shanti') AS nakshatra_rows,
    count(*) FILTER (WHERE scaffold_status = 'live') AS live_rows,
    count(*) FILTER (WHERE scaffold_status = 'review') AS review_rows
  FROM brahma_remedy_corpus
), planet_counts AS (
  SELECT coalesce(jsonb_object_agg(planet, row_count), '{}'::jsonb) AS value
  FROM (
    SELECT planet, count(*) AS row_count
    FROM brahma_remedy_corpus WHERE planet IS NOT NULL GROUP BY planet
  ) counted
), domain_counts AS (
  SELECT coalesce(jsonb_object_agg(domain, row_count), '{}'::jsonb) AS value
  FROM (
    SELECT domain, count(*) AS row_count
    FROM brahma_remedy_corpus WHERE domain IS NOT NULL GROUP BY domain
  ) counted
), type_counts AS (
  SELECT coalesce(jsonb_object_agg(remedy_type, row_count), '{}'::jsonb) AS value
  FROM (
    SELECT remedy_type, count(*) AS row_count
    FROM brahma_remedy_corpus WHERE remedy_type IS NOT NULL GROUP BY remedy_type
  ) counted
)
SELECT (
  summary.total = 316
  AND summary.distinct_ids = 316
  AND summary.id_md5 = '476de921a54acbbfaae093a66121da48'
  AND summary.planets = ARRAY['jupiter','ketu','mars','mercury','moon','rahu','saturn','sun','venus']::text[]
  AND summary.domains = ARRAY['career','education','general','health','marriage','spirituality','wealth']::text[]
  AND summary.remedy_types = ARRAY['ayurvedic','behavioral','charity','gemstone','homa','japa','mantra','puja','tantric','vrata','yantra']::text[]
  AND planet_counts.value = '{"jupiter":37,"ketu":26,"mars":32,"mercury":26,"moon":46,"rahu":30,"saturn":38,"sun":52,"venus":29}'::jsonb
  AND domain_counts.value = '{"career":12,"education":5,"general":249,"health":17,"marriage":16,"spirituality":6,"wealth":11}'::jsonb
  AND type_counts.value = '{"ayurvedic":1,"behavioral":9,"charity":67,"gemstone":22,"homa":10,"japa":26,"mantra":65,"puja":54,"tantric":4,"vrata":35,"yantra":23}'::jsonb
  AND summary.uncategorized_rows = 231
  AND summary.sweep_rows = 54
  AND summary.sweep_live = 15
  AND summary.sweep_review = 39
  AND summary.tantric_rows = 4
  AND summary.nakshatra_rows = 27
  AND summary.live_rows = 277
  AND summary.review_rows = 39
  AND NOT EXISTS (
    SELECT 1
    FROM brahma_remedy_corpus
    WHERE remedy_id IS NULL OR btrim(remedy_id) = ''
       OR planet IS NULL OR btrim(planet) = ''
       OR domain IS NULL OR btrim(domain) = ''
       OR remedy_type IS NULL OR btrim(remedy_type) = ''
       OR prescription_text IS NULL OR btrim(prescription_text) = ''
       OR source_canonical_id IS NULL OR btrim(source_canonical_id) = ''
       OR source_citation IS NULL OR btrim(source_citation) = ''
       OR classical_ref IS NULL OR btrim(classical_ref) = ''
       OR confidence IS NULL OR confidence < 0 OR confidence > 1
       OR scaffold_status IS NULL OR scaffold_status NOT IN ('live', 'review')
       OR (category IS DISTINCT FROM 'corpus_sweep'
           AND scaffold_status IS DISTINCT FROM 'live')
       OR ((left(remedy_id, 6) = 'sweep_') IS DISTINCT FROM
           coalesce(category = 'corpus_sweep', false))
       OR ((left(remedy_id, 10) = 'nakshatra_') IS DISTINCT FROM
           coalesce(category = 'nakshatra_shanti', false))
       OR ((left(remedy_id, 4) = 'tan_') IS DISTINCT FROM
           coalesce(category = 'tantric', false))
       OR (category = 'tantric' AND (
           remedy_type IS DISTINCT FROM 'tantric'
           OR classical_attestation_text IS NULL
           OR btrim(classical_attestation_text) = ''
           OR jsonb_typeof(ingredients_jsonb) IS DISTINCT FROM 'object'
           OR ingredients_jsonb = '{}'::jsonb
           OR jsonb_typeof(timing_rules_jsonb) IS DISTINCT FROM 'object'
           OR timing_rules_jsonb = '{}'::jsonb
       ))
  )
) AS integrity_ok
FROM summary CROSS JOIN planet_counts CROSS JOIN domain_counts CROSS JOIN type_counts
$ic$
 WHERE asset_id = 'bg_remedies'
   AND target_floor = 341
   AND md5(integrity_check_sql) = '8c521f10b57f6b06eb1a73e49e0c6b25';

DO $post$
DECLARE v_md5 text;
BEGIN
  SELECT max(md5(integrity_check_sql)) INTO v_md5 FROM asset_registry WHERE asset_id = 'bg_remedies';
  IF v_md5 = '8c521f10b57f6b06eb1a73e49e0c6b25' THEN
    RAISE EXCEPTION '1323: bg_remedies integrity_check_sql still carries the OLD md5 8c521f10b57f6b06eb1a73e49e0c6b25 (update did not take)';
  END IF;
END
$post$;
