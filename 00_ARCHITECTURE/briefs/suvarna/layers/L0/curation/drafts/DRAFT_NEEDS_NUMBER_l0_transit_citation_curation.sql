-- =============================================================================
-- DRAFT_NEEDS_NUMBER_l0_transit_citation_curation.sql      (HELD DRAFT: NOT APPLIED, NOT A MIGRATION)
-- Lane: curation-lane (Exec Suvarna), branch suvarna/land/TI-curation-001, N-101 curation of
--       bg_transit_rules + bg_transit_engine.  SS allocates the migration number (block 1200-1299).
--
-- WHAT IT DOES  (citation TEXT only; no rule, phala, house, vedha or numeric value changes)
--   * bg_transit_rules: re-sources 23 unfavourable rows off the refuted "BPHS Ch.29" (18) / the
--     chapter-only "Phaladeepika Ch.26" (5) to Phaladeepika Adh. XXVI slokas 9-24, chunk-level
--     (phaladeepika:PG324..PG331).  18 rows by direct statement (FACT), 5 Ketu rows by the sloka-2
--     equivalence "Rahu and Ketu are similar to the Sun" (INFERENCE, stated in the text of the citation).
--     NOT changed: Ketu 12th favourable (id 199: contradicts the text -> acharya batch), the 7
--     double-transit rows, the 6 UNSOURCED node rows, the 39 already page/sloka-anchored rows.
--   * bg_transit_engine: replaces the refuted "BPHS Ch.22 (Graha Gati)" on all 9 rows by an honest per-row
--     source-state statement (UNSOURCED, or PARTIALLY SOURCED naming the one cell the corpus states).
--     Numeric values are NOT touched (WAVE-1 Part B is an SS decision).
--   * OPTIONAL second block (runs only if bg_transit_rules.attribution_state exists, migration 1268 / PR #3044): the 18 FACT rows
--     become 'sourced', the 5 INFERENCE (Ketu) rows are reset from 'refuted' to NULL.  Apply 1268 BEFORE this file.
--   * Re-seals the two asset_registry integrity contracts (their sha256 covers these citation columns) and
--     updates the two english_description texts that still asserted the refuted sources.
--
-- GUARDS  (all fail loudly, nothing partial: one DO block under the runner-owned transaction)
--   old-value guard : live engine/rules content hashes must equal the pinned pre-state hashes; every UPDATE
--                     matches on (graha, rule_type, primary_house) AND the exact old citation AND vedha_house IS NULL;
--                     exact row counts (23, 9) asserted.
--   idempotency     : if the tables are already at the curated content AND the registry is resealed -> NOTICE + no-op.
--   post-flight     : curated content hashes equal the pinned post-state hashes; BPHS Ch.29 remains on exactly 1 row;
--                     no 'Phaladeepika Ch.26 (Gochara Vedha' and no 'BPHS Ch.22' citation remains; both stored
--                     integrity_check_sql statements evaluate true.
-- PINNED HASHES  engine 104aa45b4221b5cdbe123f6a288219991b8a2a898718cf9713c33bf79a3819ae
--                rules  d7f9f2459efffa4071a24d5042326537e7bada3293d85f493224e1ba0f5f7823
-- DOWNSTREAM NOTE (measured 2026-10-03, read-only): the Kala-layer products hold BUILD-TIME COPIES of the old rule
--   citations -- gochara_resonance_map.classical_citation (115 rows carry 'BPHS Ch.29' / 'Phaladeepika Ch.26'; 57 of
--   them reference 14 of the 23 rule ids changed here) and kala_gochara_contacts.classical_citation (123 rows; it
--   also carries a corpus_verifiable stamp).  Nothing here changes them and no integrity check compares them with
--   bg_transit_rules, but they keep the old strings until ka_gochara_resonance / the contacts writer are rebuilt
--   (Kala layer: out of this lane's scope; SS to schedule with the Pravaha owner).
-- ROLLBACK (manual): re-run the inverse UPDATEs (old/new swapped) and restore the pre-state registry rows from
--   snapshots/live_registry.json.
-- Seed parity: platform/python-sidecar/brahmagyan/l0_transit.py must carry the same citations or the next L0
--   rebuild reverts them -> see DRAFT_l0_transit_seed_curation.patch (stales nirmana-writer-digests.json: needs
--   regeneration after PR #2984 lands).
-- =============================================================================

DO $curation$
DECLARE
  c_engine_old constant text := 'e2dafc84d7fef9b8a05ad01b98b036686e8ec0af9694a4d43ac4b2b8c425797b';
  c_rules_old  constant text := '1dbdd265cf0e04edd26aebde054f34d9034be38bfabc8102085b0127196a598d';
  c_engine_new constant text := '104aa45b4221b5cdbe123f6a288219991b8a2a898718cf9713c33bf79a3819ae';
  c_rules_new  constant text := 'd7f9f2459efffa4071a24d5042326537e7bada3293d85f493224e1ba0f5f7823';
  c_eng_ic_md5 constant text := '9c1b1f5b6792fc4643d689e5124fa554';
  c_rul_ic_md5 constant text := 'a3ded694827457ffaf640d24ff1e4057';
  c_eng_desc_old constant text := $d$L0 average graha motion parameters — daily motion, zodiac period, sign residence. Source: BPHS Ch.22.$d$;
  c_eng_desc_new constant text := $d$L0 average graha motion parameters — daily motion, zodiac period, sign residence. The period values coincide with modern mean sidereal periods; none is a classical statement: the former 'Source: BPHS Ch.22' was refuted (served bphs:PG22:C1 is Chapter 2, incarnations). Only round sign-residence figures for the Sun, Jupiter and Saturn are stated in the held corpus; each row's classical_citation says exactly which cell, if any, is sourced.$d$;
  c_rul_desc_old constant text := $d$76 classical transit rules: 43 favourable, 26 unfavourable, 7 double-transit. Citation state after the 2026-09 L0 repair, measured not asserted: 36 favourable-with-vedha rows carry page-anchored Phaladipika Adh. XXVI citations (PG322:C1/PG323:C1); 6 Rahu/Ketu favourable-with-vedha rows are declared UNSOURCED (the served corpus carries no house-transit vedha doctrine for the nodes); 19 rows (18 unfavourable + 1 favourable with no vedha pair) STILL carry the refuted "BPHS Ch.29" — they lie outside the repair's row-by-row verified predicate and were deliberately not re-cited on an unverified basis; the remaining 15 cite Phaladeepika Ch.26, Adh. XXVI slokas 2/8/21, Saravali or Jataka Parijata.$d$;
  c_rul_desc_new constant text := $d$76 classical transit rules: 43 favourable, 26 unfavourable, 7 double-transit. Citation state after the 2026-10 N-101 curation, measured not asserted: 39 rows carry page/sloka-anchored Phaladipika Adh. XXVI citations from the earlier L0 repair (36 favourable-with-vedha, 3 Venus unfavourable); 23 unfavourable rows were re-sourced to Phaladipika Adh. XXVI slokas 9-24 (18 by direct statement of the adverse result; 5 Ketu rows by the sloka-2 'Rahu and Ketu are similar to the Sun' equivalence, an INFERENCE) — the stored phala wording of those rows goes beyond the slokas and is editorial; 6 Rahu/Ketu favourable-with-vedha rows are declared UNSOURCED; 1 row (Ketu 12th, favourable) still carries the refuted "BPHS Ch.29" and CONTRADICTS the held text (acharya batch, row not changed); 7 double-transit rows cite a Phaladeepika section and other sources that cannot be resolved in the held corpus (unsourced).$d$;
  engine_hash_sql constant text := $q$SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(graha,avg_daily_motion_deg,zodiac_period_days,
      sign_residence_days,classical_citation)::text,
    E'\n' ORDER BY graha COLLATE "C"
  ),''),'UTF8')),'hex') FROM bg_transit_engine$q$;
  rules_hash_sql  constant text := $q$SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(rule_type,graha,primary_house,vedha_house,phala,
      classical_citation,rule_notes)::text,
    E'\n' ORDER BY graha COLLATE "C",rule_type COLLATE "C",primary_house
  ),''),'UTF8')),'hex') FROM bg_transit_rules$q$;
  eng_reg asset_registry%ROWTYPE;
  rul_reg asset_registry%ROWTYPE;
  h_engine text;
  h_rules text;
  n integer;
  ok boolean;
BEGIN
  SELECT * INTO eng_reg FROM asset_registry WHERE asset_id = 'bg_transit_engine' FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'curation refuses: asset_registry row bg_transit_engine not found'; END IF;
  SELECT * INTO rul_reg FROM asset_registry WHERE asset_id = 'bg_transit_rules' FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'curation refuses: asset_registry row bg_transit_rules not found'; END IF;

  EXECUTE engine_hash_sql INTO h_engine;
  EXECUTE rules_hash_sql INTO h_rules;

  -- idempotent no-op: already curated AND resealed
  IF h_engine = c_engine_new AND h_rules = c_rules_new THEN
    IF position(c_engine_new IN eng_reg.integrity_check_sql) = 0
       OR position(c_engine_new IN rul_reg.integrity_check_sql) = 0
       OR position(c_rules_new IN rul_reg.integrity_check_sql) = 0 THEN
      RAISE EXCEPTION 'curation refuses: tables are at the curated content but the registry contracts are not resealed';
    END IF;
    RAISE NOTICE 'curation already applied: no-op';
    RETURN;
  END IF;

  -- old-value guards
  IF h_engine IS DISTINCT FROM c_engine_old OR h_rules IS DISTINCT FROM c_rules_old THEN
    RAISE EXCEPTION 'curation refuses: bg_transit_engine / bg_transit_rules content is not the pinned pre-state (engine %, rules %)', h_engine, h_rules;
  END IF;
  IF md5(eng_reg.integrity_check_sql) IS DISTINCT FROM c_eng_ic_md5
     OR md5(rul_reg.integrity_check_sql) IS DISTINCT FROM c_rul_ic_md5 THEN
    RAISE EXCEPTION 'curation refuses: registry integrity_check_sql is not the pinned pre-state text (md5 mismatch)';
  END IF;
  IF eng_reg.english_description IS DISTINCT FROM c_eng_desc_old OR rul_reg.english_description IS DISTINCT FROM c_rul_desc_old THEN
    RAISE EXCEPTION 'curation refuses: registry english_description has drifted from the pinned pre-state';
  END IF;

  -- bg_transit_rules: 23 citation updates
  UPDATE bg_transit_rules r SET classical_citation = v.new_c
    FROM (VALUES
      ($c$sun$c$, $c$unfavourable$c$, 1, $c$BPHS Ch.29 (Gochara Phala — Transit Results)$c$, $c$Phaladipika Adh. XXVI, Sloka 9 — phaladeepika:PG324:C1 (Sastri trans. 1950) [supports: unfavourable valence; ill-health (diseases); remaining phala wording is not in the sloka]$c$),
      ($c$sun$c$, $c$unfavourable$c$, 5, $c$BPHS Ch.29 (Gochara Phala — Transit Results)$c$, $c$Phaladipika Adh. XXVI, Sloka 10 — phaladeepika:PG324:C1 (Sastri trans. 1950) [supports: unfavourable valence; ill-health, mental agitation; remaining phala wording is not in the sloka]$c$),
      ($c$sun$c$, $c$unfavourable$c$, 8, $c$BPHS Ch.29 (Gochara Phala — Transit Results)$c$, $c$Phaladipika Adh. XXVI, Sloka 10 (continued from PG324) — phaladeepika:PG325:C1 (Sastri trans. 1950) [supports: unfavourable valence; diseases; royal displeasure (conflict with authority); remaining phala wording is not in the sloka]$c$),
      ($c$moon$c$, $c$unfavourable$c$, 8, $c$BPHS Ch.29 (Gochara Phala — Transit Results)$c$, $c$Phaladipika Adh. XXVI, Sloka 12 — phaladeepika:PG325:C1 (Sastri trans. 1950) [supports: unfavourable valence only (wording 'untoward events' is weak); remaining phala wording is not in the sloka]$c$),
      ($c$mars$c$, $c$unfavourable$c$, 1, $c$BPHS Ch.29 (Gochara Phala — Transit Results)$c$, $c$Phaladipika Adh. XXVI, Sloka 13 — phaladeepika:PG326:C1 (Sastri trans. 1950) [supports: unfavourable valence; diseases from blood, bile or heat; remaining phala wording is not in the sloka]$c$),
      ($c$mars$c$, $c$unfavourable$c$, 4, $c$BPHS Ch.29 (Gochara Phala — Transit Results)$c$, $c$Phaladipika Adh. XXVI, Sloka 13 — phaladeepika:PG326:C1 (Sastri trans. 1950) [supports: unfavourable valence; loss of position; sorrow through relations; remaining phala wording is not in the sloka]$c$),
      ($c$mars$c$, $c$unfavourable$c$, 8, $c$BPHS Ch.29 (Gochara Phala — Transit Results)$c$, $c$Phaladipika Adh. XXVI, Sloka 15 (continued from PG326) — phaladeepika:PG327:C1 (Sastri trans. 1950) [supports: unfavourable valence; fever; loss of wealth and honour; remaining phala wording is not in the sloka]$c$),
      ($c$jupiter$c$, $c$unfavourable$c$, 4, $c$BPHS Ch.29 (Gochara Phala — Transit Results)$c$, $c$Phaladipika Adh. XXVI, Sloka 18 — phaladeepika:PG328:C1 (Sastri trans. 1950) [supports: unfavourable valence; sorrow through relations; humiliation; remaining phala wording is not in the sloka]$c$),
      ($c$jupiter$c$, $c$unfavourable$c$, 8, $c$BPHS Ch.29 (Gochara Phala — Transit Results)$c$, $c$Phaladipika Adh. XXVI, Sloka 19 — phaladeepika:PG328:C1 (Sastri trans. 1950) [supports: unfavourable valence; loss of money; unlucky, miserable; remaining phala wording is not in the sloka]$c$),
      ($c$saturn$c$, $c$unfavourable$c$, 1, $c$Phaladeepika Ch.26 (Gochara Vedha and Transit Phala)$c$, $c$Phaladipika Adh. XXVI, Sloka 22 — phaladeepika:PG330:C1 (Sastri trans. 1950) [supports: unfavourable valence; disease; remaining phala wording is not in the sloka]$c$),
      ($c$saturn$c$, $c$unfavourable$c$, 4, $c$BPHS Ch.29 (Gochara Phala — Transit Results)$c$, $c$Phaladipika Adh. XXVI, Sloka 22 — phaladeepika:PG330:C1 (Sastri trans. 1950) [supports: unfavourable valence; loss of wife, relation and wealth; remaining phala wording is not in the sloka]$c$),
      ($c$saturn$c$, $c$unfavourable$c$, 8, $c$BPHS Ch.29 (Gochara Phala — Transit Results)$c$, $c$Phaladipika Adh. XXVI, Sloka 22 — phaladeepika:PG330:C1 (Sastri trans. 1950) [supports: unfavourable valence; disease; loss of children, cattle, friends, wealth; remaining phala wording is not in the sloka]$c$),
      ($c$rahu$c$, $c$unfavourable$c$, 1, $c$BPHS Ch.29 (Gochara Phala — Transit Results)$c$, $c$Phaladipika Adh. XXVI, Sloka 24 — phaladeepika:PG331:C1 (Sastri trans. 1950) [supports: unfavourable valence; sickness or death; remaining phala wording is not in the sloka]$c$),
      ($c$rahu$c$, $c$unfavourable$c$, 2, $c$BPHS Ch.29 (Gochara Phala — Transit Results)$c$, $c$Phaladipika Adh. XXVI, Sloka 24 — phaladeepika:PG331:C1 (Sastri trans. 1950) [supports: unfavourable valence; loss of wealth; remaining phala wording is not in the sloka]$c$),
      ($c$rahu$c$, $c$unfavourable$c$, 4, $c$BPHS Ch.29 (Gochara Phala — Transit Results)$c$, $c$Phaladipika Adh. XXVI, Sloka 24 — phaladeepika:PG331:C1 (Sastri trans. 1950) [supports: unfavourable valence; sorrow; remaining phala wording is not in the sloka]$c$),
      ($c$rahu$c$, $c$unfavourable$c$, 7, $c$Phaladeepika Ch.26 (Gochara Vedha and Transit Phala)$c$, $c$Phaladipika Adh. XXVI, Sloka 24 — phaladeepika:PG331:C1 (Sastri trans. 1950) [supports: unfavourable valence; loss; remaining phala wording is not in the sloka]$c$),
      ($c$rahu$c$, $c$unfavourable$c$, 8, $c$BPHS Ch.29 (Gochara Phala — Transit Results)$c$, $c$Phaladipika Adh. XXVI, Sloka 24 — phaladeepika:PG331:C1 (Sastri trans. 1950) [supports: unfavourable valence; danger to life; remaining phala wording is not in the sloka]$c$),
      ($c$rahu$c$, $c$unfavourable$c$, 12, $c$Phaladeepika Ch.26 (Gochara Vedha and Transit Phala)$c$, $c$Phaladipika Adh. XXVI, Sloka 24 — phaladeepika:PG331:C1 (Sastri trans. 1950) [supports: unfavourable valence; expenditure; remaining phala wording is not in the sloka]$c$),
      ($c$ketu$c$, $c$unfavourable$c$, 1, $c$BPHS Ch.29 (Gochara Phala — Transit Results)$c$, $c$Phaladipika Adh. XXVI, Sloka 2 (Rahu and Ketu are similar to the Sun) read with Sloka 9 (Sun, house 1) and Sloka 24 (Rahu, house 1) — phaladeepika:PG321:C1, phaladeepika:PG324:C1, phaladeepika:PG331:C1 (Sastri trans. 1950) [INFERENCE: no Ketu-specific verse; unfavourable valence only; remaining phala wording is not in the text]$c$),
      ($c$ketu$c$, $c$unfavourable$c$, 2, $c$Phaladeepika Ch.26 (Gochara Vedha and Transit Phala)$c$, $c$Phaladipika Adh. XXVI, Sloka 2 (Rahu and Ketu are similar to the Sun) read with Sloka 9 (Sun, house 2) and Sloka 24 (Rahu, house 2) — phaladeepika:PG321:C1, phaladeepika:PG324:C1, phaladeepika:PG331:C1 (Sastri trans. 1950) [INFERENCE: no Ketu-specific verse; unfavourable valence only; remaining phala wording is not in the text]$c$),
      ($c$ketu$c$, $c$unfavourable$c$, 4, $c$BPHS Ch.29 (Gochara Phala — Transit Results)$c$, $c$Phaladipika Adh. XXVI, Sloka 2 (Rahu and Ketu are similar to the Sun) read with Sloka 9 (Sun, house 4) and Sloka 24 (Rahu, house 4) — phaladeepika:PG321:C1, phaladeepika:PG324:C1, phaladeepika:PG331:C1 (Sastri trans. 1950) [INFERENCE: no Ketu-specific verse; unfavourable valence only; remaining phala wording is not in the text]$c$),
      ($c$ketu$c$, $c$unfavourable$c$, 7, $c$Phaladeepika Ch.26 (Gochara Vedha and Transit Phala)$c$, $c$Phaladipika Adh. XXVI, Sloka 2 (Rahu and Ketu are similar to the Sun) read with Sloka 10 (Sun, house 7) and Sloka 24 (Rahu, house 7) — phaladeepika:PG321:C1, phaladeepika:PG324:C1, phaladeepika:PG331:C1 (Sastri trans. 1950) [INFERENCE: no Ketu-specific verse; unfavourable valence only; remaining phala wording is not in the text]$c$),
      ($c$ketu$c$, $c$unfavourable$c$, 8, $c$BPHS Ch.29 (Gochara Phala — Transit Results)$c$, $c$Phaladipika Adh. XXVI, Sloka 2 (Rahu and Ketu are similar to the Sun) read with Sloka 10 (Sun, house 8) and Sloka 24 (Rahu, house 8) — phaladeepika:PG321:C1, phaladeepika:PG325:C1, phaladeepika:PG331:C1 (Sastri trans. 1950) [INFERENCE: no Ketu-specific verse; unfavourable valence only; remaining phala wording is not in the text]$c$)
    ) AS v(graha, rule_type, primary_house, old_c, new_c)
    WHERE r.graha = v.graha AND r.rule_type = v.rule_type AND r.primary_house = v.primary_house
      AND r.classical_citation = v.old_c AND r.vedha_house IS NULL;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n <> 23 THEN RAISE EXCEPTION 'curation expected 23 bg_transit_rules rows, updated %', n; END IF;

  -- bg_transit_engine: 9 citation updates
  UPDATE bg_transit_engine e SET classical_citation = v.new_c
    FROM (VALUES
      ($c$jupiter$c$, $c$BPHS Ch.22 (Graha Gati — Planetary Motion)$c$, $c$PARTIALLY SOURCED — only sign_residence_days (about one year per sign) is stated in the held corpus: yavana_jataka:PG662:C1 ('at the rate of one sign a year'), yavana_jataka:PG900:C1, bphs:PG933:C1 (worked example); stored 361.05 is read from the round figure: INFERENCE. Motion and period values are not stated (the period coincides with the modern mean sidereal period). Former citation "BPHS Ch.22 (Graha Gati)" withdrawn as refuted: served bphs:PG22:C1 is Chapter 2 (incarnations) and the held corpus has no BPHS Graha Gati text.$c$),
      ($c$ketu$c$, $c$BPHS Ch.22 (Graha Gati — Planetary Motion)$c$, $c$UNSOURCED — no value of this row is stated in the held classical corpus (the period coincides with the modern mean sidereal period). Former citation "BPHS Ch.22 (Graha Gati)" withdrawn as refuted: served bphs:PG22:C1 is Chapter 2 (incarnations) and the held corpus has no BPHS Graha Gati text.$c$),
      ($c$mars$c$, $c$BPHS Ch.22 (Graha Gati — Planetary Motion)$c$, $c$UNSOURCED — no value of this row is stated in the held classical corpus (the period coincides with the modern mean sidereal period). Former citation "BPHS Ch.22 (Graha Gati)" withdrawn as refuted: served bphs:PG22:C1 is Chapter 2 (incarnations) and the held corpus has no BPHS Graha Gati text.$c$),
      ($c$mercury$c$, $c$BPHS Ch.22 (Graha Gati — Planetary Motion)$c$, $c$UNSOURCED — no value of this row is stated in the held classical corpus (the period coincides with the modern mean sidereal period). Former citation "BPHS Ch.22 (Graha Gati)" withdrawn as refuted: served bphs:PG22:C1 is Chapter 2 (incarnations) and the held corpus has no BPHS Graha Gati text.$c$),
      ($c$moon$c$, $c$BPHS Ch.22 (Graha Gati — Planetary Motion)$c$, $c$UNSOURCED — no value of this row is stated in the held corpus (sarvartha_chintamani:PG1:C301 has a translator note giving the Moon's time per sign, but the numeral is OCR-illegible and is not relied on). The period coincides with the modern mean sidereal period. Former citation "BPHS Ch.22 (Graha Gati)" withdrawn as refuted: served bphs:PG22:C1 is Chapter 2 (incarnations) and the held corpus has no BPHS Graha Gati text.$c$),
      ($c$rahu$c$, $c$BPHS Ch.22 (Graha Gati — Planetary Motion)$c$, $c$UNSOURCED — no value of this row is stated in the held classical corpus (the period coincides with the modern mean sidereal period). Former citation "BPHS Ch.22 (Graha Gati)" withdrawn as refuted: served bphs:PG22:C1 is Chapter 2 (incarnations) and the held corpus has no BPHS Graha Gati text.$c$),
      ($c$saturn$c$, $c$BPHS Ch.22 (Graha Gati — Planetary Motion)$c$, $c$PARTIALLY SOURCED — only sign_residence_days is stated in the held corpus, as round figures: '30 months' per sign (brihat_jataka:PG96:C1; jataka_parijata:PG144:C1, translator notes) and 'takes 900 days to move in a sign' (sarvartha_chintamani:PG1:C301, translator note); stored 913.37 is read as 30 months: INFERENCE. Motion and period values are not stated (the period coincides with the modern mean sidereal period). Former citation "BPHS Ch.22 (Graha Gati)" withdrawn as refuted: served bphs:PG22:C1 is Chapter 2 (incarnations) and the held corpus has no BPHS Graha Gati text.$c$),
      ($c$sun$c$, $c$BPHS Ch.22 (Graha Gati — Planetary Motion)$c$, $c$PARTIALLY SOURCED — only sign_residence_days is stated in the held corpus, as the round figure '30 days' per sign (brihat_jataka:PG96:C1; jataka_parijata:PG144:C1, translator notes; stored 30.44 is read from it: INFERENCE). Motion and period values are not stated in the held corpus (the period coincides with the modern mean sidereal period). Former citation "BPHS Ch.22 (Graha Gati)" withdrawn as refuted: served bphs:PG22:C1 is Chapter 2 (incarnations) and the held corpus has no BPHS Graha Gati text.$c$),
      ($c$venus$c$, $c$BPHS Ch.22 (Graha Gati — Planetary Motion)$c$, $c$UNSOURCED — no value of this row is stated in the held classical corpus (the period coincides with the modern mean sidereal period). Former citation "BPHS Ch.22 (Graha Gati)" withdrawn as refuted: served bphs:PG22:C1 is Chapter 2 (incarnations) and the held corpus has no BPHS Graha Gati text.$c$)
    ) AS v(graha, old_c, new_c)
    WHERE e.graha = v.graha AND e.classical_citation = v.old_c;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n <> 9 THEN RAISE EXCEPTION 'curation expected 9 bg_transit_engine rows, updated %', n; END IF;

  -- post-flight content
  EXECUTE engine_hash_sql INTO h_engine;
  EXECUTE rules_hash_sql INTO h_rules;
  IF h_engine IS DISTINCT FROM c_engine_new OR h_rules IS DISTINCT FROM c_rules_new THEN
    RAISE EXCEPTION 'curation post-flight: content hash mismatch (engine %, rules %)', h_engine, h_rules;
  END IF;
  SELECT count(*) INTO n FROM bg_transit_rules WHERE classical_citation LIKE 'BPHS Ch.29%';
  IF n <> 1 THEN RAISE EXCEPTION 'curation post-flight: expected exactly 1 remaining BPHS Ch.29 row (Ketu 12th), found %', n; END IF;
  SELECT count(*) INTO n FROM bg_transit_rules WHERE classical_citation LIKE 'Phaladeepika Ch.26 (Gochara Vedha%';
  IF n <> 0 THEN RAISE EXCEPTION 'curation post-flight: % chapter-only Phaladeepika Ch.26 rows remain', n; END IF;
  SELECT count(*) INTO n FROM bg_transit_engine WHERE classical_citation LIKE '%BPHS Ch.22 (Graha Gati%' AND classical_citation NOT LIKE 'PARTIALLY SOURCED%' AND classical_citation NOT LIKE 'UNSOURCED%';
  IF n <> 0 THEN RAISE EXCEPTION 'curation post-flight: % engine rows still cite BPHS Ch.22 as a source', n; END IF;

  -- reseal the two registry contracts
  UPDATE asset_registry
     SET integrity_check_sql = replace(integrity_check_sql, c_engine_old, c_engine_new),
         english_description = c_eng_desc_new
   WHERE asset_id = 'bg_transit_engine';
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n <> 1 THEN RAISE EXCEPTION 'curation expected 1 engine registry row, updated %', n; END IF;
  UPDATE asset_registry
     SET integrity_check_sql = replace(replace(integrity_check_sql, c_engine_old, c_engine_new), c_rules_old, c_rules_new),
         english_description = c_rul_desc_new
   WHERE asset_id = 'bg_transit_rules';
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n <> 1 THEN RAISE EXCEPTION 'curation expected 1 rules registry row, updated %', n; END IF;

  -- post-flight: the stored contracts themselves read true
  SELECT integrity_check_sql INTO eng_reg.integrity_check_sql FROM asset_registry WHERE asset_id = 'bg_transit_engine';
  EXECUTE eng_reg.integrity_check_sql INTO ok;
  IF ok IS NOT TRUE THEN RAISE EXCEPTION 'curation post-flight: bg_transit_engine stored integrity_check_sql reads false'; END IF;
  SELECT integrity_check_sql INTO rul_reg.integrity_check_sql FROM asset_registry WHERE asset_id = 'bg_transit_rules';
  EXECUTE rul_reg.integrity_check_sql INTO ok;
  IF ok IS NOT TRUE THEN RAISE EXCEPTION 'curation post-flight: bg_transit_rules stored integrity_check_sql reads false'; END IF;
END
$curation$;


-- ---------------------------------------------------------------------------------------------
-- OPTIONAL second block: attribution_state (migration 1268 / PR #3044, TI-L0-09).  Runs only if the column exists.
--   ORDER: apply 1268 FIRST (its backfill guard expects 19 `refuted` rows = the BPHS Ch.29 set this file re-sources;
--   applied after this file it would refuse by design: the audited set changed).  Then this block moves the rows:
--     * 18 rows re-sourced by direct statement (FACT)      -> 'sourced'   (from NULL or 'refuted')
--     * 5 Ketu rows sourced by the sloka-2 equivalence     -> NULL        (INFERENCE is not a PASS until the acharya accepts it;
--                                                                          'refuted' no longer describes the NEW citation)
--     * Ketu 12th (id 199), the 6 UNSOURCED node rows, the 7 double-transit rows: untouched.
--   Any of the 23 rows in another state raises.  Idempotent.
DO $attr$
DECLARE
  n integer;
  bad integer;
  fact_keys constant text[] := ARRAY['sun|unfavourable|1', 'sun|unfavourable|5', 'sun|unfavourable|8', 'moon|unfavourable|8', 'mars|unfavourable|1', 'mars|unfavourable|4', 'mars|unfavourable|8', 'jupiter|unfavourable|4', 'jupiter|unfavourable|8', 'saturn|unfavourable|1', 'saturn|unfavourable|4', 'saturn|unfavourable|8', 'rahu|unfavourable|1', 'rahu|unfavourable|2', 'rahu|unfavourable|4', 'rahu|unfavourable|7', 'rahu|unfavourable|8', 'rahu|unfavourable|12'];
  inf_keys  constant text[] := ARRAY['ketu|unfavourable|1', 'ketu|unfavourable|2', 'ketu|unfavourable|4', 'ketu|unfavourable|7', 'ketu|unfavourable|8'];
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                  WHERE table_schema = current_schema() AND table_name = 'bg_transit_rules' AND column_name = 'attribution_state') THEN
    RAISE NOTICE 'attribution_state column absent (migration 1268 not applied): skipping the state block';
    RETURN;
  END IF;
  EXECUTE $q$SELECT count(*) FROM bg_transit_rules
              WHERE (graha||'|'||rule_type||'|'||primary_house) = ANY($1 || $2)
                AND attribution_state IS NOT NULL AND attribution_state <> 'refuted' AND attribution_state <> 'sourced'$q$
     INTO bad USING fact_keys, inf_keys;
  IF bad <> 0 THEN
    RAISE EXCEPTION 'curation refuses: % of the 23 re-sourced rows carry an attribution_state other than NULL / refuted / sourced', bad;
  END IF;
  EXECUTE $q$UPDATE bg_transit_rules SET attribution_state = 'sourced'
              WHERE (graha||'|'||rule_type||'|'||primary_house) = ANY($1) AND attribution_state IS DISTINCT FROM 'sourced'$q$ USING fact_keys;
  GET DIAGNOSTICS n = ROW_COUNT;
  RAISE NOTICE 'attribution_state: % FACT rows set to sourced', n;
  EXECUTE $q$UPDATE bg_transit_rules SET attribution_state = NULL
              WHERE (graha||'|'||rule_type||'|'||primary_house) = ANY($1) AND attribution_state = 'refuted'$q$ USING inf_keys;
  GET DIAGNOSTICS n = ROW_COUNT;
  RAISE NOTICE 'attribution_state: % INFERENCE rows reset from refuted to NULL', n;
  EXECUTE $q$SELECT count(*) FROM bg_transit_rules WHERE (graha||'|'||rule_type||'|'||primary_house) = ANY($1) AND attribution_state IS DISTINCT FROM 'sourced'$q$
     INTO bad USING fact_keys;
  IF bad <> 0 THEN RAISE EXCEPTION 'curation post-flight: % FACT rows are not sourced', bad; END IF;
END
$attr$;

-- VERIFY (run after apply):
--   SELECT classical_citation FROM bg_transit_rules WHERE id IN (5,6,7,14,18,19,20,31,32,39,40,41,190,191,192,193,194,195,200,201,202,203,204);
--   SELECT graha, left(classical_citation, 60) FROM bg_transit_engine ORDER BY graha;
--   -- then execute each stored integrity_check_sql: expect t
