-- =============================================================================
-- DRAFT_NEEDS_NUMBER_l0_bg_reference_citation_curation.sql      (HELD DRAFT: NOT APPLIED, NOT A MIGRATION)
-- Lane: curation-lane (Exec Suvarna), branch suvarna/land/TI-curation-001, N-101 curation of bg_reference.
-- SS allocates the migration number (block 1200-1299).  Citation TEXT only: 319 rows across 9 table(s);
-- no value, key or other column changes.  Every proposed citation is chunk-level (corpus chunk id + page + printed
-- sloka) and each row's FACT/INFERENCE class and supporting quote are in the ledger
-- (assets/bg_reference_ledger.json); rows the held text CONTRADICTS are not touched (acharya batch).
-- GUARDS  per-table md5 fingerprint of every non-timestamp column must equal the pinned pre-state; every UPDATE
--         matches natural key AND exact old citation and must hit the exact expected row count; post-state
--         fingerprints are pinned; the stored integrity_check_sql is pinned by md5 and resealed (each sha256/md5 literal replaced by the value computed on the test replica after the UPDATEs); it must read true afterwards;
--         idempotent: a second apply is a NOTICE + no-op.
-- Seed parity (NOT patched here; follow-up after SS review and PR #2984): platform/python-sidecar/brahmagyan/l0_reference.py (ON CONFLICT upserts)
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
  fp_5 text;
  fp_6 text;
  fp_7 text;
  fp_8 text;
  fp_9 text;
  fp_10 text;
BEGIN
  SELECT integrity_check_sql INTO ic FROM asset_registry WHERE asset_id = 'bg_reference' FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'curation refuses: asset_registry row bg_reference not found'; END IF;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t) - ARRAY[$v$created_at$v$]::text[])::text, E'\n' ORDER BY planet_id::text COLLATE "C"), '')) FROM reference_planets t$q$ INTO fp_0;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t) - ARRAY[$v$created_at$v$]::text[])::text, E'\n' ORDER BY sign_id::text COLLATE "C"), '')) FROM reference_signs t$q$ INTO fp_1;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY house_num::text COLLATE "C"), '')) FROM reference_houses t$q$ INTO fp_2;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t) - ARRAY[$v$created_at$v$]::text[])::text, E'\n' ORDER BY planet_id::text COLLATE "C",aspect_house::text COLLATE "C"), '')) FROM reference_aspects t$q$ INTO fp_3;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t) - ARRAY[$v$created_at$v$]::text[])::text, E'\n' ORDER BY varga_id::text COLLATE "C"), '')) FROM reference_vargas t$q$ INTO fp_4;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY upagraha_id::text COLLATE "C"), '')) FROM reference_upagrahas t$q$ INTO fp_5;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY strength_id::text COLLATE "C"), '')) FROM reference_strength_systems t$q$ INTO fp_6;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY karaka_id::text COLLATE "C"), '')) FROM reference_karakas t$q$ INTO fp_7;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY constant_id::text COLLATE "C"), '')) FROM reference_constants t$q$ INTO fp_8;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY term_id::text COLLATE "C"), '')) FROM reference_glossary t$q$ INTO fp_9;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY 1), '')) FROM reference_topic_tags t$q$ INTO fp_10;
  IF fp_0 = 'b24330881588405e3280d4d2ad06bea9' AND fp_1 = '1929fa861aee5966bab4c2566f827a5d' AND fp_2 = '42ce51f84e07e692a504299ab82594ec' AND fp_3 = '4720cc744a390275bb514a45b875aec5' AND fp_4 = '7c6d4e2277a1e5dd70c956d9198c4d29' AND fp_5 = 'd792e78755ebe8cfbf82784b80dfcfcf' AND fp_6 = '453c0c04284632098e805090335cff90' AND fp_7 = '5a63e77928cefe1466e16e785c4d7dc6' AND fp_8 = '868811981c90dd570e3a28ae941767e4' AND fp_9 = '08e69ca18715909f9bd3c4711fd0946e' AND fp_10 = 'af70b29a8842fba70ceb0da7710d00b2' THEN
    IF NOT (position('4e40a8e1c28f56c49c50fc65d7dbccc5' IN ic) > 0 AND position('c8e7e4a8d0b623f7969fda5239e9cfd6' IN ic) > 0 AND position('b2dd1998171a96795939fe588781ec4e' IN ic) > 0 AND position('6e0e57e8b65cbe6cf7c27325991f1bca' IN ic) > 0 AND position('80266a318b102ac0f2d772cc31ab93cb' IN ic) > 0 AND position('b618e1891d70fbd0ca127a5d5538ed70' IN ic) > 0 AND position('3715b7dbd06eaa7bd99c464fe6b2a561' IN ic) > 0 AND position('b4820981f3e285a5675d4fcfc0a91fb0' IN ic) > 0 AND position('b275ec96e14e3443284b608cf1f4113f' IN ic) > 0) THEN RAISE EXCEPTION 'curation refuses: tables are at the curated content but the registry contract is not resealed'; END IF;
    RAISE NOTICE 'curation already applied: no-op';
    RETURN;
  END IF;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t) - ARRAY[$v$created_at$v$]::text[])::text, E'\n' ORDER BY planet_id::text COLLATE "C"), '')) FROM reference_planets t$q$ INTO fp_0;
  IF fp_0 IS DISTINCT FROM '67f97c56c6074c5e1dc2e98e25b55814' THEN RAISE EXCEPTION 'curation refuses: reference_planets is not the pinned pre-state (%)', fp_0; END IF;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t) - ARRAY[$v$created_at$v$]::text[])::text, E'\n' ORDER BY sign_id::text COLLATE "C"), '')) FROM reference_signs t$q$ INTO fp_1;
  IF fp_1 IS DISTINCT FROM 'c6c4d218ea26ee03cab75211ed8901eb' THEN RAISE EXCEPTION 'curation refuses: reference_signs is not the pinned pre-state (%)', fp_1; END IF;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY house_num::text COLLATE "C"), '')) FROM reference_houses t$q$ INTO fp_2;
  IF fp_2 IS DISTINCT FROM 'c87a10777c280675095d2c725831c658' THEN RAISE EXCEPTION 'curation refuses: reference_houses is not the pinned pre-state (%)', fp_2; END IF;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t) - ARRAY[$v$created_at$v$]::text[])::text, E'\n' ORDER BY planet_id::text COLLATE "C",aspect_house::text COLLATE "C"), '')) FROM reference_aspects t$q$ INTO fp_3;
  IF fp_3 IS DISTINCT FROM '3f332cba3fbf9651897d36c1c21cd5f4' THEN RAISE EXCEPTION 'curation refuses: reference_aspects is not the pinned pre-state (%)', fp_3; END IF;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t) - ARRAY[$v$created_at$v$]::text[])::text, E'\n' ORDER BY varga_id::text COLLATE "C"), '')) FROM reference_vargas t$q$ INTO fp_4;
  IF fp_4 IS DISTINCT FROM '8660b2cfddcdd84239614902b647729e' THEN RAISE EXCEPTION 'curation refuses: reference_vargas is not the pinned pre-state (%)', fp_4; END IF;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY upagraha_id::text COLLATE "C"), '')) FROM reference_upagrahas t$q$ INTO fp_5;
  IF fp_5 IS DISTINCT FROM '957f2fe12a4aacde4b15fc8574f4f08b' THEN RAISE EXCEPTION 'curation refuses: reference_upagrahas is not the pinned pre-state (%)', fp_5; END IF;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY strength_id::text COLLATE "C"), '')) FROM reference_strength_systems t$q$ INTO fp_6;
  IF fp_6 IS DISTINCT FROM '2b5115ee9401076c86955073aa8f52c6' THEN RAISE EXCEPTION 'curation refuses: reference_strength_systems is not the pinned pre-state (%)', fp_6; END IF;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY karaka_id::text COLLATE "C"), '')) FROM reference_karakas t$q$ INTO fp_7;
  IF fp_7 IS DISTINCT FROM 'bf6e5950ab1c9b58269c49a47193a6c3' THEN RAISE EXCEPTION 'curation refuses: reference_karakas is not the pinned pre-state (%)', fp_7; END IF;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY constant_id::text COLLATE "C"), '')) FROM reference_constants t$q$ INTO fp_8;
  IF fp_8 IS DISTINCT FROM '86c57086d63a649b3e7dbcea389c123b' THEN RAISE EXCEPTION 'curation refuses: reference_constants is not the pinned pre-state (%)', fp_8; END IF;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY term_id::text COLLATE "C"), '')) FROM reference_glossary t$q$ INTO fp_9;
  IF fp_9 IS DISTINCT FROM '08e69ca18715909f9bd3c4711fd0946e' THEN RAISE EXCEPTION 'curation refuses: reference_glossary is not the pinned pre-state (%)', fp_9; END IF;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY 1), '')) FROM reference_topic_tags t$q$ INTO fp_10;
  IF fp_10 IS DISTINCT FROM 'af70b29a8842fba70ceb0da7710d00b2' THEN RAISE EXCEPTION 'curation refuses: reference_topic_tags is not the pinned pre-state (%)', fp_10; END IF;
  IF md5(ic) IS DISTINCT FROM '791980491fda3d52848c2513218d3af7' THEN RAISE EXCEPTION 'curation refuses: registry integrity_check_sql is not the pinned pre-state text (md5 mismatch)'; END IF;

  UPDATE reference_planets t SET source_citation = v.new_c
    FROM (VALUES
      ($c$sun$c$, $c$BPHS Ch.3 (Grahana-svarupa-adhyaya)$c$, $c$BPHS, Sloka 49-50 as printed - bphs:PG37:C2, bphs:PG38:C1; Sloka 51-54 as printed - bphs:PG38:C1; Sloka 11 as printed - bphs:PG26:C1; Sloka 15 as printed - bphs:PG499:C1, bphs:PG499:C2 (Santhanam trans.); Phaladipika, Adh. I, Sloka 7 as printed - phaladeepika:PG41:C1; Adh. I, Sloka 6 as printed - phaladeepika:PG40:C1 (Sastri trans. 1950)$c$),
      ($c$moon$c$, $c$BPHS Ch.3 (Grahana-svarupa-adhyaya)$c$, $c$BPHS, Sloka 49-50 as printed - bphs:PG37:C2, bphs:PG38:C1; Sloka 11 as printed - bphs:PG26:C1; Sloka 15 as printed - bphs:PG499:C1, bphs:PG499:C2 (Santhanam trans.); Phaladipika, Adh. I, Sloka 7 as printed - phaladeepika:PG41:C1; Adh. I, Sloka 6 as printed - phaladeepika:PG40:C1 (Sastri trans. 1950); Jataka Parijata, Slokas 26-28 as printed - jataka_parijata:PG45:C1 (Sastri trans. 1932-33)$c$),
      ($c$mars$c$, $c$BPHS Ch.3 (Grahana-svarupa-adhyaya)$c$, $c$BPHS, Sloka 49-50 as printed - bphs:PG37:C2, bphs:PG38:C1; Sloka 51-54 as printed - bphs:PG38:C1; Sloka 11 as printed - bphs:PG26:C1; Sloka 15 as printed - bphs:PG499:C1, bphs:PG499:C2 (Santhanam trans.); Phaladipika, Adh. I, Sloka 7 as printed - phaladeepika:PG41:C1; Adh. I, Sloka 6 as printed - phaladeepika:PG40:C1 (Sastri trans. 1950)$c$),
      ($c$mercury$c$, $c$BPHS Ch.3 (Grahana-svarupa-adhyaya)$c$, $c$BPHS, Sloka 49-50 as printed - bphs:PG37:C2, bphs:PG38:C1; Sloka 51-54 as printed - bphs:PG38:C2; Sloka 11 as printed - bphs:PG26:C1; Sloka 15 as printed - bphs:PG499:C1, bphs:PG499:C2 (Santhanam trans.); Phaladipika, Adh. I, Sloka 7 as printed - phaladeepika:PG41:C1; Adh. I, Sloka 6 as printed - phaladeepika:PG40:C1 (Sastri trans. 1950)$c$),
      ($c$jupiter$c$, $c$BPHS Ch.3 (Grahana-svarupa-adhyaya)$c$, $c$BPHS, Sloka 49-50 as printed - bphs:PG37:C2, bphs:PG38:C1; Sloka 51-54 as printed - bphs:PG38:C2; Sloka 11 as printed - bphs:PG26:C1; Sloka 15 as printed - bphs:PG499:C1, bphs:PG499:C2 (Santhanam trans.); Phaladipika, Adh. I, Sloka 7 as printed - phaladeepika:PG41:C1; Adh. I, Sloka 6 as printed - phaladeepika:PG40:C1 (Sastri trans. 1950)$c$),
      ($c$venus$c$, $c$BPHS Ch.3 (Grahana-svarupa-adhyaya)$c$, $c$BPHS, Sloka 49-50 as printed - bphs:PG37:C2, bphs:PG38:C1; Sloka 51-54 as printed - bphs:PG38:C2; Sloka 11 as printed - bphs:PG26:C1; Sloka 15 as printed - bphs:PG499:C1, bphs:PG499:C2 (Santhanam trans.); Phaladipika, Adh. I, Sloka 7 as printed - phaladeepika:PG41:C1; Adh. I, Sloka 6 as printed - phaladeepika:PG40:C1 (Sastri trans. 1950)$c$),
      ($c$saturn$c$, $c$BPHS Ch.3 (Grahana-svarupa-adhyaya)$c$, $c$BPHS, Sloka 49-50 as printed - bphs:PG37:C2, bphs:PG38:C1; Sloka 51-54 as printed - bphs:PG38:C2; Sloka 11 as printed - bphs:PG26:C1; Sloka 15 as printed - bphs:PG499:C1, bphs:PG499:C2 (Santhanam trans.); Phaladipika, Adh. I, Sloka 7 as printed - phaladeepika:PG41:C1; Adh. I, Sloka 6 as printed - phaladeepika:PG40:C1 (Sastri trans. 1950)$c$)
    ) AS v(planet_id, old_c, new_c)
    WHERE t.planet_id::text = v.planet_id AND t.source_citation = v.old_c;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n <> 7 THEN RAISE EXCEPTION 'curation expected 7 reference_planets rows, updated %', n; END IF;
  UPDATE reference_signs t SET source_citation = v.new_c
    FROM (VALUES
      ($c$2$c$, $c$BPHS Ch.6 (Rasi-svarupa-adhyaya)$c$, $c$BPHS, Sloka 8 as printed - bphs:PG49:C2; Sloka 5-6 as printed - bphs:PG48:C1 (Santhanam trans.); Phaladipika, Adh. I, Sloka 6 as printed - phaladeepika:PG40:C1 (Sastri trans. 1950)$c$),
      ($c$3$c$, $c$BPHS Ch.6 (Rasi-svarupa-adhyaya)$c$, $c$BPHS, Sloka 9-9½ as printed - bphs:PG50:C1; Sloka 5-6 as printed - bphs:PG48:C1 (Santhanam trans.); Phaladipika, Adh. I, Sloka 6 as printed - phaladeepika:PG40:C1 (Sastri trans. 1950)$c$),
      ($c$4$c$, $c$BPHS Ch.6 (Rasi-svarupa-adhyaya)$c$, $c$BPHS, Sloka 10-11 as printed - bphs:PG50:C1; Sloka 5-6 as printed - bphs:PG48:C1 (Santhanam trans.); Phaladipika, Adh. I, Sloka 6 as printed - phaladeepika:PG40:C1 (Sastri trans. 1950)$c$),
      ($c$5$c$, $c$BPHS Ch.6 (Rasi-svarupa-adhyaya)$c$, $c$BPHS, Sloka 12 as printed - bphs:PG50:C1; Sloka 5-6 as printed - bphs:PG48:C1 (Santhanam trans.); Phaladipika, Adh. I, Sloka 6 as printed - phaladeepika:PG40:C1 (Sastri trans. 1950)$c$),
      ($c$6$c$, $c$BPHS Ch.6 (Rasi-svarupa-adhyaya)$c$, $c$BPHS, Sloka 13-14 as printed - bphs:PG50:C1; Sloka 5-6 as printed - bphs:PG48:C1 (Santhanam trans.); Phaladipika, Adh. I, Sloka 6 as printed - phaladeepika:PG40:C1 (Sastri trans. 1950)$c$),
      ($c$7$c$, $c$BPHS Ch.6 (Rasi-svarupa-adhyaya)$c$, $c$BPHS, Sloka 15-16 as printed - bphs:PG51:C1; Sloka 5-6 as printed - bphs:PG48:C1 (Santhanam trans.); Phaladipika, Adh. I, Sloka 6 as printed - phaladeepika:PG40:C1 (Sastri trans. 1950)$c$),
      ($c$8$c$, $c$BPHS Ch.6 (Rasi-svarupa-adhyaya)$c$, $c$BPHS, Sloka 15-16 as printed - bphs:PG51:C1; Sloka 5-6 as printed - bphs:PG48:C1 (Santhanam trans.); Phaladipika, Adh. I, Sloka 6 as printed - phaladeepika:PG40:C1 (Sastri trans. 1950)$c$),
      ($c$10$c$, $c$BPHS Ch.6 (Rasi-svarupa-adhyaya)$c$, $c$BPHS, Sloka 19-20 as printed - bphs:PG52:C1; Sloka 5-6 as printed - bphs:PG48:C1 (Santhanam trans.); Phaladipika, Adh. I, Sloka 6 as printed - phaladeepika:PG40:C1 (Sastri trans. 1950)$c$),
      ($c$11$c$, $c$BPHS Ch.6 (Rasi-svarupa-adhyaya)$c$, $c$BPHS, Sloka 21-21½ as printed - bphs:PG52:C1; Sloka 5-6 as printed - bphs:PG48:C1 (Santhanam trans.); Phaladipika, Adh. I, Sloka 6 as printed - phaladeepika:PG40:C1 (Sastri trans. 1950)$c$),
      ($c$12$c$, $c$BPHS Ch.6 (Rasi-svarupa-adhyaya)$c$, $c$BPHS, Sloka 22-24 as printed - bphs:PG52:C1; Sloka 5-6 as printed - bphs:PG48:C1 (Santhanam trans.); Phaladipika, Adh. I, Sloka 6 as printed - phaladeepika:PG40:C1 (Sastri trans. 1950)$c$)
    ) AS v(sign_id, old_c, new_c)
    WHERE t.sign_id::text = v.sign_id AND t.source_citation = v.old_c;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n <> 10 THEN RAISE EXCEPTION 'curation expected 10 reference_signs rows, updated %', n; END IF;
  UPDATE reference_houses t SET source_citation = v.new_c
    FROM (VALUES
      ($c$3$c$, $c$BPHS Ch.7; Phaladeepika Ch.4$c$, $c$BPHS, Sloka 33-36 as printed - bphs:PG101:C1; Sloka 37-38 as printed - bphs:PG101:C1 (Santhanam trans.); Phaladipika, Adh. I, Sloka 18 as printed - phaladeepika:PG46:C1; Adh. XV, Sloka 17 as printed - phaladeepika:PG196:C1 (Sastri trans. 1950)$c$),
      ($c$5$c$, $c$BPHS Ch.7; Phaladeepika Ch.4$c$, $c$BPHS, Sloka 33-36 as printed - bphs:PG101:C1; Sloka 37-38 as printed - bphs:PG101:C1 (Santhanam trans.); Phaladipika, Adh. I, Sloka 18 as printed - phaladeepika:PG46:C1; Adh. XV, Sloka 17 as printed - phaladeepika:PG196:C1 (Sastri trans. 1950)$c$),
      ($c$6$c$, $c$BPHS Ch.7; Phaladeepika Ch.4$c$, $c$BPHS, Sloka 33-36 as printed - bphs:PG101:C1; Sloka 37-38 as printed - bphs:PG101:C1 (Santhanam trans.); Phaladipika, Adh. I, Sloka 17 as printed - phaladeepika:PG46:C1; Adh. XV, Sloka 17 as printed - phaladeepika:PG196:C1 (Sastri trans. 1950)$c$),
      ($c$7$c$, $c$BPHS Ch.7; Phaladeepika Ch.4$c$, $c$BPHS, Sloka 33-36 as printed - bphs:PG101:C1; Sloka 37-38 as printed - bphs:PG101:C1; Sloka 2-5 as printed, translator note - bphs:PG440:C1 (Santhanam trans.); Phaladipika, Adh. I, Sloka 17 as printed - phaladeepika:PG46:C1; Adh. XV, Sloka 17 as printed - phaladeepika:PG196:C1 (Sastri trans. 1950)$c$),
      ($c$8$c$, $c$BPHS Ch.7; Phaladeepika Ch.4$c$, $c$BPHS, Sloka 33-36 as printed - bphs:PG101:C1; Sloka 37-38 as printed - bphs:PG101:C1 (Santhanam trans.); Phaladipika, Adh. I, Sloka 17 as printed - phaladeepika:PG46:C1; Adh. XV, Sloka 17 as printed - phaladeepika:PG196:C1 (Sastri trans. 1950)$c$),
      ($c$9$c$, $c$BPHS Ch.7; Phaladeepika Ch.4$c$, $c$BPHS, Sloka 33-36 as printed - bphs:PG101:C1; Sloka 37-38 as printed - bphs:PG101:C1 (Santhanam trans.); Phaladipika, Adh. I, Sloka 18 as printed - phaladeepika:PG46:C1; Adh. XV, Sloka 17 as printed - phaladeepika:PG196:C1 (Sastri trans. 1950)$c$),
      ($c$10$c$, $c$BPHS Ch.7; Phaladeepika Ch.4$c$, $c$BPHS, Sloka 33-36 as printed - bphs:PG101:C1; Sloka 37-38 as printed - bphs:PG101:C1 (Santhanam trans.); Phaladipika, Adh. I, Sloka 17 as printed - phaladeepika:PG46:C1; Adh. XV, Sloka 17 as printed - phaladeepika:PG196:C1 (Sastri trans. 1950)$c$),
      ($c$11$c$, $c$BPHS Ch.7; Phaladeepika Ch.4$c$, $c$BPHS, Sloka 33-36 as printed - bphs:PG101:C1; Sloka 37-38 as printed - bphs:PG101:C1 (Santhanam trans.); Phaladipika, Adh. I, Sloka 18 as printed - phaladeepika:PG46:C1; Adh. XV, Sloka 17 as printed - phaladeepika:PG196:C1 (Sastri trans. 1950)$c$)
    ) AS v(house_num, old_c, new_c)
    WHERE t.house_num::text = v.house_num AND t.source_citation = v.old_c;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n <> 8 THEN RAISE EXCEPTION 'curation expected 8 reference_houses rows, updated %', n; END IF;
  UPDATE reference_aspects t SET source_citation = v.new_c
    FROM (VALUES
      ($c$sun$c$, $c$7$c$, $c$BPHS Ch.26 (Drishti-phala-adhyaya)$c$, $c$BPHS, Sloka 2-5 as printed - bphs:PG254:C1 (Santhanam trans.)$c$),
      ($c$moon$c$, $c$7$c$, $c$BPHS Ch.26 (Drishti-phala-adhyaya)$c$, $c$BPHS, Sloka 2-5 as printed - bphs:PG254:C1 (Santhanam trans.)$c$),
      ($c$mars$c$, $c$7$c$, $c$BPHS Ch.26 (Drishti-phala-adhyaya)$c$, $c$BPHS, Sloka 2-5 as printed - bphs:PG254:C1 (Santhanam trans.)$c$),
      ($c$mercury$c$, $c$7$c$, $c$BPHS Ch.26 (Drishti-phala-adhyaya)$c$, $c$BPHS, Sloka 2-5 as printed - bphs:PG254:C1 (Santhanam trans.)$c$),
      ($c$jupiter$c$, $c$7$c$, $c$BPHS Ch.26 (Drishti-phala-adhyaya)$c$, $c$BPHS, Sloka 2-5 as printed - bphs:PG254:C1 (Santhanam trans.)$c$),
      ($c$venus$c$, $c$7$c$, $c$BPHS Ch.26 (Drishti-phala-adhyaya)$c$, $c$BPHS, Sloka 2-5 as printed - bphs:PG254:C1 (Santhanam trans.)$c$),
      ($c$saturn$c$, $c$7$c$, $c$BPHS Ch.26 (Drishti-phala-adhyaya)$c$, $c$BPHS, Sloka 2-5 as printed - bphs:PG254:C1 (Santhanam trans.)$c$),
      ($c$rahu$c$, $c$7$c$, $c$BPHS Ch.26 (Drishti-phala-adhyaya)$c$, $c$BPHS, Sloka 2-5 as printed - bphs:PG254:C1 (Santhanam trans.); Uttara Kalamrita, p.41 - uttara_kalamrita:PG41:C1 (P.S. Sastri trans.)$c$),
      ($c$ketu$c$, $c$7$c$, $c$BPHS Ch.26 (Drishti-phala-adhyaya)$c$, $c$BPHS, Sloka 2-5 as printed - bphs:PG254:C1 (Santhanam trans.)$c$),
      ($c$mars$c$, $c$4$c$, $c$BPHS Ch.26 (Drishti-phala-adhyaya)$c$, $c$BPHS, Sloka 2-5 as printed - bphs:PG254:C1 (Santhanam trans.)$c$),
      ($c$mars$c$, $c$8$c$, $c$BPHS Ch.26 (Drishti-phala-adhyaya)$c$, $c$BPHS, Sloka 2-5 as printed - bphs:PG254:C1 (Santhanam trans.)$c$),
      ($c$jupiter$c$, $c$5$c$, $c$BPHS Ch.26 (Drishti-phala-adhyaya)$c$, $c$BPHS, Sloka 2-5 as printed - bphs:PG254:C1 (Santhanam trans.)$c$),
      ($c$jupiter$c$, $c$9$c$, $c$BPHS Ch.26 (Drishti-phala-adhyaya)$c$, $c$BPHS, Sloka 2-5 as printed - bphs:PG254:C1 (Santhanam trans.)$c$),
      ($c$saturn$c$, $c$3$c$, $c$BPHS Ch.26 (Drishti-phala-adhyaya)$c$, $c$BPHS, Sloka 2-5 as printed - bphs:PG254:C1 (Santhanam trans.)$c$),
      ($c$saturn$c$, $c$10$c$, $c$BPHS Ch.26 (Drishti-phala-adhyaya)$c$, $c$BPHS, Sloka 2-5 as printed - bphs:PG254:C1 (Santhanam trans.)$c$)
    ) AS v(planet_id, aspect_house, old_c, new_c)
    WHERE t.planet_id::text = v.planet_id AND t.aspect_house::text = v.aspect_house AND t.source_citation = v.old_c;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n <> 15 THEN RAISE EXCEPTION 'curation expected 15 reference_aspects rows, updated %', n; END IF;
  UPDATE reference_vargas t SET source_citation = v.new_c
    FROM (VALUES
      ($c$D1$c$, $c$BPHS Ch.6 (Shodasha-varga-adhyaya)$c$, $c$BPHS, Sloka 2-4 as printed - bphs:PG67:C1; Sloka 1-8 as printed - bphs:PG90:C1 (Santhanam trans.)$c$),
      ($c$D2$c$, $c$BPHS Ch.6 (Shodasha-varga-adhyaya)$c$, $c$BPHS, Sloka 2-4 as printed - bphs:PG67:C1; Sloka 1-8 as printed - bphs:PG90:C1 (Santhanam trans.)$c$),
      ($c$D3$c$, $c$BPHS Ch.6 (Shodasha-varga-adhyaya)$c$, $c$BPHS, Sloka 2-4 as printed - bphs:PG67:C1; Sloka 1-8 as printed - bphs:PG90:C1 (Santhanam trans.)$c$),
      ($c$D4$c$, $c$BPHS Ch.6 (Shodasha-varga-adhyaya)$c$, $c$BPHS, Sloka 2-4 as printed - bphs:PG67:C1; Sloka 1-8 as printed - bphs:PG91:C1 (Santhanam trans.)$c$),
      ($c$D7$c$, $c$BPHS Ch.6 (Shodasha-varga-adhyaya)$c$, $c$BPHS, Sloka 2-4 as printed - bphs:PG67:C1; Sloka 1-8 as printed - bphs:PG91:C1 (Santhanam trans.)$c$),
      ($c$D9$c$, $c$BPHS Ch.6 (Shodasha-varga-adhyaya)$c$, $c$BPHS, Sloka 2-4 as printed - bphs:PG67:C1; Sloka 1-8 as printed - bphs:PG91:C1 (Santhanam trans.)$c$),
      ($c$D10$c$, $c$BPHS Ch.6 (Shodasha-varga-adhyaya)$c$, $c$BPHS, Sloka 2-4 as printed - bphs:PG67:C1; Sloka 1-8 as printed - bphs:PG91:C1; Sloka 1-8 as printed, translator note - bphs:PG91:C1 (Santhanam trans.)$c$),
      ($c$D12$c$, $c$BPHS Ch.6 (Shodasha-varga-adhyaya)$c$, $c$BPHS, Sloka 2-4 as printed - bphs:PG67:C1; Sloka 1-8 as printed - bphs:PG91:C1 (Santhanam trans.)$c$),
      ($c$D16$c$, $c$BPHS Ch.6 (Shodasha-varga-adhyaya)$c$, $c$BPHS, Sloka 2-4 as printed - bphs:PG67:C1; Sloka 1-8 as printed - bphs:PG91:C1 (Santhanam trans.)$c$),
      ($c$D20$c$, $c$BPHS Ch.6 (Shodasha-varga-adhyaya)$c$, $c$BPHS, Sloka 2-4 as printed - bphs:PG67:C1; Sloka 1-8 as printed - bphs:PG91:C1 (Santhanam trans.)$c$),
      ($c$D24$c$, $c$BPHS Ch.6 (Shodasha-varga-adhyaya)$c$, $c$BPHS, Sloka 2-4 as printed - bphs:PG67:C1; Sloka 1-8 as printed - bphs:PG91:C1 (Santhanam trans.)$c$),
      ($c$D27$c$, $c$BPHS Ch.6 (Shodasha-varga-adhyaya)$c$, $c$BPHS, Sloka 2-4 as printed - bphs:PG67:C1; Sloka 1-8 as printed - bphs:PG91:C1; Sloka 24-26 as printed - bphs:PG77:C1 (Santhanam trans.)$c$),
      ($c$D30$c$, $c$BPHS Ch.6 (Shodasha-varga-adhyaya)$c$, $c$BPHS, Sloka 2-4 as printed - bphs:PG67:C1; Sloka 1-8 as printed - bphs:PG91:C1 (Santhanam trans.)$c$)
    ) AS v(varga_id, old_c, new_c)
    WHERE t.varga_id::text = v.varga_id AND t.source_citation = v.old_c;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n <> 13 THEN RAISE EXCEPTION 'curation expected 13 reference_vargas rows, updated %', n; END IF;
  UPDATE reference_upagrahas t SET source_citation = v.new_c
    FROM (VALUES
      ($c$gulika$c$, $c$BPHS Ch.3; Ch.5$c$, $c$BPHS, Sloka 65-70 as printed, translator note - bphs:PG44:C1; Sloka 70 as printed - bphs:PG45:C1 (Santhanam trans.)$c$),
      ($c$maandi$c$, $c$BPHS Ch.3; Ch.5$c$, $c$BPHS, Sloka 65-70 as printed, translator note - bphs:PG44:C1; Sloka 70 as printed - bphs:PG45:C1 (Santhanam trans.)$c$),
      ($c$dhuma$c$, $c$BPHS Ch.3$c$, $c$BPHS, Sloka 61-64 as printed - bphs:PG42:C1 (Santhanam trans.)$c$),
      ($c$vyatipata$c$, $c$BPHS Ch.3$c$, $c$BPHS, Sloka 61-64 as printed - bphs:PG42:C1 (Santhanam trans.)$c$),
      ($c$parivesha$c$, $c$BPHS Ch.3$c$, $c$BPHS, Sloka 61-64 as printed - bphs:PG42:C1 (Santhanam trans.)$c$),
      ($c$upaketu$c$, $c$BPHS Ch.3$c$, $c$BPHS, Sloka 61-64 as printed - bphs:PG42:C1 (Santhanam trans.)$c$),
      ($c$kala$c$, $c$BPHS Ch.3; Ch.5$c$, $c$BPHS, Sloka 65-70 as printed, translator note - bphs:PG44:C1; Sloka 70 as printed, translator note - bphs:PG45:C1 (Santhanam trans.)$c$),
      ($c$mrityu$c$, $c$BPHS Ch.3; Ch.5$c$, $c$BPHS, Sloka 65-70 as printed, translator note - bphs:PG44:C1; Sloka 70 as printed, translator note - bphs:PG45:C1 (Santhanam trans.)$c$),
      ($c$ardhaprahara$c$, $c$BPHS Ch.3; Ch.5$c$, $c$BPHS, Sloka 65-70 as printed, translator note - bphs:PG44:C1; Sloka 70 as printed, translator note - bphs:PG45:C1 (Santhanam trans.)$c$),
      ($c$yamaghantaka$c$, $c$BPHS Ch.3; Ch.5$c$, $c$BPHS, Sloka 65-70 as printed, translator note - bphs:PG44:C1; Sloka 70 as printed, translator note - bphs:PG45:C1 (Santhanam trans.)$c$)
    ) AS v(upagraha_id, old_c, new_c)
    WHERE t.upagraha_id::text = v.upagraha_id AND t.source_citation = v.old_c;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n <> 10 THEN RAISE EXCEPTION 'curation expected 10 reference_upagrahas rows, updated %', n; END IF;
  UPDATE reference_strength_systems t SET source_citation = v.new_c
    FROM (VALUES
      ($c$abdadhipa_bala$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 13 as printed - bphs:PG269:C1 (Santhanam trans.)$c$),
      ($c$masadhipa_bala$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 13 as printed - bphs:PG269:C1 (Santhanam trans.)$c$),
      ($c$varadhipa_bala$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 13 as printed - bphs:PG269:C1 (Santhanam trans.)$c$),
      ($c$horadhipa_bala$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 13 as printed - bphs:PG269:C1 (Santhanam trans.)$c$),
      ($c$kala_bala$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 8-9 as printed, translator note - bphs:PG267:C1 (Santhanam trans.)$c$),
      ($c$sthana_bala$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 1 as printed, translator note - bphs:PG263:C1; Sloka 6 as printed, translator note - bphs:PG266:C1 (Santhanam trans.)$c$),
      ($c$kendradi_bala$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 5 as printed - bphs:PG265:C1 (Santhanam trans.)$c$),
      ($c$naisargika_bala$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 14 as printed - bphs:PG275:C1; Sloka 14 as printed, translator note - bphs:PG275:C1 (Santhanam trans.)$c$),
      ($c$nathonnatha_bala$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 8-9 as printed, translator note - bphs:PG267:C1; Sloka 8-9 as printed - bphs:PG267:C1 (Santhanam trans.)$c$),
      ($c$paksha_bala$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 10-11 as printed - bphs:PG268:C1 (Santhanam trans.)$c$),
      ($c$tribhaga_bala$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 12 as printed - bphs:PG268:C1, bphs:PG268:C2 (Santhanam trans.)$c$),
      ($c$ojhayugma_bala$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 4½ as printed - bphs:PG264:C2; Sloka 4½ as printed, translator note - bphs:PG265:C1 (Santhanam trans.)$c$),
      ($c$dig_bala$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 7-7½ as printed - bphs:PG266:C1; Sloka 7-7½ as printed, translator note - bphs:PG266:C1 (Santhanam trans.)$c$),
      ($c$graha_drishti_value$c$, $c$BPHS Ch.26$c$, $c$BPHS, Sloka 2-5 as printed - bphs:PG254:C1 (Santhanam trans.)$c$),
      ($c$drik_bala$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 19 as printed - bphs:PG283:C1 (Santhanam trans.)$c$),
      ($c$bhavadhipati_bala$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 26-29 as printed - bphs:PG285:C1 (Santhanam trans.)$c$),
      ($c$bhava_drishti_bala$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 26-29 as printed - bphs:PG285:C1 (Santhanam trans.)$c$),
      ($c$bhinnashtakavarga$c$, $c$BPHS Ch.66-72$c$, $c$BPHS, Sloka 1-2 as printed - bphs:PG859:C1; p.891 - bphs:PG891:C1 (Santhanam trans.)$c$),
      ($c$trikona_shodhana$c$, $c$BPHS Ch.66-72$c$, $c$BPHS, Sloka 1-2 as printed - bphs:PG859:C1 (Santhanam trans.)$c$),
      ($c$ekadhipatya_shodhana$c$, $c$BPHS Ch.66-72$c$, $c$BPHS, Sloka 1-5 as printed - bphs:PG867:C1 (Santhanam trans.)$c$),
      ($c$shodhya_pinda$c$, $c$BPHS Ch.66-72$c$, $c$BPHS, p.880 - bphs:PG880:C1, bphs:PG874:C1 (Santhanam trans.)$c$),
      ($c$vimsopaka_bala$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 17-19 as printed - bphs:PG94:C1; Sloka 21-25 as printed - bphs:PG95:C1 (Santhanam trans.)$c$),
      ($c$vimsottari_weight$c$, $c$BPHS Ch.46$c$, $c$BPHS, Sloka 12-14 as printed, translator note - bphs:PG499:C1; Sloka 15 as printed - bphs:PG499:C1, bphs:PG499:C2 (Santhanam trans.)$c$),
      ($c$yuddha_bala$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 20 as printed - bphs:PG283:C1 (Santhanam trans.); Phaladipika, Adh. IV, Sloka 2 as printed - phaladeepika:PG71:C1 (Sastri trans. 1950)$c$),
      ($c$kashta_phala$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 6 as printed - bphs:PG289:C1 (Santhanam trans.)$c$)
    ) AS v(strength_id, old_c, new_c)
    WHERE t.strength_id::text = v.strength_id AND t.source_citation = v.old_c;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n <> 25 THEN RAISE EXCEPTION 'curation expected 25 reference_strength_systems rows, updated %', n; END IF;
  UPDATE reference_karakas t SET source_citation = v.new_c
    FROM (VALUES
      ($c$atmakaraka$c$, $c$Jaimini Sutram Ch.1$c$, $c$Jaimini Sutras, Sloka 11 as printed — bphs_jaimini:PG29:C1 (Suryanarain Rao trans. 1949) ; BPHS, Sloka 3-8 as printed — bphs:PG316:C1 (Santhanam trans.)$c$),
      ($c$amatyakaraka$c$, $c$Jaimini Sutram Ch.1$c$, $c$Jaimini Sutras, Sloka 13 as printed — bphs_jaimini:PG35:C1 (Suryanarain Rao trans. 1949) ; Jaimini Sutras, Sloka 13 (Notes) as printed — bphs_jaimini:PG36:C1 (Suryanarain Rao trans. 1949)$c$),
      ($c$bhratrikaraka$c$, $c$Jaimini Sutram Ch.1$c$, $c$Jaimini Sutras, Sloka 14 as printed — bphs_jaimini:PG36:C1 (Suryanarain Rao trans. 1949)$c$),
      ($c$matrikaraka$c$, $c$Jaimini Sutram Ch.1$c$, $c$Jaimini Sutras, Sloka 15 as printed — bphs_jaimini:PG36:C1 (Suryanarain Rao trans. 1949)$c$),
      ($c$putrakaraka$c$, $c$Jaimini Sutram Ch.1$c$, $c$Jaimini Sutras, Sloka 16 as printed — bphs_jaimini:PG37:C1 (Suryanarain Rao trans. 1949) ; Jaimini Sutras, Sloka 19 as printed — bphs_jaimini:PG39:C1 (Suryanarain Rao trans. 1949)$c$),
      ($c$gnatikaraka$c$, $c$Jaimini Sutram Ch.1$c$, $c$Jaimini Sutras, Sloka 17 as printed — bphs_jaimini:PG38:C1 (Suryanarain Rao trans. 1949)$c$),
      ($c$darakaraka$c$, $c$Jaimini Sutram Ch.1$c$, $c$Jaimini Sutras, Sloka 18 as printed — bphs_jaimini:PG38:C1 (Suryanarain Rao trans. 1949) ; BPHS, Sloka 13-17 (Notes) as printed — bphs:PG318:C1 (Santhanam trans.)$c$),
      ($c$karaka_children$c$, $c$BPHS Ch.27$c$, $c$Jaimini Sutras, Sloka 23 (Notes) as printed — bphs_jaimini:PG42:C1 (Suryanarain Rao trans. 1949) ; BPHS, Sloka 22-24 (Notes) as printed — bphs:PG320:C1 (Santhanam trans.) ; BPHS, Sloka 31-34 (Notes) as printed — bphs:PG324:C1 (Santhanam trans.)$c$),
      ($c$karaka_courage$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 31-34 (Notes) as printed — bphs:PG324:C1 (Santhanam trans.)$c$),
      ($c$karaka_dharma$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 31-34 (Notes) as printed — bphs:PG324:C1 (Santhanam trans.)$c$),
      ($c$karaka_fame$c$, $c$BPHS Ch.27$c$, $c$Jaimini Sutras, Sloka 23 (Notes) as printed — bphs_jaimini:PG42:C1 (Suryanarain Rao trans. 1949)$c$),
      ($c$karaka_father$c$, $c$BPHS Ch.27$c$, $c$Jaimini Sutras, Sloka 23 (Notes) as printed — bphs_jaimini:PG42:C1 (Suryanarain Rao trans. 1949) ; BPHS, Sloka 18-21 (Notes) as printed — bphs:PG319:C1 (Santhanam trans.) ; BPHS, Sloka 22-24 as printed — bphs:PG320:C1 (Santhanam trans.) ; BPHS, Sloka 31-34 (Notes) as printed — bphs:PG324:C1 (Santhanam trans.) ; BPHS, Sloka 11 as printed — bphs:PG121:C1 (Santhanam trans.)$c$),
      ($c$karaka_food$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 3 as printed — bphs:PG120:C1 (Santhanam trans.) ; BPHS, Sloka 31-34 (Notes) as printed — bphs:PG324:C1 (Santhanam trans.)$c$),
      ($c$karaka_gains$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 12 as printed — bphs:PG122:C1 (Santhanam trans.) ; BPHS, Sloka 31-34 (Notes) as printed — bphs:PG324:C1 (Santhanam trans.)$c$),
      ($c$karaka_government$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 14-15 as printed — bphs:PG27:C1 (Santhanam trans.)$c$),
      ($c$karaka_grief$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 12-13 (Notes) as printed — bphs:PG27:C1 (Santhanam trans.)$c$),
      ($c$karaka_higher_learning$c$, $c$BPHS Ch.27$c$, $c$Jaimini Sutras, Sloka 23 (Notes) as printed — bphs_jaimini:PG42:C1 (Suryanarain Rao trans. 1949) ; BPHS, Sloka 12-13 (Notes) as printed — bphs:PG27:C1 (Santhanam trans.)$c$),
      ($c$karaka_home$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 31-34 (Notes) as printed — bphs:PG324:C1 (Santhanam trans.) ; BPHS, Sloka 5 as printed — bphs:PG120:C1 (Santhanam trans.)$c$),
      ($c$karaka_inheritance$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 31-34 (Notes) as printed — bphs:PG324:C1 (Santhanam trans.) ; BPHS, Sloka 9 as printed — bphs:PG121:C1 (Santhanam trans.)$c$),
      ($c$karaka_intelligence$c$, $c$BPHS Ch.27$c$, $c$Jaimini Sutras, Sloka 23 (Notes) as printed — bphs_jaimini:PG42:C1 (Suryanarain Rao trans. 1949)$c$),
      ($c$karaka_land$c$, $c$BPHS Ch.27$c$, $c$Jaimini Sutras, Sloka 23 (Notes) as printed — bphs_jaimini:PG42:C1 (Suryanarain Rao trans. 1949)$c$),
      ($c$karaka_longevity$c$, $c$BPHS Ch.27$c$, $c$Jaimini Sutras, Sloka 23 (Notes) as printed — bphs_jaimini:PG43:C1 (Suryanarain Rao trans. 1949) ; BPHS, Sloka 22-24 (Notes) as printed — bphs:PG320:C1 (Santhanam trans.)$c$),
      ($c$karaka_losses$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 31-34 (Notes) as printed — bphs:PG324:C1 (Santhanam trans.)$c$),
      ($c$karaka_marriage$c$, $c$BPHS Ch.27$c$, $c$Jaimini Sutras, Sloka 23 (Notes) as printed — bphs_jaimini:PG42:C1 (Suryanarain Rao trans. 1949) ; BPHS, Sloka 22-24 (Notes) as printed — bphs:PG320:C1 (Santhanam trans.) ; BPHS, Sloka 31-34 (Notes) as printed — bphs:PG324:C1 (Santhanam trans.)$c$),
      ($c$karaka_mind$c$, $c$BPHS Ch.27$c$, $c$Jaimini Sutras, Sloka 23 (Notes) as printed — bphs_jaimini:PG42:C1 (Suryanarain Rao trans. 1949)$c$),
      ($c$karaka_mother$c$, $c$BPHS Ch.27$c$, $c$Jaimini Sutras, Sloka 23 (Notes) as printed — bphs_jaimini:PG42:C1 (Suryanarain Rao trans. 1949) ; BPHS, Sloka 18-21 (Notes) as printed — bphs:PG319:C1 (Santhanam trans.) ; BPHS, Sloka 22-24 as printed — bphs:PG320:C1 (Santhanam trans.)$c$),
      ($c$karaka_passion$c$, $c$BPHS Ch.27$c$, $c$Jaimini Sutras, Sloka 23 (Notes) as printed — bphs_jaimini:PG42:C1 (Suryanarain Rao trans. 1949)$c$),
      ($c$karaka_pilgrimage$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 10 as printed — bphs:PG121:C1 (Santhanam trans.) ; BPHS, Sloka 31-34 (Notes) as printed — bphs:PG324:C1 (Santhanam trans.)$c$),
      ($c$karaka_pleasure$c$, $c$BPHS Ch.27$c$, $c$Jaimini Sutras, Sloka 23 (Notes) as printed — bphs_jaimini:PG42:C1 (Suryanarain Rao trans. 1949)$c$),
      ($c$karaka_progeny$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 31-34 (Notes) as printed — bphs:PG324:C1 (Santhanam trans.) ; BPHS, Sloka 22-24 (Notes) as printed — bphs:PG320:C1 (Santhanam trans.)$c$),
      ($c$karaka_property$c$, $c$BPHS Ch.27$c$, $c$Jaimini Sutras, Sloka 23 (Notes) as printed — bphs_jaimini:PG42:C1 (Suryanarain Rao trans. 1949)$c$),
      ($c$karaka_relatives$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 22-24 (Notes) as printed — bphs:PG320:C1 (Santhanam trans.) ; Jaimini Sutras, Sloka 21 as printed — bphs_jaimini:PG41:C1 (Suryanarain Rao trans. 1949)$c$),
      ($c$karaka_romance$c$, $c$BPHS Ch.27$c$, $c$Jaimini Sutras, Sloka 23 (Notes) as printed — bphs_jaimini:PG42:C1 (Suryanarain Rao trans. 1949)$c$),
      ($c$karaka_servants$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 14-15 as printed — bphs:PG27:C1 (Santhanam trans.)$c$),
      ($c$karaka_spirituality$c$, $c$BPHS Ch.27$c$, $c$Jaimini Sutras, Sloka 23 (Notes) as printed — bphs_jaimini:PG43:C1 (Suryanarain Rao trans. 1949) ; Jaimini Sutras, Sloka 23 (Notes) as printed — bphs_jaimini:PG42:C1 (Suryanarain Rao trans. 1949)$c$),
      ($c$karaka_spouse$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 22-24 (Notes) as printed — bphs:PG320:C1 (Santhanam trans.) ; Jaimini Sutras, Sloka 23 (Notes) as printed — bphs_jaimini:PG42:C1 (Suryanarain Rao trans. 1949) ; BPHS, Sloka 31-34 (Notes) as printed — bphs:PG324:C1 (Santhanam trans.)$c$),
      ($c$karaka_status$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 14-15 as printed — bphs:PG27:C1 (Santhanam trans.)$c$),
      ($c$karaka_vitality$c$, $c$BPHS Ch.27$c$, $c$Jaimini Sutras, Sloka 23 (Notes) as printed — bphs_jaimini:PG42:C1 (Suryanarain Rao trans. 1949)$c$),
      ($c$karaka_wealth$c$, $c$BPHS Ch.27$c$, $c$Jaimini Sutras, Sloka 23 (Notes) as printed — bphs_jaimini:PG42:C1 (Suryanarain Rao trans. 1949) ; BPHS, Sloka 31-34 (Notes) as printed — bphs:PG324:C1 (Santhanam trans.)$c$),
      ($c$karaka_wealth_accumulated$c$, $c$BPHS Ch.27$c$, $c$Jaimini Sutras, Sloka 23 (Notes) as printed — bphs_jaimini:PG42:C1 (Suryanarain Rao trans. 1949)$c$),
      ($c$karaka_wisdom$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 12-13 (Notes) as printed — bphs:PG27:C1 (Santhanam trans.) ; Jaimini Sutras, Sloka 23 (Notes) as printed — bphs_jaimini:PG42:C1 (Suryanarain Rao trans. 1949)$c$),
      ($c$karaka_younger_siblings$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 18-21 as printed — bphs:PG319:C1 (Santhanam trans.) ; Jaimini Sutras, Sloka 20 as printed — bphs_jaimini:PG40:C1 (Suryanarain Rao trans. 1949) ; BPHS, Sloka 31-34 (Notes) as printed — bphs:PG324:C1 (Santhanam trans.)$c$)
    ) AS v(karaka_id, old_c, new_c)
    WHERE t.karaka_id::text = v.karaka_id AND t.source_citation = v.old_c;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n <> 42 THEN RAISE EXCEPTION 'curation expected 42 reference_karakas rows, updated %', n; END IF;
  UPDATE reference_constants t SET source_citation = v.new_c
    FROM (VALUES
      ($c$ashtakavarga_jupiter_from_jupiter$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 53-55 as printed — bphs:PG852:C1 (Santhanam trans.) ; BPHS, Sloka 31-34 as printed — bphs:PG843:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_jupiter_from_lagna$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 53-55 as printed — bphs:PG852:C1 (Santhanam trans.) ; BPHS, Sloka 31-34 as printed — bphs:PG843:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_jupiter_from_mars$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 53-55 as printed — bphs:PG852:C1 (Santhanam trans.) ; BPHS, Sloka 31-34 as printed — bphs:PG843:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_jupiter_from_mercury$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 53-55 as printed — bphs:PG852:C1 (Santhanam trans.) ; BPHS, Sloka 31-34 as printed — bphs:PG843:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_jupiter_from_moon$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 53-55 as printed — bphs:PG852:C1 (Santhanam trans.) ; BPHS, Sloka 31-34 as printed — bphs:PG843:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_jupiter_from_saturn$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 53-55 as printed — bphs:PG852:C1 (Santhanam trans.) ; BPHS, Sloka 31-34 as printed — bphs:PG843:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_jupiter_from_sun$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 53-55 as printed — bphs:PG852:C1 (Santhanam trans.) ; BPHS, Sloka 31-34 as printed — bphs:PG843:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_jupiter_from_venus$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 53-55 as printed — bphs:PG852:C1 (Santhanam trans.) ; BPHS, Sloka 31-34 as printed — bphs:PG843:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_lagna_from_jupiter$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 65-68 as printed — bphs:PG857:C1 (Santhanam trans.) ; BPHS, Sloka 61-64 as printed — bphs:PG855:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_lagna_from_lagna$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 65-68 as printed — bphs:PG857:C1 (Santhanam trans.) ; BPHS, Sloka 61-64 as printed — bphs:PG855:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_lagna_from_mars$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 65-68 as printed — bphs:PG857:C1 (Santhanam trans.) ; BPHS, Sloka 61-64 as printed — bphs:PG855:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_lagna_from_mercury$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 65-68 as printed — bphs:PG857:C1 (Santhanam trans.) ; BPHS, Sloka 61-64 as printed — bphs:PG855:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_lagna_from_moon$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 65-68 as printed — bphs:PG857:C1 (Santhanam trans.) ; BPHS, Sloka 61-64 as printed — bphs:PG855:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_lagna_from_saturn$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 65-68 as printed — bphs:PG857:C1 (Santhanam trans.) ; BPHS, Sloka 61-64 as printed — bphs:PG855:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_lagna_from_sun$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 65-68 as printed — bphs:PG857:C1 (Santhanam trans.) ; BPHS, Sloka 61-64 as printed — bphs:PG855:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_lagna_from_venus$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 65-68 as printed — bphs:PG857:C1 (Santhanam trans.) ; BPHS, Sloka 61-64 as printed — bphs:PG855:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_mars_from_jupiter$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 49-50 as printed — bphs:PG849:C1 (Santhanam trans.) ; BPHS, Sloka 23-27 as printed — bphs:PG841:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_mars_from_lagna$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 49-50 as printed — bphs:PG849:C1 (Santhanam trans.) ; BPHS, Sloka 23-27 as printed — bphs:PG841:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_mars_from_mars$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 49-50 as printed — bphs:PG849:C1 (Santhanam trans.) ; BPHS, Sloka 23-27 as printed — bphs:PG841:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_mars_from_mercury$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 49-50 as printed — bphs:PG849:C1 (Santhanam trans.) ; BPHS, Sloka 23-27 as printed — bphs:PG841:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_mars_from_moon$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 49-50 as printed — bphs:PG849:C1 (Santhanam trans.) ; BPHS, Sloka 23-27 as printed — bphs:PG841:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_mars_from_saturn$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 49-50 as printed — bphs:PG849:C1 (Santhanam trans.) ; BPHS, Sloka 23-27 as printed — bphs:PG841:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_mars_from_sun$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 49-50 as printed — bphs:PG849:C1 (Santhanam trans.) ; BPHS, Sloka 23-27 as printed — bphs:PG841:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_mars_from_venus$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 49-50 as printed — bphs:PG849:C1 (Santhanam trans.) ; BPHS, Sloka 23-27 as printed — bphs:PG841:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_mercury_from_jupiter$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 51-52 as printed — bphs:PG850:C1 (Santhanam trans.) ; BPHS, Sloka 28-30 as printed — bphs:PG842:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_mercury_from_lagna$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 51-52 as printed — bphs:PG850:C1 (Santhanam trans.) ; BPHS, Sloka 28-30 as printed — bphs:PG842:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_mercury_from_mars$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 51-52 as printed — bphs:PG850:C1 (Santhanam trans.) ; BPHS, Sloka 28-30 as printed — bphs:PG842:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_mercury_from_mercury$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 51-52 as printed — bphs:PG850:C1 (Santhanam trans.) ; BPHS, Sloka 28-30 as printed — bphs:PG842:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_mercury_from_moon$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 51-52 as printed — bphs:PG850:C1 (Santhanam trans.) ; BPHS, Sloka 28-30 as printed — bphs:PG842:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_mercury_from_venus$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 51-52 as printed — bphs:PG850:C1 (Santhanam trans.) ; BPHS, Sloka 28-30 as printed — bphs:PG842:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_moon_from_lagna$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 46-48 as printed — bphs:PG848:C1 (Santhanam trans.) ; BPHS, Sloka 20-22 as printed — bphs:PG839:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_moon_from_mercury$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 46-48 as printed — bphs:PG848:C1 (Santhanam trans.) ; BPHS, Sloka 20-22 as printed — bphs:PG839:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_moon_from_saturn$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 46-48 as printed — bphs:PG848:C1 (Santhanam trans.) ; BPHS, Sloka 20-22 as printed — bphs:PG839:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_moon_from_sun$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 46-48 as printed — bphs:PG848:C1 (Santhanam trans.) ; BPHS, Sloka 20-22 as printed — bphs:PG839:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_moon_from_venus$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 46-48 as printed — bphs:PG848:C1 (Santhanam trans.) ; BPHS, Sloka 20-22 as printed — bphs:PG839:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_saturn_from_jupiter$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 59-60 as printed — bphs:PG854:C1 (Santhanam trans.) ; BPHS, Sloka 39-42 as printed — bphs:PG845:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_saturn_from_lagna$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 59-60 as printed — bphs:PG854:C1 (Santhanam trans.) ; BPHS, Sloka 39-42 as printed — bphs:PG845:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_saturn_from_mars$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 59-60 as printed — bphs:PG854:C1 (Santhanam trans.) ; BPHS, Sloka 39-42 as printed — bphs:PG845:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_saturn_from_mercury$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 59-60 as printed — bphs:PG854:C1 (Santhanam trans.) ; BPHS, Sloka 39-42 as printed — bphs:PG845:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_saturn_from_moon$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 59-60 as printed — bphs:PG854:C1 (Santhanam trans.) ; BPHS, Sloka 39-42 as printed — bphs:PG845:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_saturn_from_saturn$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 59-60 as printed — bphs:PG854:C1 (Santhanam trans.) ; BPHS, Sloka 39-42 as printed — bphs:PG845:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_saturn_from_sun$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 59-60 as printed — bphs:PG854:C1 (Santhanam trans.) ; BPHS, Sloka 39-42 as printed — bphs:PG845:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_saturn_from_venus$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 59-60 as printed — bphs:PG854:C1 (Santhanam trans.) ; BPHS, Sloka 39-42 as printed — bphs:PG845:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_sun_from_jupiter$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 43-45 as printed — bphs:PG846:C1 (Santhanam trans.) ; BPHS, Sloka 17-19 as printed — bphs:PG837:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_sun_from_lagna$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 43-45 as printed — bphs:PG846:C1 (Santhanam trans.) ; BPHS, Sloka 17-19 as printed — bphs:PG837:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_sun_from_mars$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 43-45 as printed — bphs:PG846:C1 (Santhanam trans.) ; BPHS, Sloka 17-19 as printed — bphs:PG837:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_sun_from_mercury$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 43-45 as printed — bphs:PG846:C1 (Santhanam trans.) ; BPHS, Sloka 17-19 as printed — bphs:PG837:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_sun_from_moon$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 43-45 as printed — bphs:PG846:C1 (Santhanam trans.) ; BPHS, Sloka 17-19 as printed — bphs:PG837:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_sun_from_saturn$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 43-45 as printed — bphs:PG846:C1 (Santhanam trans.) ; BPHS, Sloka 17-19 as printed — bphs:PG837:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_sun_from_sun$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 43-45 as printed — bphs:PG846:C1 (Santhanam trans.) ; BPHS, Sloka 17-19 as printed — bphs:PG837:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_sun_from_venus$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 43-45 as printed — bphs:PG846:C1 (Santhanam trans.) ; BPHS, Sloka 17-19 as printed — bphs:PG837:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_venus_from_jupiter$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 56-58 as printed — bphs:PG853:C1 (Santhanam trans.) ; BPHS, Sloka 35-38 as printed — bphs:PG844:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_venus_from_lagna$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 56-58 as printed — bphs:PG853:C1 (Santhanam trans.) ; BPHS, Sloka 35-38 as printed — bphs:PG844:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_venus_from_mercury$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 56-58 as printed — bphs:PG853:C1 (Santhanam trans.) ; BPHS, Sloka 35-38 as printed — bphs:PG844:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_venus_from_moon$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 56-58 as printed — bphs:PG853:C1 (Santhanam trans.) ; BPHS, Sloka 35-38 as printed — bphs:PG844:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_venus_from_saturn$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 56-58 as printed — bphs:PG853:C1 (Santhanam trans.) ; BPHS, Sloka 35-38 as printed — bphs:PG844:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_venus_from_sun$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 56-58 as printed — bphs:PG853:C1 (Santhanam trans.) ; BPHS, Sloka 35-38 as printed — bphs:PG844:C1 (Santhanam trans.)$c$),
      ($c$ashtakavarga_venus_from_venus$c$, $c$BPHS Ch.66$c$, $c$BPHS, Sloka 56-58 as printed — bphs:PG853:C1 (Santhanam trans.) ; BPHS, Sloka 35-38 as printed — bphs:PG844:C1 (Santhanam trans.)$c$),
      ($c$vimshottari_years_sun$c$, $c$BPHS Ch.46$c$, $c$BPHS, Sloka 15 as printed — bphs:PG499:C1 (Santhanam trans.) ; BPHS, Sloka 15 as printed — bphs:PG499:C2 (Santhanam trans.)$c$),
      ($c$vimshottari_years_moon$c$, $c$BPHS Ch.46$c$, $c$BPHS, Sloka 15 as printed — bphs:PG499:C1 (Santhanam trans.) ; BPHS, Sloka 15 as printed — bphs:PG499:C2 (Santhanam trans.)$c$),
      ($c$vimshottari_years_mars$c$, $c$BPHS Ch.46$c$, $c$BPHS, Sloka 15 as printed — bphs:PG499:C1 (Santhanam trans.) ; BPHS, Sloka 15 as printed — bphs:PG499:C2 (Santhanam trans.)$c$),
      ($c$vimshottari_years_rahu$c$, $c$BPHS Ch.46$c$, $c$BPHS, Sloka 15 as printed — bphs:PG499:C1 (Santhanam trans.) ; BPHS, Sloka 15 as printed — bphs:PG499:C2 (Santhanam trans.)$c$),
      ($c$vimshottari_years_jupiter$c$, $c$BPHS Ch.46$c$, $c$BPHS, Sloka 15 as printed — bphs:PG499:C1 (Santhanam trans.) ; BPHS, Sloka 15 as printed — bphs:PG499:C2 (Santhanam trans.)$c$),
      ($c$vimshottari_years_saturn$c$, $c$BPHS Ch.46$c$, $c$BPHS, Sloka 15 as printed — bphs:PG499:C1 (Santhanam trans.) ; BPHS, Sloka 15 as printed — bphs:PG499:C2 (Santhanam trans.)$c$),
      ($c$vimshottari_years_mercury$c$, $c$BPHS Ch.46$c$, $c$BPHS, Sloka 15 as printed — bphs:PG499:C1 (Santhanam trans.) ; BPHS, Sloka 15 as printed — bphs:PG499:C2 (Santhanam trans.)$c$),
      ($c$vimshottari_years_ketu$c$, $c$BPHS Ch.46$c$, $c$BPHS, Sloka 15 as printed — bphs:PG499:C1 (Santhanam trans.) ; BPHS, Sloka 15 as printed — bphs:PG499:C2 (Santhanam trans.)$c$),
      ($c$vimshottari_years_venus$c$, $c$BPHS Ch.46$c$, $c$BPHS, Sloka 15 as printed — bphs:PG499:C1 (Santhanam trans.) ; BPHS, Sloka 15 as printed — bphs:PG499:C2 (Santhanam trans.)$c$),
      ($c$vimshottari_total$c$, $c$BPHS Ch.46$c$, $c$BPHS, p.505 — bphs:PG505:C1 (Santhanam trans.)$c$),
      ($c$exalt_deg_sun$c$, $c$BPHS Ch.3$c$, $c$BPHS, Sloka 49-50 as printed — bphs:PG37:C2 (Santhanam trans.) ; BPHS, Sloka 49-50 as printed — bphs:PG38:C1 (Santhanam trans.)$c$),
      ($c$exalt_deg_moon$c$, $c$BPHS Ch.3$c$, $c$BPHS, Sloka 49-50 as printed — bphs:PG37:C2 (Santhanam trans.) ; BPHS, Sloka 49-50 as printed — bphs:PG38:C1 (Santhanam trans.)$c$),
      ($c$exalt_deg_mars$c$, $c$BPHS Ch.3$c$, $c$BPHS, Sloka 49-50 as printed — bphs:PG38:C1 (Santhanam trans.) ; BPHS, Sloka 49-50 as printed — bphs:PG37:C2 (Santhanam trans.)$c$),
      ($c$exalt_deg_mercury$c$, $c$BPHS Ch.3$c$, $c$BPHS, Sloka 49-50 as printed — bphs:PG37:C2 (Santhanam trans.) ; BPHS, Sloka 49-50 as printed — bphs:PG38:C1 (Santhanam trans.)$c$),
      ($c$exalt_deg_jupiter$c$, $c$BPHS Ch.3$c$, $c$BPHS, Sloka 49-50 as printed — bphs:PG37:C2 (Santhanam trans.) ; BPHS, Sloka 49-50 as printed — bphs:PG38:C1 (Santhanam trans.)$c$),
      ($c$exalt_deg_venus$c$, $c$BPHS Ch.3$c$, $c$BPHS, Sloka 49-50 as printed — bphs:PG37:C2 (Santhanam trans.) ; BPHS, Sloka 49-50 as printed — bphs:PG38:C1 (Santhanam trans.)$c$),
      ($c$exalt_deg_saturn$c$, $c$BPHS Ch.3$c$, $c$BPHS, Sloka 49-50 as printed — bphs:PG37:C2 (Santhanam trans.) ; BPHS, Sloka 49-50 as printed — bphs:PG38:C1 (Santhanam trans.)$c$),
      ($c$debil_deg_sun$c$, $c$BPHS Ch.3$c$, $c$BPHS, Sloka 49-50 as printed — bphs:PG38:C1 (Santhanam trans.)$c$),
      ($c$debil_deg_moon$c$, $c$BPHS Ch.3$c$, $c$BPHS, Sloka 49-50 as printed — bphs:PG38:C1 (Santhanam trans.)$c$),
      ($c$debil_deg_mars$c$, $c$BPHS Ch.3$c$, $c$BPHS, Sloka 49-50 as printed — bphs:PG38:C1 (Santhanam trans.)$c$),
      ($c$debil_deg_mercury$c$, $c$BPHS Ch.3$c$, $c$BPHS, Sloka 49-50 as printed — bphs:PG38:C1 (Santhanam trans.)$c$),
      ($c$debil_deg_jupiter$c$, $c$BPHS Ch.3$c$, $c$BPHS, Sloka 49-50 as printed — bphs:PG38:C1 (Santhanam trans.)$c$),
      ($c$debil_deg_venus$c$, $c$BPHS Ch.3$c$, $c$BPHS, Sloka 49-50 as printed — bphs:PG38:C1 (Santhanam trans.)$c$),
      ($c$debil_deg_saturn$c$, $c$BPHS Ch.3$c$, $c$BPHS, Sloka 49-50 as printed — bphs:PG38:C1 (Santhanam trans.)$c$),
      ($c$moolatrikona_sun$c$, $c$BPHS Ch.3$c$, $c$BPHS, Sloka 51-54 as printed — bphs:PG38:C1 (Santhanam trans.)$c$),
      ($c$moolatrikona_moon$c$, $c$BPHS Ch.3$c$, $c$Hora Sara, p.18 — hora_sara:PG18:C1 (Santhanam trans.)  [cites Hora Sara; the BPHS Ch.3 moolatrikona line for the Moon is OCR-lost]$c$),
      ($c$moolatrikona_mars$c$, $c$BPHS Ch.3$c$, $c$BPHS, Sloka 51-54 as printed — bphs:PG38:C1 (Santhanam trans.)$c$),
      ($c$moolatrikona_mercury$c$, $c$BPHS Ch.3$c$, $c$BPHS, Sloka 51-54 as printed — bphs:PG38:C2 (Santhanam trans.)$c$),
      ($c$moolatrikona_jupiter$c$, $c$BPHS Ch.3$c$, $c$BPHS, Sloka 51-54 as printed — bphs:PG38:C2 (Santhanam trans.)$c$),
      ($c$moolatrikona_venus$c$, $c$BPHS Ch.3$c$, $c$BPHS, Sloka 51-54 as printed — bphs:PG38:C2 (Santhanam trans.)$c$),
      ($c$moolatrikona_saturn$c$, $c$BPHS Ch.3$c$, $c$BPHS, Sloka 51-54 as printed — bphs:PG38:C2 (Santhanam trans.)$c$),
      ($c$digbala_house_jupiter$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 7-71 as printed — bphs:PG266:C1 (Santhanam trans.)$c$),
      ($c$digbala_house_mercury$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 7-71 as printed — bphs:PG266:C1 (Santhanam trans.)$c$),
      ($c$digbala_house_moon$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 7-71 as printed — bphs:PG266:C1 (Santhanam trans.)$c$),
      ($c$digbala_house_venus$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 7-71 as printed — bphs:PG266:C1 (Santhanam trans.)$c$),
      ($c$digbala_house_saturn$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 7-71 as printed — bphs:PG266:C1 (Santhanam trans.)$c$),
      ($c$digbala_house_sun$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 7-71 as printed — bphs:PG266:C1 (Santhanam trans.)$c$),
      ($c$digbala_house_mars$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 7-71 as printed — bphs:PG266:C1 (Santhanam trans.)$c$),
      ($c$drishti_full$c$, $c$BPHS Ch.26$c$, $c$BPHS, Sloka 2-5 as printed — bphs:PG254:C1 (Santhanam trans.)$c$),
      ($c$drishti_half$c$, $c$BPHS Ch.26$c$, $c$BPHS, Sloka 2-5 as printed — bphs:PG254:C1 (Santhanam trans.)$c$),
      ($c$drishti_quarter$c$, $c$BPHS Ch.26$c$, $c$BPHS, Sloka 2-5 as printed — bphs:PG254:C1 (Santhanam trans.)$c$),
      ($c$drishti_three_quarter$c$, $c$BPHS Ch.26$c$, $c$BPHS, Sloka 2-5 as printed — bphs:PG254:C1 (Santhanam trans.)$c$),
      ($c$special_aspect_jupiter$c$, $c$BPHS Ch.26$c$, $c$BPHS, Sloka 2-5 as printed — bphs:PG254:C1 (Santhanam trans.)$c$),
      ($c$special_aspect_mars$c$, $c$BPHS Ch.26$c$, $c$BPHS, Sloka 2-5 as printed — bphs:PG254:C1 (Santhanam trans.)$c$),
      ($c$special_aspect_saturn$c$, $c$BPHS Ch.26$c$, $c$BPHS, Sloka 2-5 as printed — bphs:PG254:C1 (Santhanam trans.)$c$),
      ($c$naisargika_bala_sun$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 14 as printed — bphs:PG275:C1 (Santhanam trans.)$c$),
      ($c$naisargika_bala_moon$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 14 as printed — bphs:PG275:C1 (Santhanam trans.)$c$),
      ($c$naisargika_bala_venus$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 14 as printed — bphs:PG275:C1 (Santhanam trans.)$c$),
      ($c$naisargika_bala_jupiter$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 14 as printed — bphs:PG275:C1 (Santhanam trans.)$c$),
      ($c$naisargika_bala_mercury$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 14 as printed — bphs:PG275:C1 (Santhanam trans.)$c$),
      ($c$naisargika_bala_mars$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 14 as printed — bphs:PG275:C1 (Santhanam trans.)$c$),
      ($c$naisargika_bala_saturn$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 14 as printed — bphs:PG275:C1 (Santhanam trans.)$c$),
      ($c$own_sign_sun$c$, $c$BPHS Ch.1$c$, $c$BPHS, Sloka 12 as printed — bphs:PG50:C1 (Santhanam trans.)$c$),
      ($c$own_sign_moon$c$, $c$BPHS Ch.1$c$, $c$BPHS, Sloka 10-11 as printed — bphs:PG50:C1 (Santhanam trans.)$c$),
      ($c$own_sign_mars$c$, $c$BPHS Ch.1$c$, $c$BPHS, Sloka 6-7 as printed — bphs:PG49:C2 (Santhanam trans.) ; BPHS, Sloka 15-16 as printed — bphs:PG51:C1 (Santhanam trans.)$c$),
      ($c$own_sign_mercury$c$, $c$BPHS Ch.1$c$, $c$BPHS, Sloka 9-91 as printed — bphs:PG50:C1 (Santhanam trans.) ; BPHS, Sloka 13-14 as printed — bphs:PG51:C1 (Santhanam trans.)$c$),
      ($c$own_sign_jupiter$c$, $c$BPHS Ch.1$c$, $c$BPHS, Sloka 17-18 as printed — bphs:PG51:C1 (Santhanam trans.) ; BPHS, Sloka 22-24 as printed — bphs:PG52:C1 (Santhanam trans.)$c$),
      ($c$own_sign_venus$c$, $c$BPHS Ch.1$c$, $c$BPHS, Sloka 8 as printed — bphs:PG49:C2 (Santhanam trans.) ; BPHS, Sloka 15-16 as printed — bphs:PG51:C1 (Santhanam trans.)$c$),
      ($c$own_sign_saturn$c$, $c$BPHS Ch.1$c$, $c$BPHS, Sloka 19-20 as printed — bphs:PG51:C2 (Santhanam trans.) ; BPHS, Sloka 21-21t as printed — bphs:PG52:C1 (Santhanam trans.)$c$),
      ($c$drekkana_span$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 7-8 as printed — bphs:PG69:C1 (Santhanam trans.)$c$),
      ($c$hora_span$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 5-6 as printed — bphs:PG67:C1 (Santhanam trans.)$c$),
      ($c$karana_count$c$, $c$classical_tradition$c$, $c$Jataka Parijata, Sloka 101-102 as printed — jataka_parijata:PG648:C1 (Subramanya Shashtri trans. 1932-33) ; Jataka Parijata, Sloka 103 as printed — jataka_parijata:PG649:C1 (Subramanya Shashtri trans. 1932-33)$c$),
      ($c$nakshatra_count$c$, $c$classical_tradition$c$, $c$BPHS, Sloka 4-6 as printed — bphs:PG24:C1 (Santhanam trans.)$c$),
      ($c$nakshatra_span$c$, $c$classical_tradition$c$, $c$BPHS, p.501 — bphs:PG501:C1 (Santhanam trans.)$c$),
      ($c$pada_span$c$, $c$classical_tradition$c$, $c$BPHS, p.501 — bphs:PG501:C1 (Santhanam trans.)$c$),
      ($c$rasi_count$c$, $c$classical_tradition$c$, $c$BPHS, Sloka 4-6 as printed — bphs:PG24:C1 (Santhanam trans.)$c$),
      ($c$rasi_span$c$, $c$classical_tradition$c$, $c$BPHS, p.501 — bphs:PG501:C1 (Santhanam trans.)$c$),
      ($c$tithi_count$c$, $c$classical_tradition$c$, $c$Jataka Parijata, Sloka 29-30 as printed — jataka_parijata:PG616:C1 (Subramanya Shashtri trans. 1932-33)$c$),
      ($c$saptavargaja_moolatrikona$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 2-4 as printed — bphs:PG264:C1 (Santhanam trans.)$c$),
      ($c$saptavargaja_own$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 2-4 as printed — bphs:PG264:C1 (Santhanam trans.)$c$),
      ($c$saptavargaja_friend$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 2-4 as printed — bphs:PG264:C1 (Santhanam trans.)$c$),
      ($c$shadbala_min_sun$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 32-33 as printed — bphs:PG286:C1 (Santhanam trans.)$c$),
      ($c$shadbala_min_moon$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 32-33 as printed — bphs:PG286:C1 (Santhanam trans.)$c$),
      ($c$shadbala_min_mars$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 32-33 as printed — bphs:PG286:C1 (Santhanam trans.)$c$),
      ($c$shadbala_min_mercury$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 32-33 as printed — bphs:PG286:C1 (Santhanam trans.)$c$),
      ($c$shadbala_min_jupiter$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 32-33 as printed — bphs:PG286:C1 (Santhanam trans.)$c$),
      ($c$shadbala_min_venus$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 32-33 as printed — bphs:PG286:C1 (Santhanam trans.)$c$),
      ($c$shadbala_min_saturn$c$, $c$BPHS Ch.27$c$, $c$BPHS, Sloka 32-33 as printed — bphs:PG286:C1 (Santhanam trans.)$c$),
      ($c$varga_divisor_d2$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 5-6 as printed — bphs:PG67:C1 (Santhanam trans.)$c$),
      ($c$varga_divisor_d3$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 7-8 as printed — bphs:PG68:C1 (Santhanam trans.)$c$),
      ($c$varga_divisor_d4$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 9 as printed — bphs:PG69:C1 (Santhanam trans.)$c$),
      ($c$varga_divisor_d7$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 10-11 as printed — bphs:PG70:C1 (Santhanam trans.)$c$),
      ($c$varga_divisor_d9$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 12 as printed — bphs:PG71:C1 (Santhanam trans.)$c$),
      ($c$varga_divisor_d10$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 13-14 as printed — bphs:PG72:C1 (Santhanam trans.)$c$),
      ($c$varga_divisor_d12$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 15 as printed — bphs:PG72:C1 (Santhanam trans.)$c$),
      ($c$varga_divisor_d16$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 16 as printed — bphs:PG73:C1 (Santhanam trans.)$c$),
      ($c$varga_divisor_d20$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 17-21 as printed — bphs:PG75:C1 (Santhanam trans.)$c$),
      ($c$varga_divisor_d24$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 22-23 as printed — bphs:PG76:C1 (Santhanam trans.)$c$),
      ($c$varga_divisor_d27$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 24-26 as printed — bphs:PG78:C1 (Santhanam trans.)$c$),
      ($c$varga_divisor_d40$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 29-30 as printed — bphs:PG79:C1 (Santhanam trans.)$c$),
      ($c$varga_divisor_d45$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 31-32 as printed — bphs:PG80:C1 (Santhanam trans.)$c$),
      ($c$varga_divisor_d60$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 33-41 as printed — bphs:PG82:C1 (Santhanam trans.)$c$),
      ($c$vimshopaka_shadvarga_d1$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 17-19 as printed — bphs:PG94:C1 (Santhanam trans.)$c$),
      ($c$vimshopaka_shadvarga_d2$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 17-19 as printed — bphs:PG94:C1 (Santhanam trans.)$c$),
      ($c$vimshopaka_shadvarga_d3$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 17-19 as printed — bphs:PG94:C1 (Santhanam trans.)$c$),
      ($c$vimshopaka_shadvarga_d9$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 17-19 as printed — bphs:PG94:C1 (Santhanam trans.)$c$),
      ($c$vimshopaka_shadvarga_d12$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 17-19 as printed — bphs:PG94:C1 (Santhanam trans.)$c$),
      ($c$vimshopaka_shadvarga_d30$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 17-19 as printed — bphs:PG94:C1 (Santhanam trans.)$c$),
      ($c$vimshopaka_saptavarga_d1$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 17-19 as printed — bphs:PG94:C1 (Santhanam trans.)$c$),
      ($c$vimshopaka_saptavarga_d2$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 17-19 as printed — bphs:PG94:C1 (Santhanam trans.)$c$),
      ($c$vimshopaka_saptavarga_d3$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 17-19 as printed — bphs:PG94:C1 (Santhanam trans.)$c$),
      ($c$vimshopaka_saptavarga_d7$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 17-19 as printed — bphs:PG94:C1 (Santhanam trans.)$c$),
      ($c$vimshopaka_saptavarga_d9$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 17-19 as printed — bphs:PG94:C1 (Santhanam trans.)$c$),
      ($c$vimshopaka_saptavarga_d12$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 17-19 as printed — bphs:PG94:C1 (Santhanam trans.)$c$),
      ($c$vimshopaka_saptavarga_d30$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 17-19 as printed — bphs:PG94:C1 (Santhanam trans.)$c$),
      ($c$vimshopaka_dashavarga_d1$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 20 as printed — bphs:PG95:C1 (Santhanam trans.)$c$),
      ($c$vimshopaka_dashavarga_d2$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 20 as printed — bphs:PG95:C1 (Santhanam trans.)$c$),
      ($c$vimshopaka_dashavarga_d3$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 20 as printed — bphs:PG95:C1 (Santhanam trans.)$c$),
      ($c$vimshopaka_dashavarga_d7$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 20 as printed — bphs:PG95:C1 (Santhanam trans.)$c$),
      ($c$vimshopaka_dashavarga_d9$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 20 as printed — bphs:PG95:C1 (Santhanam trans.)$c$),
      ($c$vimshopaka_dashavarga_d10$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 20 as printed — bphs:PG95:C1 (Santhanam trans.)$c$),
      ($c$vimshopaka_dashavarga_d12$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 20 as printed — bphs:PG95:C1 (Santhanam trans.)$c$),
      ($c$vimshopaka_dashavarga_d16$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 20 as printed — bphs:PG95:C1 (Santhanam trans.)$c$),
      ($c$vimshopaka_dashavarga_d30$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 20 as printed — bphs:PG95:C1 (Santhanam trans.)$c$),
      ($c$vimshopaka_dashavarga_d60$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 20 as printed — bphs:PG95:C1 (Santhanam trans.)$c$),
      ($c$vimshopaka_shodashavarga_d1$c$, $c$BPHS Ch.7$c$, $c$BPHS, p.97 — bphs:PG97:C1 (Santhanam trans.)$c$),
      ($c$vimshopaka_shodashavarga_d2$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 21-25 as printed — bphs:PG95:C1 (Santhanam trans.)$c$),
      ($c$vimshopaka_shodashavarga_d3$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 21-25 as printed — bphs:PG95:C1 (Santhanam trans.)$c$),
      ($c$vimshopaka_shodashavarga_d4$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 21-25 as printed — bphs:PG95:C1 (Santhanam trans.)$c$),
      ($c$vimshopaka_shodashavarga_d7$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 21-25 as printed — bphs:PG95:C1 (Santhanam trans.)$c$),
      ($c$vimshopaka_shodashavarga_d9$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 21-25 as printed — bphs:PG95:C1 (Santhanam trans.)$c$),
      ($c$vimshopaka_shodashavarga_d10$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 21-25 as printed — bphs:PG95:C1 (Santhanam trans.)$c$),
      ($c$vimshopaka_shodashavarga_d12$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 21-25 as printed — bphs:PG95:C1 (Santhanam trans.)$c$),
      ($c$vimshopaka_shodashavarga_d16$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 21-25 as printed — bphs:PG95:C1 (Santhanam trans.)$c$),
      ($c$vimshopaka_shodashavarga_d20$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 21-25 as printed — bphs:PG95:C1 (Santhanam trans.)$c$),
      ($c$vimshopaka_shodashavarga_d24$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 21-25 as printed — bphs:PG95:C1 (Santhanam trans.)$c$),
      ($c$vimshopaka_shodashavarga_d27$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 21-25 as printed — bphs:PG95:C1 (Santhanam trans.)$c$),
      ($c$vimshopaka_shodashavarga_d30$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 21-25 as printed — bphs:PG95:C1 (Santhanam trans.)$c$),
      ($c$vimshopaka_shodashavarga_d40$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 21-25 as printed — bphs:PG95:C1 (Santhanam trans.)$c$),
      ($c$vimshopaka_shodashavarga_d45$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 21-25 as printed — bphs:PG95:C1 (Santhanam trans.)$c$),
      ($c$vimshopaka_shodashavarga_d60$c$, $c$BPHS Ch.7$c$, $c$BPHS, Sloka 21-25 as printed — bphs:PG95:C1 (Santhanam trans.)$c$)
    ) AS v(constant_id, old_c, new_c)
    WHERE t.constant_id::text = v.constant_id AND t.source_citation = v.old_c;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n <> 189 THEN RAISE EXCEPTION 'curation expected 189 reference_constants rows, updated %', n; END IF;

  -- post-flight
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t) - ARRAY[$v$created_at$v$]::text[])::text, E'\n' ORDER BY planet_id::text COLLATE "C"), '')) FROM reference_planets t$q$ INTO fp_0;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t) - ARRAY[$v$created_at$v$]::text[])::text, E'\n' ORDER BY sign_id::text COLLATE "C"), '')) FROM reference_signs t$q$ INTO fp_1;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY house_num::text COLLATE "C"), '')) FROM reference_houses t$q$ INTO fp_2;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t) - ARRAY[$v$created_at$v$]::text[])::text, E'\n' ORDER BY planet_id::text COLLATE "C",aspect_house::text COLLATE "C"), '')) FROM reference_aspects t$q$ INTO fp_3;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t) - ARRAY[$v$created_at$v$]::text[])::text, E'\n' ORDER BY varga_id::text COLLATE "C"), '')) FROM reference_vargas t$q$ INTO fp_4;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY upagraha_id::text COLLATE "C"), '')) FROM reference_upagrahas t$q$ INTO fp_5;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY strength_id::text COLLATE "C"), '')) FROM reference_strength_systems t$q$ INTO fp_6;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY karaka_id::text COLLATE "C"), '')) FROM reference_karakas t$q$ INTO fp_7;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY constant_id::text COLLATE "C"), '')) FROM reference_constants t$q$ INTO fp_8;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY term_id::text COLLATE "C"), '')) FROM reference_glossary t$q$ INTO fp_9;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY 1), '')) FROM reference_topic_tags t$q$ INTO fp_10;
  IF fp_0 IS DISTINCT FROM 'b24330881588405e3280d4d2ad06bea9' THEN RAISE EXCEPTION 'curation post-flight: reference_planets content fingerprint mismatch (%)', fp_0; END IF;
  IF fp_1 IS DISTINCT FROM '1929fa861aee5966bab4c2566f827a5d' THEN RAISE EXCEPTION 'curation post-flight: reference_signs content fingerprint mismatch (%)', fp_1; END IF;
  IF fp_2 IS DISTINCT FROM '42ce51f84e07e692a504299ab82594ec' THEN RAISE EXCEPTION 'curation post-flight: reference_houses content fingerprint mismatch (%)', fp_2; END IF;
  IF fp_3 IS DISTINCT FROM '4720cc744a390275bb514a45b875aec5' THEN RAISE EXCEPTION 'curation post-flight: reference_aspects content fingerprint mismatch (%)', fp_3; END IF;
  IF fp_4 IS DISTINCT FROM '7c6d4e2277a1e5dd70c956d9198c4d29' THEN RAISE EXCEPTION 'curation post-flight: reference_vargas content fingerprint mismatch (%)', fp_4; END IF;
  IF fp_5 IS DISTINCT FROM 'd792e78755ebe8cfbf82784b80dfcfcf' THEN RAISE EXCEPTION 'curation post-flight: reference_upagrahas content fingerprint mismatch (%)', fp_5; END IF;
  IF fp_6 IS DISTINCT FROM '453c0c04284632098e805090335cff90' THEN RAISE EXCEPTION 'curation post-flight: reference_strength_systems content fingerprint mismatch (%)', fp_6; END IF;
  IF fp_7 IS DISTINCT FROM '5a63e77928cefe1466e16e785c4d7dc6' THEN RAISE EXCEPTION 'curation post-flight: reference_karakas content fingerprint mismatch (%)', fp_7; END IF;
  IF fp_8 IS DISTINCT FROM '868811981c90dd570e3a28ae941767e4' THEN RAISE EXCEPTION 'curation post-flight: reference_constants content fingerprint mismatch (%)', fp_8; END IF;
  IF fp_9 IS DISTINCT FROM '08e69ca18715909f9bd3c4711fd0946e' THEN RAISE EXCEPTION 'curation post-flight: reference_glossary content fingerprint mismatch (%)', fp_9; END IF;
  IF fp_10 IS DISTINCT FROM 'af70b29a8842fba70ceb0da7710d00b2' THEN RAISE EXCEPTION 'curation post-flight: reference_topic_tags content fingerprint mismatch (%)', fp_10; END IF;

  -- reseal the stored integrity contract (its sha256 covers the changed tables)
  UPDATE asset_registry SET integrity_check_sql = replace(replace(replace(replace(replace(replace(replace(replace(replace(integrity_check_sql, '2a24fff91ac1c6fe56410769461c797d', '4e40a8e1c28f56c49c50fc65d7dbccc5'), 'd8384f552b0f9bd507fe1ac83fa8d5a0', 'c8e7e4a8d0b623f7969fda5239e9cfd6'), 'c92a24b7eda3fe2382bf3943a95ae900', 'b2dd1998171a96795939fe588781ec4e'), '6ea911e25c1592f24b7383e8c8ec5f16', '6e0e57e8b65cbe6cf7c27325991f1bca'), 'ba0be72447cf4e69ec249f7682fc6044', '80266a318b102ac0f2d772cc31ab93cb'), 'a62ee26273919321094aa3a9cc53b0cf', 'b618e1891d70fbd0ca127a5d5538ed70'), 'd5b06b1bd27fd7e9e853621b9779a964', '3715b7dbd06eaa7bd99c464fe6b2a561'), '3e089533a087c7540fcdde628524a27a', 'b4820981f3e285a5675d4fcfc0a91fb0'), 'ff504cadcd864211bf258b39eee2154b', 'b275ec96e14e3443284b608cf1f4113f') WHERE asset_id = 'bg_reference';
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n <> 1 THEN RAISE EXCEPTION 'curation expected 1 registry row, updated %', n; END IF;
  SELECT integrity_check_sql INTO ic FROM asset_registry WHERE asset_id = 'bg_reference';
  IF ic IS NOT NULL THEN
    EXECUTE ic INTO ok;
    IF ok IS NOT TRUE THEN RAISE EXCEPTION 'curation post-flight: bg_reference stored integrity_check_sql reads false'; END IF;
  END IF;
END
$curation$;
