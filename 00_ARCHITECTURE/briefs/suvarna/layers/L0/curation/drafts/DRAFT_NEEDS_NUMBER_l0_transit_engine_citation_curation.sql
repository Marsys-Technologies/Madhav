-- =============================================================================
-- DRAFT_NEEDS_NUMBER_l0_transit_engine_citation_curation.sql   (HELD DRAFT: NOT APPLIED, NOT A MIGRATION)
-- Lane: curation-lane (Exec Suvarna), branch suvarna/land/TI-curation-001, N-101 curation of bg_transit_engine.
-- SS allocates the migration number (block 1200-1299).
--
-- SCOPE: bg_transit_engine.classical_citation ONLY (9 rows). The 23 bg_transit_rules re-citations are PR #3049's (TI-L0-10);
-- this lane's ledger independently confirms them (see ledger section 4) and ships no SQL or seed patch for them.
-- The refuted "BPHS Ch.22 (Graha Gati)" (served bphs:PG22:C1 is Chapter 2, incarnations) is replaced on all 9 rows by an
-- honest per-row source-state statement: UNSOURCED, or PARTIALLY SOURCED naming the one cell the held corpus states
-- (Sun '30 days', Jupiter ~1 year, Saturn '30 months'/'900 days' per sign). NUMERIC VALUES ARE NOT TOUCHED (WAVE-1 Part B = SS decision).
-- Reseals the engine sha256 inside BOTH stored integrity checks (bg_transit_engine, and the composite bg_transit_rules check).
--
-- GUARDS  engine content hash must equal the pinned pre-state; each UPDATE matches graha AND exact old citation, exactly 9 rows;
--         the engine hash literal must occur exactly once in each registry check (so this composes with #3049's rules reseal in either
--         order); english_description pinned; post-flight: pinned post hash, no row still cites BPHS Ch.22 as a source, the engine
--         check reads true, and the rules check reads true iff it did before (it is only true while the rules table is at its sealed content).
--         Idempotent: second apply = NOTICE + no-op.
-- Seed parity: platform/python-sidecar/brahmagyan/l0_transit.py BG_TRANSIT_ENGINE must carry the same citations or the next rebuild
--         reverts them -> DRAFT_l0_transit_engine_seed_curation.patch (stales nirmana-writer-digests.json: wait for #2984).
--         Also: nirmana_l0_transit_integrity_contract.test.ts pins HASHES.engine; it must be re-baselined with the seed patch.
-- =============================================================================

DO $curation$
DECLARE
  c_old constant text := 'e2dafc84d7fef9b8a05ad01b98b036686e8ec0af9694a4d43ac4b2b8c425797b';
  c_new constant text := '104aa45b4221b5cdbe123f6a288219991b8a2a898718cf9713c33bf79a3819ae';
  c_desc_old constant text := $d$L0 average graha motion parameters — daily motion, zodiac period, sign residence. Source: BPHS Ch.22.$d$;
  c_desc_new constant text := $d$L0 average graha motion parameters — daily motion, zodiac period, sign residence. The period values coincide with modern mean sidereal periods; none is a classical statement: the former 'Source: BPHS Ch.22' was refuted (served bphs:PG22:C1 is Chapter 2, incarnations). Only round sign-residence figures for the Sun, Jupiter and Saturn are stated in the held corpus; each row's classical_citation says exactly which cell, if any, is sourced.$d$;
  hash_sql constant text := $q$SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(graha,avg_daily_motion_deg,zodiac_period_days,
      sign_residence_days,classical_citation)::text,
    E'\n' ORDER BY graha COLLATE "C"
  ),''),'UTF8')),'hex') FROM bg_transit_engine$q$;
  eng_ic text; rul_ic text; eng_desc text;
  h text; n integer; ok boolean; rules_ok_before boolean;
BEGIN
  SELECT integrity_check_sql, english_description INTO eng_ic, eng_desc FROM asset_registry WHERE asset_id = 'bg_transit_engine' FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'curation refuses: asset_registry row bg_transit_engine not found'; END IF;
  SELECT integrity_check_sql INTO rul_ic FROM asset_registry WHERE asset_id = 'bg_transit_rules' FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'curation refuses: asset_registry row bg_transit_rules not found'; END IF;
  EXECUTE hash_sql INTO h;
  IF h = c_new THEN
    IF position(c_new IN eng_ic) = 0 OR position(c_new IN rul_ic) = 0 THEN
      RAISE EXCEPTION 'curation refuses: engine table is at the curated content but a registry contract is not resealed';
    END IF;
    RAISE NOTICE 'curation already applied: no-op';
    RETURN;
  END IF;
  IF h IS DISTINCT FROM c_old THEN RAISE EXCEPTION 'curation refuses: bg_transit_engine is not the pinned pre-state (%)', h; END IF;
  IF (length(eng_ic) - length(replace(eng_ic, c_old, ''))) <> length(c_old)
     OR (length(rul_ic) - length(replace(rul_ic, c_old, ''))) <> length(c_old) THEN
    RAISE EXCEPTION 'curation refuses: the engine hash literal is not present exactly once in both stored integrity checks';
  END IF;
  IF eng_desc IS DISTINCT FROM c_desc_old THEN RAISE EXCEPTION 'curation refuses: bg_transit_engine english_description has drifted'; END IF;
  EXECUTE rul_ic INTO rules_ok_before;

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
  EXECUTE hash_sql INTO h;
  IF h IS DISTINCT FROM c_new THEN RAISE EXCEPTION 'curation post-flight: engine content hash mismatch (%)', h; END IF;
  SELECT count(*) INTO n FROM bg_transit_engine WHERE classical_citation LIKE '%BPHS Ch.22 (Graha Gati%' AND classical_citation NOT LIKE 'PARTIALLY SOURCED%' AND classical_citation NOT LIKE 'UNSOURCED%';
  IF n <> 0 THEN RAISE EXCEPTION 'curation post-flight: % engine rows still cite BPHS Ch.22 as a source', n; END IF;

  UPDATE asset_registry SET integrity_check_sql = replace(integrity_check_sql, c_old, c_new), english_description = c_desc_new WHERE asset_id = 'bg_transit_engine';
  GET DIAGNOSTICS n = ROW_COUNT; IF n <> 1 THEN RAISE EXCEPTION 'curation expected 1 engine registry row, updated %', n; END IF;
  UPDATE asset_registry SET integrity_check_sql = replace(integrity_check_sql, c_old, c_new) WHERE asset_id = 'bg_transit_rules';
  GET DIAGNOSTICS n = ROW_COUNT; IF n <> 1 THEN RAISE EXCEPTION 'curation expected 1 rules registry row, updated %', n; END IF;

  SELECT integrity_check_sql INTO eng_ic FROM asset_registry WHERE asset_id = 'bg_transit_engine';
  EXECUTE eng_ic INTO ok;
  IF ok IS NOT TRUE THEN RAISE EXCEPTION 'curation post-flight: bg_transit_engine stored integrity_check_sql reads false'; END IF;
  SELECT integrity_check_sql INTO rul_ic FROM asset_registry WHERE asset_id = 'bg_transit_rules';
  EXECUTE rul_ic INTO ok;
  IF ok IS DISTINCT FROM rules_ok_before THEN RAISE EXCEPTION 'curation post-flight: bg_transit_rules stored check changed from % to %', rules_ok_before, ok; END IF;
END
$curation$;

-- VERIFY: SELECT graha, left(classical_citation, 60) FROM bg_transit_engine ORDER BY graha;  then execute both stored integrity_check_sql: expect t
