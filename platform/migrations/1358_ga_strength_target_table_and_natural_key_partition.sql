-- 1358_ga_strength_target_table_and_natural_key_partition.sql
--
-- Certification registry fix (SS N-425, Exec Suvarna). Fills TWO NULL columns of ONE asset_registry row (ga_strength): target_table
-- and natural_key_partition, in ONE guarded UPDATE; nothing else. They go together on purpose (see "WHY BOTH"). Transaction ownership
-- belongs to platform/scripts/migrate.ts (no BEGIN/COMMIT here). Data-only: no table or function is created or altered, so it runs
-- as amjis_app on the routine path. Shape: 1340 (guarded UPDATE + post-check that raises) with the 872/874 partition text shape.
--
-- THE GAP. Migration 891 recorded it and left it: "ga_strength asset_registry.natural_key_partition / target_table are both NULL
-- (a registry-data gap, not fixed here)". The census cells Ldgr and Vocab.identity read only asset_registry.target_table
-- (asset_census.py measure()), so the asset reads as having no table. Its writer writes ONE table, chart_facts.
--
-- WHY BOTH. provenance.py _registry_partition computes has_cowriters as "another active has_writer asset shares my target_table".
-- Today ga_strength's target_table is NULL, so has_cowriters is false and the partition is not needed. The moment target_table =
-- 'chart_facts' is set (shared with the other chart_facts writers, e.g. ga_nakshatra whose seed row names it), has_cowriters is true; provenance.py then (line ~92) marks the receipt reason partition_undeclared and
-- leaves partition_digest None when natural_key_partition is NULL, and the dependents (per the read-only investigation: ga_structural,
-- bo_laksana, ga_sade_sati, ga_vichara, ka_sangam) block on DEP-ASSERT. So target_table is never set without the partition.
--
-- HOW THE PARTITION WAS DERIVED (nothing guessed; 32 categories). Three independent sources agree exactly:
--  (1) THE WRITER. ga_writers/ga_strength_writer.py (registered by pipeline/orchestrator/writers/ga_strength.py) has ONE row sink:
--      _insert_chart_facts_rows (line 1876) -> INSERT INTO chart_facts (_CHART_FACTS_UPSERT_SQL, line 1849, ON CONFLICT on
--      chart_facts' key), after replace_prior_chart_facts(conn, rows) (line 1883; ga_writers/_idempotency.py lines 63-81: DELETE FROM chart_facts WHERE chart_id
--      AND fact_category = ANY(<the categories present in rows>) AND ayanamsha_id = ANY(...)). No other table is written. The
--      categories its rows carry were enumerated by the repo's own static extractor (platform/python-sidecar/tests/
--      test_l1_emitted_categories_have_ownership.py: AST over every "fact_category" dict key / keyword / subscript and helper call
--      site, f-strings and loops resolved; UNRESOLVED = 0 for this file): 32 categories.
--  (2) THE OWNERSHIP TABLE. fact_category_ownership rows ('<category>', 'ga_strength') are seeded by migration
--      1219_nirmana_l1_ga_structural_argala_graha_natal_ownership_and_count_sql.sql lines 281-312: the same 32, no more, no fewer
--      (the guard in 1219 refuses a category owned by another asset; none of the 32 has another owner).
--  (3) THE REGISTERED COUNT PREDICATE (as set by migration 1219; not read from production here). asset_registry.count_sql for
--      ga_strength (1219's strength_new; the seed text in scripts/seed/asset_registry_seed.ts) is: graha_shadbala_% (7) + graha_ishta_phala, graha_kashta_phala (2) + graha_vimsopaka_%
--      (4) + ashtakavarga_% minus ashtakavarga_anubindu (12) + house_bhava_bala_% (3) + graha_%_bala_per_varga (4) = 32.
--      ashtakavarga_anubindu and the bhava_bala_* / vimsopaka_bala_per_graha / graha_saptavargaja_bala_component rows belong to
--      ga_structural (1219) and are NOT in this partition.
--  None of the 32 appears in any other asset's natural_key_partition (migrations 868, 870, 871, 872, 874, 876, 878 checked).
--  natural_key_partition describes what the writer OWNS, in the 872/874 text shape ("chart_facts.fact_category IN (<sorted list>)").
--  Some of the 32 may have zero rows on a given chart (for example ashtakavarga_bindu_contributor was "not yet live" at 1219); the
--  partition names what the writer is entitled to emit, as 874 did for the esoteric_point_* trisphuta family.
--
-- GUARD. One UPDATE; each column is filled only while it is NULL (COALESCE keeps an existing value), and the UPDATE runs only if
-- at least one of the two is NULL. A column that already holds a different value is left as is with a NOTICE (never overwritten).
-- An absent row (empty registry) is a no-op with a NOTICE. The cases that RAISE: the post-check finds the row present and either
-- column still NULL (the UPDATE silently did nothing; never trust a silent no-op, CLAUDE.md N.4).
--
-- TRIGGER EFFECT (real, intended). target_table and natural_key_partition are columns of nirmana_registry_receipt_invalidation
-- (migration 596): the UPDATE stales the asset_freshness rows of ga_strength ONLY (registry_changed). ga_strength must be re-run,
-- then ga_structural (and the other dependents) rebuilt. Both columns are also in the registry-contract fingerprint
-- (nirmana-elevation/definitions.ts), so ga_strength's frozen manifest reads evidence_refresh_required until refreshed.
--
-- NOT CHANGED HERE: count_sql, size_sql, target_floor, volume_explanation, depends_on, the TypeScript seed
-- (scripts/seed/asset_registry_seed.ts keeps target_table: null; its registry insert is ON CONFLICT DO NOTHING, so a re-seed never
-- reverts this, and a fresh database replaying the seed then the migrations holds NULL, matches the guard, and is set here), the
-- ownership table, any data row, the writer, asset_declarations.json.
--
-- VERIFICATION BY PRODUCTION STRUCTURE (never trust a deploy log). After the deploy, as the read-only role:
--   SELECT asset_id, target_table, natural_key_partition FROM asset_registry WHERE asset_id = 'ga_strength';
--   -- expect chart_facts and the 32-category text below (md5 9b0a66322164e423ff99098977cdce7e, length 874)
--
-- ROLLBACK (not executed by migrate.ts): UPDATE asset_registry SET target_table = NULL, natural_key_partition = NULL
-- WHERE asset_id = 'ga_strength' AND target_table = 'chart_facts' AND md5(natural_key_partition) = '9b0a66322164e423ff99098977cdce7e';

SET LOCAL lock_timeout = '5s';

DO $pre$
DECLARE v_n int; v_tt text; v_nkp text;
BEGIN
  SELECT count(*), max(target_table), max(natural_key_partition) INTO v_n, v_tt, v_nkp FROM asset_registry WHERE asset_id = 'ga_strength';
  IF v_n = 0 THEN
    RAISE NOTICE '1358: no ga_strength registry row (empty registry); nothing to do';
  ELSE
    IF v_tt IS NOT NULL AND v_tt IS DISTINCT FROM 'chart_facts' THEN
      RAISE NOTICE '1358: ga_strength target_table is already % (not NULL); left as is', v_tt;
    END IF;
    IF v_nkp IS NOT NULL AND md5(v_nkp) IS DISTINCT FROM '9b0a66322164e423ff99098977cdce7e' THEN
      RAISE NOTICE '1358: ga_strength natural_key_partition is already set to a different text (md5 %); left as is', md5(v_nkp);
    END IF;
    IF v_tt IS NOT NULL AND v_nkp IS NOT NULL THEN
      RAISE NOTICE '1358: ga_strength target_table and natural_key_partition are already set; nothing to do';
    END IF;
  END IF;
END
$pre$;

UPDATE asset_registry
SET target_table = COALESCE(target_table, 'chart_facts'),
    natural_key_partition = COALESCE(natural_key_partition, $nkp$chart_facts.fact_category IN (ashtakavarga_bindu, ashtakavarga_bindu_contributor, ashtakavarga_bindu_per_varga, ashtakavarga_bindu_sign, ashtakavarga_ekadhipathya_shodhana, ashtakavarga_kakshya_boundary, ashtakavarga_pinda_bhinna, ashtakavarga_pinda_raasi, ashtakavarga_pinda_sarva, ashtakavarga_pinda_sarva_per_varga, ashtakavarga_pinda_sodhita, ashtakavarga_trikona_shodhana, graha_cheshta_bala_per_varga, graha_drik_bala_per_varga, graha_ishta_phala, graha_kala_bala_per_varga, graha_kashta_phala, graha_shadbala_cheshta, graha_shadbala_dig, graha_shadbala_drik, graha_shadbala_kala, graha_shadbala_naisargika, graha_shadbala_sthana, graha_shadbala_total, graha_sthana_bala_per_varga, graha_vimsopaka_dasavarga, graha_vimsopaka_saptavarga, graha_vimsopaka_shadvarga, graha_vimsopaka_shodasavarga, house_bhava_bala_ratio, house_bhava_bala_subscore, house_bhava_bala_total)$nkp$)
WHERE asset_id = 'ga_strength'
  AND (target_table IS NULL OR natural_key_partition IS NULL);

DO $post$
DECLARE v_n int; v_tt text; v_nkp text;
BEGIN
  SELECT count(*), max(target_table), max(natural_key_partition) INTO v_n, v_tt, v_nkp FROM asset_registry WHERE asset_id = 'ga_strength';
  IF v_n = 1 AND v_tt IS NULL THEN
    RAISE EXCEPTION '1358: ga_strength target_table update did not take (still NULL)';
  END IF;
  IF v_n = 1 AND v_nkp IS NULL THEN
    RAISE EXCEPTION '1358: ga_strength natural_key_partition update did not take (still NULL)';
  END IF;
END
$post$;
