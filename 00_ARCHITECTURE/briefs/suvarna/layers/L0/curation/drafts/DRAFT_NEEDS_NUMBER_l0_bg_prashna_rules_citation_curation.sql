-- =============================================================================
-- DRAFT_NEEDS_NUMBER_l0_bg_prashna_rules_citation_curation.sql      (HELD DRAFT: NOT APPLIED, NOT A MIGRATION)
-- Lane: curation-lane (Exec Suvarna), branch suvarna/land/TI-curation-001, N-101 curation of bg_prashna_rules.
-- SS allocates the migration number (block 1200-1299).  Citation TEXT only: 4 rows across 3 table(s);
-- no value, key or other column changes.  Every proposed citation is chunk-level (corpus chunk id + page + printed
-- sloka) and each row's FACT/INFERENCE class and supporting quote are in the ledger
-- (assets/bg_prashna_rules_ledger.json); rows the held text CONTRADICTS are not touched (acharya batch).
-- GUARDS  per-table md5 fingerprint of every non-timestamp column must equal the pinned pre-state; every UPDATE
--         matches natural key AND exact old citation and must hit the exact expected row count; post-state
--         fingerprints are pinned; the stored integrity_check_sql is pinned by md5 and resealed (each sha256/md5 literal replaced by the value computed on the test replica after the UPDATEs); it must read true afterwards;
--         idempotent: a second apply is a NOTICE + no-op.
-- Seed parity (NOT patched here; follow-up after SS review and PR #2984): platform/python-sidecar/brahmagyan/l0_prashna.py (ON CONFLICT upserts)
--         must carry the same citations or the next L0 rebuild reverts them; editing it also stales
--         nirmana-writer-digests.json (a #2984 file).
-- =============================================================================

DO $curation$
DECLARE
  n integer;
  ic text;
  ok boolean;
  fp_0 text;
  fp_1 text;
  fp_2 text;
  fp_3 text;
  fp_4 text;
BEGIN
  SELECT integrity_check_sql INTO ic FROM asset_registry WHERE asset_id = 'bg_prashna_rules' FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'curation refuses: asset_registry row bg_prashna_rules not found'; END IF;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY method_id::text COLLATE "C"), '')) FROM bg_prashna_lagna_methods t$q$ INTO fp_0;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY yoga_id::text COLLATE "C"), '')) FROM bg_prashna_tajik_yogas t$q$ INTO fp_1;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY question_class::text COLLATE "C"), '')) FROM bg_prashna_significators t$q$ INTO fp_2;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY rule_id::text COLLATE "C"), '')) FROM bg_prashna_fructification_rules t$q$ INTO fp_3;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY technique_id::text COLLATE "C"), '')) FROM bg_prashna_special_techniques t$q$ INTO fp_4;
  IF fp_0 = 'c55b42164a9d29c56157c5a7484bda69' AND fp_1 = '5a1d3bea02d24809864f3a23c127fa1d' AND fp_2 = 'be936e05e90b4192ea6311021649d45a' AND fp_3 = '7245a54369015b333be169f3d29aa3bc' AND fp_4 = '1a66973aa8535cae93bb2f58d3b458d9' THEN
    IF NOT (position('a71319cb57ee9288be608dc29ea4e7cf1866919a221ed22b72d76abf74bf88b1' IN ic) > 0 AND position('2d99bc467a4310e0f7af8b050700ea9daf49c23ca217c575b5aa31b0464dbf92' IN ic) > 0 AND position('b1ae7d8856ee217bcbb675f73e5e8795c2ee9325035649de1e96fed845cf96a5' IN ic) > 0) THEN RAISE EXCEPTION 'curation refuses: tables are at the curated content but the registry contract is not resealed'; END IF;
    RAISE NOTICE 'curation already applied: no-op';
    RETURN;
  END IF;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY method_id::text COLLATE "C"), '')) FROM bg_prashna_lagna_methods t$q$ INTO fp_0;
  IF fp_0 IS DISTINCT FROM '4269437ecb22d66a27a9745889725a82' THEN RAISE EXCEPTION 'curation refuses: bg_prashna_lagna_methods is not the pinned pre-state (%)', fp_0; END IF;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY yoga_id::text COLLATE "C"), '')) FROM bg_prashna_tajik_yogas t$q$ INTO fp_1;
  IF fp_1 IS DISTINCT FROM '4a5bf812362f63bfdcd67a61d7d5cda4' THEN RAISE EXCEPTION 'curation refuses: bg_prashna_tajik_yogas is not the pinned pre-state (%)', fp_1; END IF;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY question_class::text COLLATE "C"), '')) FROM bg_prashna_significators t$q$ INTO fp_2;
  IF fp_2 IS DISTINCT FROM '99f473e76e6ff36136a3e8c390134af3' THEN RAISE EXCEPTION 'curation refuses: bg_prashna_significators is not the pinned pre-state (%)', fp_2; END IF;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY rule_id::text COLLATE "C"), '')) FROM bg_prashna_fructification_rules t$q$ INTO fp_3;
  IF fp_3 IS DISTINCT FROM '7245a54369015b333be169f3d29aa3bc' THEN RAISE EXCEPTION 'curation refuses: bg_prashna_fructification_rules is not the pinned pre-state (%)', fp_3; END IF;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY technique_id::text COLLATE "C"), '')) FROM bg_prashna_special_techniques t$q$ INTO fp_4;
  IF fp_4 IS DISTINCT FROM '1a66973aa8535cae93bb2f58d3b458d9' THEN RAISE EXCEPTION 'curation refuses: bg_prashna_special_techniques is not the pinned pre-state (%)', fp_4; END IF;
  IF md5(ic) IS DISTINCT FROM '1dcfbb4b4a5083d3d7d26a7fd34155c4' THEN RAISE EXCEPTION 'curation refuses: registry integrity_check_sql is not the pinned pre-state text (md5 mismatch)'; END IF;

  UPDATE bg_prashna_lagna_methods t SET classical_citation = v.new_c
    FROM (VALUES
      ($c$tajik_moment_lagna$c$, $c$Tājika Nīlakaṇṭhī, Ch. 1 (Prashna Lagna Nirūpaṇa); Prashna Mārga Ch. 1$c$, $c$Hora Sara, Ch. 27 (printed 'CHAPTER 27'), Sloka 5 as printed — hora_sara:PG308:C1 (Santhanam trans.); Brihat Jataka, Ch. XXVI, Sloka 1 as printed — brihat_jataka:PG525:C1 (Sastri 2nd ed.)$c$)
    ) AS v(method_id, old_c, new_c)
    WHERE t.method_id::text = v.method_id AND t.classical_citation = v.old_c;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n <> 1 THEN RAISE EXCEPTION 'curation expected 1 bg_prashna_lagna_methods rows, updated %', n; END IF;
  UPDATE bg_prashna_tajik_yogas t SET classical_citation = v.new_c
    FROM (VALUES
      ($c$eesarpha$c$, $c$Tājika Nīlakaṇṭhī, Ch. 4 (Ithashāla adhyāya, Eesarpha section)$c$, $c$Tajika Nilakanthi (Mahidhara Hindi bhasha-tika), Ṣoḍaśa-yoga-adhyāya (printed 'अथ षोडशयोगाध्यायः'), Sloka 10 as printed — tajaka_neelakanthi:PG55:C1 (Shrikrishnadas Press ed. with Hindi bhasha-tika; Devanagari OCR, AWAITING_NATIVE_DECISION) [Isarpha: faster planet one degree beyond the slower]$c$),
      ($c$nakta$c$, $c$Tājika Nīlakaṇṭhī, Ch. 4 (Nakta adhyāya)$c$, $c$Tajika Nilakanthi (Mahidhara Hindi bhasha-tika), Ṣoḍaśa-yoga-adhyāya (printed 'अथ षोडशयोगाध्यायः'), Sloka 11 as printed — tajaka_neelakanthi:PG55:C1 (Shrikrishnadas Press ed. with Hindi bhasha-tika; Devanagari OCR, AWAITING_NATIVE_DECISION) [Nakta]$c$)
    ) AS v(yoga_id, old_c, new_c)
    WHERE t.yoga_id::text = v.yoga_id AND t.classical_citation = v.old_c;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n <> 2 THEN RAISE EXCEPTION 'curation expected 2 bg_prashna_tajik_yogas rows, updated %', n; END IF;
  UPDATE bg_prashna_significators t SET classical_citation = v.new_c
    FROM (VALUES
      ($c$children_progeny$c$, $c$Prashna Mārga, Ch. 18 (Santāna Prashna)$c$, $c$Tājika Nīlakaṇṭhī, Prashna-tantra, Bhāva-nirṇaya (printed 'अथ भवनिणयः'), Sloka 5 as printed — tajaka_neelakanthi:PG213:C1 (Shrikrishnadas Press ed. with Hindi bhasha-tika; Devanagari OCR, AWAITING_NATIVE_DECISION) [house-assignment only; planetary karakas not stated]$c$)
    ) AS v(question_class, old_c, new_c)
    WHERE t.question_class::text = v.question_class AND t.classical_citation = v.old_c;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n <> 1 THEN RAISE EXCEPTION 'curation expected 1 bg_prashna_significators rows, updated %', n; END IF;

  -- post-flight
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY method_id::text COLLATE "C"), '')) FROM bg_prashna_lagna_methods t$q$ INTO fp_0;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY yoga_id::text COLLATE "C"), '')) FROM bg_prashna_tajik_yogas t$q$ INTO fp_1;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY question_class::text COLLATE "C"), '')) FROM bg_prashna_significators t$q$ INTO fp_2;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY rule_id::text COLLATE "C"), '')) FROM bg_prashna_fructification_rules t$q$ INTO fp_3;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY technique_id::text COLLATE "C"), '')) FROM bg_prashna_special_techniques t$q$ INTO fp_4;
  IF fp_0 IS DISTINCT FROM 'c55b42164a9d29c56157c5a7484bda69' THEN RAISE EXCEPTION 'curation post-flight: bg_prashna_lagna_methods content fingerprint mismatch (%)', fp_0; END IF;
  IF fp_1 IS DISTINCT FROM '5a1d3bea02d24809864f3a23c127fa1d' THEN RAISE EXCEPTION 'curation post-flight: bg_prashna_tajik_yogas content fingerprint mismatch (%)', fp_1; END IF;
  IF fp_2 IS DISTINCT FROM 'be936e05e90b4192ea6311021649d45a' THEN RAISE EXCEPTION 'curation post-flight: bg_prashna_significators content fingerprint mismatch (%)', fp_2; END IF;
  IF fp_3 IS DISTINCT FROM '7245a54369015b333be169f3d29aa3bc' THEN RAISE EXCEPTION 'curation post-flight: bg_prashna_fructification_rules content fingerprint mismatch (%)', fp_3; END IF;
  IF fp_4 IS DISTINCT FROM '1a66973aa8535cae93bb2f58d3b458d9' THEN RAISE EXCEPTION 'curation post-flight: bg_prashna_special_techniques content fingerprint mismatch (%)', fp_4; END IF;

  -- reseal the stored integrity contract (its sha256 covers the changed tables)
  UPDATE asset_registry SET integrity_check_sql = replace(replace(replace(integrity_check_sql, '1fcf4a29aada13aeb3458a601f42206111cdd0e7132f1d3973f49b65de239b11', 'a71319cb57ee9288be608dc29ea4e7cf1866919a221ed22b72d76abf74bf88b1'), 'd67e84e57e5c616f132929e845dec3ee8d5fccd4d9530d9c5c90b0a275662638', '2d99bc467a4310e0f7af8b050700ea9daf49c23ca217c575b5aa31b0464dbf92'), '8a02f4bd19ad23ab67ec1b7354d6c537e0c54453d4a6c405caf033c630879427', 'b1ae7d8856ee217bcbb675f73e5e8795c2ee9325035649de1e96fed845cf96a5') WHERE asset_id = 'bg_prashna_rules';
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n <> 1 THEN RAISE EXCEPTION 'curation expected 1 registry row, updated %', n; END IF;
  SELECT integrity_check_sql INTO ic FROM asset_registry WHERE asset_id = 'bg_prashna_rules';
  IF ic IS NOT NULL THEN
    EXECUTE ic INTO ok;
    IF ok IS NOT TRUE THEN RAISE EXCEPTION 'curation post-flight: bg_prashna_rules stored integrity_check_sql reads false'; END IF;
  END IF;
END
$curation$;
