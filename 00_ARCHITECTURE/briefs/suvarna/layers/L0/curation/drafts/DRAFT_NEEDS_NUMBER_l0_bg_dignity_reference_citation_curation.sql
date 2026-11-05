-- =============================================================================
-- DRAFT_NEEDS_NUMBER_l0_bg_dignity_reference_citation_curation.sql      (HELD DRAFT: NOT APPLIED, NOT A MIGRATION)
-- Lane: curation-lane (Exec Suvarna), branch suvarna/land/TI-curation-001, N-101 curation of bg_dignity_reference.
-- SS allocates the migration number (block 1200-1299).  Citation TEXT only: 82 rows across 5 table(s);
-- no value, key or other column changes.  Every proposed citation is chunk-level (corpus chunk id + page + printed
-- sloka) and each row's FACT/INFERENCE class and supporting quote are in the ledger
-- (assets/bg_dignity_reference_ledger.json); rows the held text CONTRADICTS are not touched (acharya batch).
-- GUARDS  per-table md5 fingerprint of every non-timestamp column must equal the pinned pre-state; every UPDATE
--         matches natural key AND exact old citation and must hit the exact expected row count; post-state
--         fingerprints are pinned; the asset integrity check does not hash these columns (no reseal needed);
--         idempotent: a second apply is a NOTICE + no-op.
-- Seed parity (NOT patched here; follow-up after SS review and PR #2984): platform/python-sidecar/pipeline/orchestrator/writers/bg_dignity_reference.py (static data, ON CONFLICT DO UPDATE)
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
  SELECT integrity_check_sql INTO ic FROM asset_registry WHERE asset_id = 'bg_dignity_reference' FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'curation refuses: asset_registry row bg_dignity_reference not found'; END IF;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY graha::text COLLATE "C"), '')) FROM bg_dignity_reference t$q$ INTO fp_0;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY graha::text COLLATE "C",other_graha::text COLLATE "C"), '')) FROM bg_graha_naisargika_friendship t$q$ INTO fp_1;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY scheme_name::text COLLATE "C",state_name::text COLLATE "C"), '')) FROM bg_avastha_schemes t$q$ INTO fp_2;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY graha::text COLLATE "C",motion_state::text COLLATE "C"), '')) FROM bg_motion_state_thresholds t$q$ INTO fp_3;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY graha::text COLLATE "C"), '')) FROM bg_combustion_orbs t$q$ INTO fp_4;
  IF fp_0 = '1a65bfe09aeebdcf1b8dc2a28f674155' AND fp_1 = 'b2048cc365d49af7558b7df52c5e0e96' AND fp_2 = '3d880a2848210299d4e9c2527f1c7822' AND fp_3 = '857df5bbf3e689179309b1ad15961c4b' AND fp_4 = 'b7de8c19765249fbf7367a81f8ecea4e' THEN
    RAISE NOTICE 'curation already applied: no-op';
    RETURN;
  END IF;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY graha::text COLLATE "C"), '')) FROM bg_dignity_reference t$q$ INTO fp_0;
  IF fp_0 IS DISTINCT FROM 'ad25feb1615129dcbacd55cbe0a4fd9f' THEN RAISE EXCEPTION 'curation refuses: bg_dignity_reference is not the pinned pre-state (%)', fp_0; END IF;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY graha::text COLLATE "C",other_graha::text COLLATE "C"), '')) FROM bg_graha_naisargika_friendship t$q$ INTO fp_1;
  IF fp_1 IS DISTINCT FROM '3b1cd145b9a3766eb3f345bd9c5bd315' THEN RAISE EXCEPTION 'curation refuses: bg_graha_naisargika_friendship is not the pinned pre-state (%)', fp_1; END IF;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY scheme_name::text COLLATE "C",state_name::text COLLATE "C"), '')) FROM bg_avastha_schemes t$q$ INTO fp_2;
  IF fp_2 IS DISTINCT FROM 'c9df7b63664e7161359025c9137ca07a' THEN RAISE EXCEPTION 'curation refuses: bg_avastha_schemes is not the pinned pre-state (%)', fp_2; END IF;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY graha::text COLLATE "C",motion_state::text COLLATE "C"), '')) FROM bg_motion_state_thresholds t$q$ INTO fp_3;
  IF fp_3 IS DISTINCT FROM '552a8efd23c8f2fc27d096befc6d0140' THEN RAISE EXCEPTION 'curation refuses: bg_motion_state_thresholds is not the pinned pre-state (%)', fp_3; END IF;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY graha::text COLLATE "C"), '')) FROM bg_combustion_orbs t$q$ INTO fp_4;
  IF fp_4 IS DISTINCT FROM '5ca410cf362d46f951162fb42063f745' THEN RAISE EXCEPTION 'curation refuses: bg_combustion_orbs is not the pinned pre-state (%)', fp_4; END IF;

  UPDATE bg_dignity_reference t SET classical_citation = v.new_c
    FROM (VALUES
      ($c$Sun$c$, $c$BPHS Ch.3$c$, $c$BPHS Chapter 3, Sloka 49-50 (exaltation, debilitation) and 51-54 (Moolatrikona, own) as printed — bphs:PG37:C2, bphs:PG38:C1, bphs:PG38:C2 (Santhanam trans.); own sign Leo: Phaladeepika Adh. I, Sloka 6 — phaladeepika:PG40:C1 (Sastri trans. 1950)$c$),
      ($c$Moon$c$, $c$BPHS Ch.3$c$, $c$BPHS Chapter 3, Sloka 49-50 (exaltation, debilitation) and 51-54 (Moolatrikona, own) as printed — bphs:PG37:C2, bphs:PG38:C1, bphs:PG38:C2 (Santhanam trans.); Moolatrikona 4-30: Phaladeepika Adh. I, Sloka 7 — phaladeepika:PG41:C1 (Sastri trans. 1950)$c$),
      ($c$Mars$c$, $c$BPHS Ch.3$c$, $c$BPHS Chapter 3, Sloka 49-50 (exaltation, debilitation) and 51-54 (Moolatrikona, own) as printed — bphs:PG37:C2, bphs:PG38:C1, bphs:PG38:C2 (Santhanam trans.); Moolatrikona named for Mars: Phaladeepika Adh. I, Sloka 7 — phaladeepika:PG41:C1 (Sastri trans. 1950)$c$),
      ($c$Mercury$c$, $c$BPHS Ch.3$c$, $c$BPHS Chapter 3, Sloka 49-50 (exaltation, debilitation) and 51-54 (Moolatrikona, own) as printed — bphs:PG37:C2, bphs:PG38:C1, bphs:PG38:C2 (Santhanam trans.); '16 to 20': Phaladeepika Adh. I, Sloka 7 — phaladeepika:PG41:C1 (Sastri trans. 1950)$c$),
      ($c$Jupiter$c$, $c$BPHS Ch.3$c$, $c$BPHS Chapter 3, Sloka 49-50 (exaltation, debilitation) and 51-54 (Moolatrikona, own) as printed — bphs:PG37:C2, bphs:PG38:C1, bphs:PG38:C2 (Santhanam trans.); Moolatrikona 0-10 also Phaladeepika Adh. I, Sloka 7 — phaladeepika:PG41:C1 (Sastri trans. 1950)$c$),
      ($c$Venus$c$, $c$BPHS Ch.3$c$, $c$BPHS Chapter 3, Sloka 49-50 (exaltation, debilitation) and 51-54 (Moolatrikona, own) as printed — bphs:PG37:C2, bphs:PG38:C1, bphs:PG38:C2 (Santhanam trans.)$c$),
      ($c$Saturn$c$, $c$BPHS Ch.3$c$, $c$BPHS Chapter 3, Sloka 49-50 (exaltation, debilitation) and 51-54 (Moolatrikona, own) as printed — bphs:PG37:C2, bphs:PG38:C1, bphs:PG38:C2 (Santhanam trans.)$c$),
      ($c$Rahu$c$, $c$BPHS Ch.3 (Santanam); Phaladeepika Ch.1; Saravali — Parashari consensus: Taurus$c$, $c$BPHS Chapter 47, Sloka 34-39 as printed — bphs:PG573:C2, bphs:PG574:C1, bphs:PG574:C2 (Santhanam trans.); variants: Hora Sara p.19 — hora_sara:PG19:C1 (Santhanam trans.)$c$),
      ($c$Ketu$c$, $c$BPHS Ch.3 (Santanam); Phaladeepika Ch.1; Saravali — reverse of Rahu$c$, $c$BPHS Chapter 47, Sloka 34-39 as printed — bphs:PG574:C1 (Santhanam trans.); debilitation (Taurus): Hora Sara p.19 — hora_sara:PG19:C1 (Santhanam trans.)$c$)
    ) AS v(graha, old_c, new_c)
    WHERE t.graha::text = v.graha AND t.classical_citation = v.old_c;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n <> 9 THEN RAISE EXCEPTION 'curation expected 9 bg_dignity_reference rows, updated %', n; END IF;
  UPDATE bg_graha_naisargika_friendship t SET classical_citation = v.new_c
    FROM (VALUES
      ($c$Sun$c$, $c$Moon$c$, $c$BPHS Ch.27$c$, $c$BPHS Chapter 3, Sloka 55 (natural relationships; table at PG39:C2, Moon note PG40:C1) as printed — bphs:PG39:C1 (Santhanam trans.); corroborated Uttara Kalamrita Ch. II p.28 — uttara_kalamrita:PG26:C1 (Sastri trans.)$c$),
      ($c$Sun$c$, $c$Mars$c$, $c$BPHS Ch.27$c$, $c$BPHS Chapter 3, Sloka 55 (natural relationships; table at PG39:C2, Moon note PG40:C1) as printed — bphs:PG39:C1 (Santhanam trans.); corroborated Uttara Kalamrita Ch. II p.28 — uttara_kalamrita:PG26:C1 (Sastri trans.)$c$),
      ($c$Sun$c$, $c$Jupiter$c$, $c$BPHS Ch.27$c$, $c$BPHS Chapter 3, Sloka 55 (natural relationships; table at PG39:C2, Moon note PG40:C1) as printed — bphs:PG39:C1 (Santhanam trans.); corroborated Uttara Kalamrita Ch. II p.28 — uttara_kalamrita:PG26:C1 (Sastri trans.)$c$),
      ($c$Sun$c$, $c$Mercury$c$, $c$BPHS Ch.27$c$, $c$BPHS Chapter 3, Sloka 55 (natural relationships; table at PG39:C2, Moon note PG40:C1) as printed — bphs:PG39:C1 (Santhanam trans.); corroborated Uttara Kalamrita Ch. II p.28 — uttara_kalamrita:PG26:C1 (Sastri trans.)$c$),
      ($c$Sun$c$, $c$Venus$c$, $c$BPHS Ch.27$c$, $c$BPHS Chapter 3, Sloka 55 (natural relationships; table at PG39:C2, Moon note PG40:C1) as printed — bphs:PG39:C1 (Santhanam trans.); corroborated Uttara Kalamrita Ch. II p.28 — uttara_kalamrita:PG26:C1 (Sastri trans.)$c$),
      ($c$Sun$c$, $c$Saturn$c$, $c$BPHS Ch.27$c$, $c$BPHS Chapter 3, Sloka 55 (natural relationships; table at PG39:C2, Moon note PG40:C1) as printed — bphs:PG39:C1 (Santhanam trans.); corroborated Uttara Kalamrita Ch. II p.28 — uttara_kalamrita:PG26:C1 (Sastri trans.)$c$),
      ($c$Moon$c$, $c$Sun$c$, $c$BPHS Ch.27$c$, $c$BPHS Chapter 3, Sloka 55 (natural relationships; table at PG39:C2, Moon note PG40:C1) as printed — bphs:PG39:C1 (Santhanam trans.); corroborated Uttara Kalamrita Ch. II p.28 — uttara_kalamrita:PG26:C1 (Sastri trans.)$c$),
      ($c$Moon$c$, $c$Mercury$c$, $c$BPHS Ch.27$c$, $c$BPHS Chapter 3, Sloka 55 (natural relationships; table at PG39:C2, Moon note PG40:C1) as printed — bphs:PG39:C1 (Santhanam trans.); corroborated Uttara Kalamrita Ch. II p.28 — uttara_kalamrita:PG26:C1 (Sastri trans.)$c$),
      ($c$Moon$c$, $c$Mars$c$, $c$BPHS Ch.27$c$, $c$BPHS Chapter 3, Sloka 55 (natural relationships; table at PG39:C2, Moon note PG40:C1) as printed — bphs:PG39:C1 (Santhanam trans.); corroborated Uttara Kalamrita Ch. II p.28 — uttara_kalamrita:PG26:C1 (Sastri trans.)$c$),
      ($c$Moon$c$, $c$Jupiter$c$, $c$BPHS Ch.27$c$, $c$BPHS Chapter 3, Sloka 55 (natural relationships; table at PG39:C2, Moon note PG40:C1) as printed — bphs:PG39:C1 (Santhanam trans.); corroborated Uttara Kalamrita Ch. II p.28 — uttara_kalamrita:PG26:C1 (Sastri trans.)$c$),
      ($c$Moon$c$, $c$Venus$c$, $c$BPHS Ch.27$c$, $c$BPHS Chapter 3, Sloka 55 (natural relationships; table at PG39:C2, Moon note PG40:C1) as printed — bphs:PG39:C1 (Santhanam trans.); corroborated Uttara Kalamrita Ch. II p.28 — uttara_kalamrita:PG26:C1 (Sastri trans.)$c$),
      ($c$Moon$c$, $c$Saturn$c$, $c$BPHS Ch.27$c$, $c$BPHS Chapter 3, Sloka 55 (natural relationships; table at PG39:C2, Moon note PG40:C1) as printed — bphs:PG39:C1 (Santhanam trans.); corroborated Uttara Kalamrita Ch. II p.28 — uttara_kalamrita:PG26:C1 (Sastri trans.)$c$),
      ($c$Mars$c$, $c$Sun$c$, $c$BPHS Ch.27$c$, $c$BPHS Chapter 3, Sloka 55 (natural relationships; table at PG39:C2, Moon note PG40:C1) as printed — bphs:PG39:C1 (Santhanam trans.); corroborated Uttara Kalamrita Ch. II p.28 — uttara_kalamrita:PG26:C1 (Sastri trans.)$c$),
      ($c$Mars$c$, $c$Moon$c$, $c$BPHS Ch.27$c$, $c$BPHS Chapter 3, Sloka 55 (natural relationships; table at PG39:C2, Moon note PG40:C1) as printed — bphs:PG39:C1 (Santhanam trans.); corroborated Uttara Kalamrita Ch. II p.28 — uttara_kalamrita:PG26:C1 (Sastri trans.)$c$),
      ($c$Mars$c$, $c$Jupiter$c$, $c$BPHS Ch.27$c$, $c$BPHS Chapter 3, Sloka 55 (natural relationships; table at PG39:C2, Moon note PG40:C1) as printed — bphs:PG39:C1 (Santhanam trans.); corroborated Uttara Kalamrita Ch. II p.28 — uttara_kalamrita:PG26:C1 (Sastri trans.)$c$),
      ($c$Mars$c$, $c$Venus$c$, $c$BPHS Ch.27$c$, $c$BPHS Chapter 3, Sloka 55 (natural relationships; table at PG39:C2, Moon note PG40:C1) as printed — bphs:PG39:C1 (Santhanam trans.); corroborated Uttara Kalamrita Ch. II p.28 — uttara_kalamrita:PG26:C1 (Sastri trans.)$c$),
      ($c$Mars$c$, $c$Saturn$c$, $c$BPHS Ch.27$c$, $c$BPHS Chapter 3, Sloka 55 (natural relationships; table at PG39:C2, Moon note PG40:C1) as printed — bphs:PG39:C1 (Santhanam trans.); corroborated Uttara Kalamrita Ch. II p.28 — uttara_kalamrita:PG26:C1 (Sastri trans.)$c$),
      ($c$Mars$c$, $c$Mercury$c$, $c$BPHS Ch.27$c$, $c$BPHS Chapter 3, Sloka 55 (natural relationships; table at PG39:C2, Moon note PG40:C1) as printed — bphs:PG39:C1 (Santhanam trans.); corroborated Uttara Kalamrita Ch. II p.28 — uttara_kalamrita:PG26:C1 (Sastri trans.)$c$),
      ($c$Mercury$c$, $c$Sun$c$, $c$BPHS Ch.27$c$, $c$BPHS Chapter 3, Sloka 55 (natural relationships; table at PG39:C2, Moon note PG40:C1) as printed — bphs:PG39:C1 (Santhanam trans.); corroborated Uttara Kalamrita Ch. II p.28 — uttara_kalamrita:PG26:C1 (Sastri trans.)$c$),
      ($c$Mercury$c$, $c$Venus$c$, $c$BPHS Ch.27$c$, $c$BPHS Chapter 3, Sloka 55 (natural relationships; table at PG39:C2, Moon note PG40:C1) as printed — bphs:PG39:C1 (Santhanam trans.); corroborated Uttara Kalamrita Ch. II p.28 — uttara_kalamrita:PG26:C1 (Sastri trans.)$c$),
      ($c$Mercury$c$, $c$Mars$c$, $c$BPHS Ch.27$c$, $c$BPHS Chapter 3, Sloka 55 (natural relationships; table at PG39:C2, Moon note PG40:C1) as printed — bphs:PG39:C1 (Santhanam trans.); corroborated Uttara Kalamrita Ch. II p.28 — uttara_kalamrita:PG26:C1 (Sastri trans.)$c$),
      ($c$Mercury$c$, $c$Jupiter$c$, $c$BPHS Ch.27$c$, $c$BPHS Chapter 3, Sloka 55 (natural relationships; table at PG39:C2, Moon note PG40:C1) as printed — bphs:PG39:C1 (Santhanam trans.); corroborated Uttara Kalamrita Ch. II p.28 — uttara_kalamrita:PG26:C1 (Sastri trans.)$c$),
      ($c$Mercury$c$, $c$Saturn$c$, $c$BPHS Ch.27$c$, $c$BPHS Chapter 3, Sloka 55 (natural relationships; table at PG39:C2, Moon note PG40:C1) as printed — bphs:PG39:C1 (Santhanam trans.); corroborated Uttara Kalamrita Ch. II p.28 — uttara_kalamrita:PG26:C1 (Sastri trans.)$c$),
      ($c$Mercury$c$, $c$Moon$c$, $c$BPHS Ch.27$c$, $c$BPHS Chapter 3, Sloka 55 (natural relationships; table at PG39:C2, Moon note PG40:C1) as printed — bphs:PG39:C1 (Santhanam trans.); corroborated Uttara Kalamrita Ch. II p.28 — uttara_kalamrita:PG26:C1 (Sastri trans.)$c$),
      ($c$Jupiter$c$, $c$Sun$c$, $c$BPHS Ch.27$c$, $c$BPHS Chapter 3, Sloka 55 (natural relationships; table at PG39:C2, Moon note PG40:C1) as printed — bphs:PG39:C1 (Santhanam trans.); corroborated Uttara Kalamrita Ch. II p.28 — uttara_kalamrita:PG26:C1 (Sastri trans.)$c$),
      ($c$Jupiter$c$, $c$Moon$c$, $c$BPHS Ch.27$c$, $c$BPHS Chapter 3, Sloka 55 (natural relationships; table at PG39:C2, Moon note PG40:C1) as printed — bphs:PG39:C1 (Santhanam trans.); corroborated Uttara Kalamrita Ch. II p.28 — uttara_kalamrita:PG26:C1 (Sastri trans.)$c$),
      ($c$Jupiter$c$, $c$Mars$c$, $c$BPHS Ch.27$c$, $c$BPHS Chapter 3, Sloka 55 (natural relationships; table at PG39:C2, Moon note PG40:C1) as printed — bphs:PG39:C1 (Santhanam trans.); corroborated Uttara Kalamrita Ch. II p.28 — uttara_kalamrita:PG26:C1 (Sastri trans.)$c$),
      ($c$Jupiter$c$, $c$Saturn$c$, $c$BPHS Ch.27$c$, $c$BPHS Chapter 3, Sloka 55 (natural relationships; table at PG39:C2, Moon note PG40:C1) as printed — bphs:PG39:C1 (Santhanam trans.); corroborated Uttara Kalamrita Ch. II p.28 — uttara_kalamrita:PG26:C1 (Sastri trans.)$c$),
      ($c$Jupiter$c$, $c$Mercury$c$, $c$BPHS Ch.27$c$, $c$BPHS Chapter 3, Sloka 55 (natural relationships; table at PG39:C2, Moon note PG40:C1) as printed — bphs:PG39:C1 (Santhanam trans.); corroborated Uttara Kalamrita Ch. II p.28 — uttara_kalamrita:PG26:C1 (Sastri trans.)$c$),
      ($c$Jupiter$c$, $c$Venus$c$, $c$BPHS Ch.27$c$, $c$BPHS Chapter 3, Sloka 55 (natural relationships; table at PG39:C2, Moon note PG40:C1) as printed — bphs:PG39:C1 (Santhanam trans.); corroborated Uttara Kalamrita Ch. II p.28 — uttara_kalamrita:PG26:C1 (Sastri trans.)$c$),
      ($c$Venus$c$, $c$Mercury$c$, $c$BPHS Ch.27$c$, $c$BPHS Chapter 3, Sloka 55 (natural relationships; table at PG39:C2, Moon note PG40:C1) as printed — bphs:PG39:C1 (Santhanam trans.); corroborated Uttara Kalamrita Ch. II p.28 — uttara_kalamrita:PG26:C1 (Sastri trans.)$c$),
      ($c$Venus$c$, $c$Saturn$c$, $c$BPHS Ch.27$c$, $c$BPHS Chapter 3, Sloka 55 (natural relationships; table at PG39:C2, Moon note PG40:C1) as printed — bphs:PG39:C1 (Santhanam trans.); corroborated Uttara Kalamrita Ch. II p.28 — uttara_kalamrita:PG26:C1 (Sastri trans.)$c$),
      ($c$Venus$c$, $c$Mars$c$, $c$BPHS Ch.27$c$, $c$BPHS Chapter 3, Sloka 55 (natural relationships; table at PG39:C2, Moon note PG40:C1) as printed — bphs:PG39:C1 (Santhanam trans.); corroborated Uttara Kalamrita Ch. II p.28 — uttara_kalamrita:PG26:C1 (Sastri trans.)$c$),
      ($c$Venus$c$, $c$Jupiter$c$, $c$BPHS Ch.27$c$, $c$BPHS Chapter 3, Sloka 55 (natural relationships; table at PG39:C2, Moon note PG40:C1) as printed — bphs:PG39:C1 (Santhanam trans.); corroborated Uttara Kalamrita Ch. II p.28 — uttara_kalamrita:PG26:C1 (Sastri trans.)$c$),
      ($c$Venus$c$, $c$Sun$c$, $c$BPHS Ch.27$c$, $c$BPHS Chapter 3, Sloka 55 (natural relationships; table at PG39:C2, Moon note PG40:C1) as printed — bphs:PG39:C1 (Santhanam trans.); corroborated Uttara Kalamrita Ch. II p.28 — uttara_kalamrita:PG26:C1 (Sastri trans.)$c$),
      ($c$Venus$c$, $c$Moon$c$, $c$BPHS Ch.27$c$, $c$BPHS Chapter 3, Sloka 55 (natural relationships; table at PG39:C2, Moon note PG40:C1) as printed — bphs:PG39:C1 (Santhanam trans.); corroborated Uttara Kalamrita Ch. II p.28 — uttara_kalamrita:PG26:C1 (Sastri trans.)$c$),
      ($c$Saturn$c$, $c$Mercury$c$, $c$BPHS Ch.27$c$, $c$BPHS Chapter 3, Sloka 55 (natural relationships; table at PG39:C2, Moon note PG40:C1) as printed — bphs:PG39:C1 (Santhanam trans.); corroborated Uttara Kalamrita Ch. II p.28 — uttara_kalamrita:PG26:C1 (Sastri trans.)$c$),
      ($c$Saturn$c$, $c$Venus$c$, $c$BPHS Ch.27$c$, $c$BPHS Chapter 3, Sloka 55 (natural relationships; table at PG39:C2, Moon note PG40:C1) as printed — bphs:PG39:C1 (Santhanam trans.); corroborated Uttara Kalamrita Ch. II p.28 — uttara_kalamrita:PG26:C1 (Sastri trans.)$c$),
      ($c$Saturn$c$, $c$Jupiter$c$, $c$BPHS Ch.27$c$, $c$BPHS Chapter 3, Sloka 55 (natural relationships; table at PG39:C2, Moon note PG40:C1) as printed — bphs:PG39:C1 (Santhanam trans.); corroborated Uttara Kalamrita Ch. II p.28 — uttara_kalamrita:PG26:C1 (Sastri trans.)$c$),
      ($c$Saturn$c$, $c$Sun$c$, $c$BPHS Ch.27$c$, $c$BPHS Chapter 3, Sloka 55 (natural relationships; table at PG39:C2, Moon note PG40:C1) as printed — bphs:PG39:C1 (Santhanam trans.); corroborated Uttara Kalamrita Ch. II p.28 — uttara_kalamrita:PG26:C1 (Sastri trans.)$c$),
      ($c$Saturn$c$, $c$Moon$c$, $c$BPHS Ch.27$c$, $c$BPHS Chapter 3, Sloka 55 (natural relationships; table at PG39:C2, Moon note PG40:C1) as printed — bphs:PG39:C1 (Santhanam trans.); corroborated Uttara Kalamrita Ch. II p.28 — uttara_kalamrita:PG26:C1 (Sastri trans.)$c$),
      ($c$Saturn$c$, $c$Mars$c$, $c$BPHS Ch.27$c$, $c$BPHS Chapter 3, Sloka 55 (natural relationships; table at PG39:C2, Moon note PG40:C1) as printed — bphs:PG39:C1 (Santhanam trans.); corroborated Uttara Kalamrita Ch. II p.28 — uttara_kalamrita:PG26:C1 (Sastri trans.)$c$),
      ($c$Rahu$c$, $c$Venus$c$, $c$UK Ch.4 (Uttara Kalamrita — Rahu/Ketu tatva friendship schema)$c$, $c$BPHS Chapter 3, notes under Sloka 55 (PG40) — bphs:PG40:C1 (Santhanam trans.); Sarvartha Chintamani, Stanza 108 as printed — sarvartha_chintamani:PG1:C127 (Suryanarayana Row trans., 1899)$c$),
      ($c$Rahu$c$, $c$Saturn$c$, $c$UK Ch.4 (Uttara Kalamrita — Rahu/Ketu tatva friendship schema)$c$, $c$BPHS Chapter 3, notes under Sloka 55 (PG40) — bphs:PG40:C1 (Santhanam trans.); Sarvartha Chintamani, Stanza 108 as printed — sarvartha_chintamani:PG1:C127 (Suryanarayana Row trans., 1899)$c$),
      ($c$Rahu$c$, $c$Sun$c$, $c$UK Ch.4 (Uttara Kalamrita — Rahu/Ketu tatva friendship schema)$c$, $c$BPHS Chapter 3, notes under Sloka 55 (PG40) — bphs:PG40:C1 (Santhanam trans.)$c$),
      ($c$Rahu$c$, $c$Moon$c$, $c$UK Ch.4 (Uttara Kalamrita — Rahu/Ketu tatva friendship schema)$c$, $c$BPHS Chapter 3, notes under Sloka 55 (PG40) — bphs:PG40:C1 (Santhanam trans.)$c$),
      ($c$Ketu$c$, $c$Mars$c$, $c$UK Ch.4 (Uttara Kalamrita — Rahu/Ketu tatva friendship schema)$c$, $c$BPHS Chapter 3, notes under Sloka 55 (PG40) — bphs:PG40:C1 (Santhanam trans.)$c$),
      ($c$Ketu$c$, $c$Venus$c$, $c$UK Ch.4 (Uttara Kalamrita — Rahu/Ketu tatva friendship schema)$c$, $c$BPHS Chapter 3, notes under Sloka 55 (PG40) — bphs:PG40:C1 (Santhanam trans.); Sarvartha Chintamani, Stanza 108 as printed — sarvartha_chintamani:PG1:C127 (Suryanarayana Row trans., 1899)$c$),
      ($c$Ketu$c$, $c$Saturn$c$, $c$UK Ch.4 (Uttara Kalamrita — Rahu/Ketu tatva friendship schema)$c$, $c$BPHS Chapter 3, notes under Sloka 55 (PG40) — bphs:PG40:C1 (Santhanam trans.); Sarvartha Chintamani, Stanza 108 as printed — sarvartha_chintamani:PG1:C127 (Suryanarayana Row trans., 1899)$c$),
      ($c$Ketu$c$, $c$Mercury$c$, $c$UK Ch.4 (Uttara Kalamrita — Rahu/Ketu tatva friendship schema)$c$, $c$BPHS Chapter 3, notes under Sloka 55 (PG40) — bphs:PG40:C1 (Santhanam trans.)$c$),
      ($c$Ketu$c$, $c$Jupiter$c$, $c$UK Ch.4 (Uttara Kalamrita — Rahu/Ketu tatva friendship schema)$c$, $c$BPHS Chapter 3, notes under Sloka 55 (PG40) — bphs:PG40:C1 (Santhanam trans.)$c$)
    ) AS v(graha, other_graha, old_c, new_c)
    WHERE t.graha::text = v.graha AND t.other_graha::text = v.other_graha AND t.classical_citation = v.old_c;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n <> 51 THEN RAISE EXCEPTION 'curation expected 51 bg_graha_naisargika_friendship rows, updated %', n; END IF;
  UPDATE bg_avastha_schemes t SET classical_citation = v.new_c
    FROM (VALUES
      ($c$baladi$c$, $c$bala$c$, $c$JP Ch.7$c$, $c$BPHS Chapter 45, Sloka 3 (Baladi avasthas) as printed — bphs:PG448:C1 (Santhanam trans.)$c$),
      ($c$baladi$c$, $c$kumara$c$, $c$JP Ch.7$c$, $c$BPHS Chapter 45, Sloka 3 (Baladi avasthas) as printed — bphs:PG448:C1 (Santhanam trans.)$c$),
      ($c$baladi$c$, $c$yuva$c$, $c$JP Ch.7$c$, $c$BPHS Chapter 45, Sloka 3 (Baladi avasthas) as printed — bphs:PG448:C1 (Santhanam trans.)$c$),
      ($c$baladi$c$, $c$vriddha$c$, $c$JP Ch.7$c$, $c$BPHS Chapter 45, Sloka 3 (Baladi avasthas) as printed — bphs:PG448:C1 (Santhanam trans.)$c$),
      ($c$baladi$c$, $c$mrita$c$, $c$JP Ch.7$c$, $c$BPHS Chapter 45, Sloka 3 (Baladi avasthas) as printed — bphs:PG448:C1 (Santhanam trans.)$c$),
      ($c$jagradadi$c$, $c$jagrata$c$, $c$BPHS Ch.45$c$, $c$BPHS Chapter 45, Sloka 5 as printed — bphs:PG448:C1 (Santhanam trans.)$c$),
      ($c$deeptaadi$c$, $c$dina$c$, $c$PD Ch.4$c$, $c$Phaladeepika Adh. III, Sloka 18-20 (avasthas; chapter end printed at PG70:C1) as printed — phaladeepika:PG69:C1, phaladeepika:PG70:C1 (Sastri trans. 1950)$c$),
      ($c$lajjitaadi$c$, $c$lajjita$c$, $c$UK Ch.4$c$, $c$BPHS Chapter 45, Sloka 11-18 (Lajjitadi avasthas) as printed — bphs:PG450:C1 (Santhanam trans.); Jataka Parijata p.119 — jataka_parijata:PG119:C1 (Subramanya Shashtri trans.)$c$),
      ($c$lajjitaadi$c$, $c$kshudhita$c$, $c$UK Ch.4$c$, $c$BPHS Chapter 45, Sloka 11-18 (Lajjitadi avasthas) as printed — bphs:PG450:C1 (Santhanam trans.); Jataka Parijata p.119 — jataka_parijata:PG119:C1 (Subramanya Shashtri trans.)$c$)
    ) AS v(scheme_name, state_name, old_c, new_c)
    WHERE t.scheme_name::text = v.scheme_name AND t.state_name::text = v.state_name AND t.classical_citation = v.old_c;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n <> 9 THEN RAISE EXCEPTION 'curation expected 9 bg_avastha_schemes rows, updated %', n; END IF;
  UPDATE bg_motion_state_thresholds t SET classical_citation = v.new_c
    FROM (VALUES
      ($c$Mars$c$, $c$vakra$c$, $c$SS / Saravali$c$, $c$BPHS Chapter 27 (Cheshta Bala; motion types) — bphs:PG283:C2, bphs:PG284:C1 (Santhanam trans.)$c$),
      ($c$Mercury$c$, $c$vakra$c$, $c$SS / Saravali$c$, $c$BPHS Chapter 27 (Cheshta Bala; motion types) — bphs:PG283:C2, bphs:PG284:C1 (Santhanam trans.)$c$),
      ($c$Jupiter$c$, $c$vakra$c$, $c$SS / Saravali$c$, $c$BPHS Chapter 27 (Cheshta Bala; motion types) — bphs:PG283:C2, bphs:PG284:C1 (Santhanam trans.)$c$),
      ($c$Venus$c$, $c$vakra$c$, $c$SS / Saravali$c$, $c$BPHS Chapter 27 (Cheshta Bala; motion types) — bphs:PG283:C2, bphs:PG284:C1 (Santhanam trans.)$c$),
      ($c$Saturn$c$, $c$vakra$c$, $c$SS / Saravali$c$, $c$BPHS Chapter 27 (Cheshta Bala; motion types) — bphs:PG283:C2, bphs:PG284:C1 (Santhanam trans.)$c$),
      ($c$Rahu$c$, $c$vakra$c$, $c$SS / Saravali$c$, $c$BPHS Chapter 47 (Dasa effects of Rahu and Ketu) p.571 — bphs:PG569:C1 (Santhanam trans.); Phaladeepika Adh. XXVI, Sloka 48 — phaladeepika:PG348:C1 (Sastri trans. 1950)$c$),
      ($c$Ketu$c$, $c$vakra$c$, $c$SS / Saravali$c$, $c$BPHS Chapter 47 (Dasa effects of Rahu and Ketu) p.571 — bphs:PG569:C1 (Santhanam trans.); Phaladeepika Adh. XXVI, Sloka 48 — phaladeepika:PG348:C1 (Sastri trans. 1950)$c$)
    ) AS v(graha, motion_state, old_c, new_c)
    WHERE t.graha::text = v.graha AND t.motion_state::text = v.motion_state AND t.classical_citation = v.old_c;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n <> 7 THEN RAISE EXCEPTION 'curation expected 7 bg_motion_state_thresholds rows, updated %', n; END IF;
  UPDATE bg_combustion_orbs t SET classical_citation = v.new_c
    FROM (VALUES
      ($c$Moon$c$, $c$Saravali Ch.6 / BPHS Ch.3$c$, $c$Uttara Kalamrita Ch. VI (Notes), p.139 — uttara_kalamrita:PG135:C1 (Sastri trans.); Jataka Parijata commentary, p.262 — jataka_parijata:PG262:C1 (Subramanya Shashtri trans.); BPHS Chapter 7, notes to Sloka 28-29 — bphs:PG99:C1 (Santhanam trans.)$c$),
      ($c$Mars$c$, $c$Saravali Ch.6 / BPHS Ch.3$c$, $c$Uttara Kalamrita Ch. VI (Notes), p.139 — uttara_kalamrita:PG135:C1 (Sastri trans.); Jataka Parijata commentary, p.262 — jataka_parijata:PG262:C1 (Subramanya Shashtri trans.); BPHS Chapter 7, notes to Sloka 28-29 — bphs:PG99:C1 (Santhanam trans.)$c$),
      ($c$Mercury$c$, $c$Saravali Ch.6 / BPHS Ch.3$c$, $c$Uttara Kalamrita Ch. VI (Notes), p.139 — uttara_kalamrita:PG135:C1 (Sastri trans.); Jataka Parijata commentary, p.262 — jataka_parijata:PG262:C1 (Subramanya Shashtri trans.); BPHS Chapter 7, notes to Sloka 28-29 — bphs:PG99:C1 (Santhanam trans.)$c$),
      ($c$Jupiter$c$, $c$Saravali Ch.6 / BPHS Ch.3$c$, $c$Uttara Kalamrita Ch. VI (Notes), p.139 — uttara_kalamrita:PG135:C1 (Sastri trans.); Jataka Parijata commentary, p.262 — jataka_parijata:PG262:C1 (Subramanya Shashtri trans.); BPHS Chapter 7, notes to Sloka 28-29 — bphs:PG99:C1 (Santhanam trans.)$c$),
      ($c$Venus$c$, $c$Saravali Ch.6 / BPHS Ch.3$c$, $c$Uttara Kalamrita Ch. VI (Notes), p.139 — uttara_kalamrita:PG135:C1 (Sastri trans.); Jataka Parijata commentary, p.262 — jataka_parijata:PG262:C1 (Subramanya Shashtri trans.); BPHS Chapter 7, notes to Sloka 28-29 — bphs:PG99:C1 (Santhanam trans.)$c$),
      ($c$Saturn$c$, $c$Saravali Ch.6 / BPHS Ch.3$c$, $c$Uttara Kalamrita Ch. VI (Notes), p.139 — uttara_kalamrita:PG135:C1 (Sastri trans.); Jataka Parijata commentary, p.262 — jataka_parijata:PG262:C1 (Subramanya Shashtri trans.); BPHS Chapter 7, notes to Sloka 28-29 — bphs:PG99:C1 (Santhanam trans.)$c$)
    ) AS v(graha, old_c, new_c)
    WHERE t.graha::text = v.graha AND t.classical_citation = v.old_c;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n <> 6 THEN RAISE EXCEPTION 'curation expected 6 bg_combustion_orbs rows, updated %', n; END IF;

  -- post-flight
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY graha::text COLLATE "C"), '')) FROM bg_dignity_reference t$q$ INTO fp_0;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY graha::text COLLATE "C",other_graha::text COLLATE "C"), '')) FROM bg_graha_naisargika_friendship t$q$ INTO fp_1;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY scheme_name::text COLLATE "C",state_name::text COLLATE "C"), '')) FROM bg_avastha_schemes t$q$ INTO fp_2;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY graha::text COLLATE "C",motion_state::text COLLATE "C"), '')) FROM bg_motion_state_thresholds t$q$ INTO fp_3;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY graha::text COLLATE "C"), '')) FROM bg_combustion_orbs t$q$ INTO fp_4;
  IF fp_0 IS DISTINCT FROM '1a65bfe09aeebdcf1b8dc2a28f674155' THEN RAISE EXCEPTION 'curation post-flight: bg_dignity_reference content fingerprint mismatch (%)', fp_0; END IF;
  IF fp_1 IS DISTINCT FROM 'b2048cc365d49af7558b7df52c5e0e96' THEN RAISE EXCEPTION 'curation post-flight: bg_graha_naisargika_friendship content fingerprint mismatch (%)', fp_1; END IF;
  IF fp_2 IS DISTINCT FROM '3d880a2848210299d4e9c2527f1c7822' THEN RAISE EXCEPTION 'curation post-flight: bg_avastha_schemes content fingerprint mismatch (%)', fp_2; END IF;
  IF fp_3 IS DISTINCT FROM '857df5bbf3e689179309b1ad15961c4b' THEN RAISE EXCEPTION 'curation post-flight: bg_motion_state_thresholds content fingerprint mismatch (%)', fp_3; END IF;
  IF fp_4 IS DISTINCT FROM 'b7de8c19765249fbf7367a81f8ecea4e' THEN RAISE EXCEPTION 'curation post-flight: bg_combustion_orbs content fingerprint mismatch (%)', fp_4; END IF;

  SELECT integrity_check_sql INTO ic FROM asset_registry WHERE asset_id = 'bg_dignity_reference';
  IF ic IS NOT NULL THEN
    EXECUTE ic INTO ok;
    IF ok IS NOT TRUE THEN RAISE EXCEPTION 'curation post-flight: bg_dignity_reference stored integrity_check_sql reads false'; END IF;
  END IF;
END
$curation$;
