-- 1271_bg_transit_engine_honest_attribution.sql
--
-- Suvarna Track I, WAVE-1 (bg_transit_engine fix; routed by Exec Suvarna from L0_WAVE_SURVEY; design
-- TrackI/WAVE1_TRANSIT_ENGINE_FIX_DESIGN.md; number 1271 allocated by SS): replace the REFUTED citation on the nine
-- bg_transit_engine rows by an honest per-row attribution, declare what the table is, and re-seal the integrity
-- digests that cover the citation column. NO NUMERIC VALUE IS CHANGED.
--
--   1. bg_transit_engine.classical_citation, 9 rows:
--        'BPHS Ch.22 (Graha Gati - Planetary Motion)'  ->  'UNSOURCED - modern mean value; ...'   (8 rows)
--                                                      ->  'PARTLY SOURCED - 'about one year per sign' ...' (jupiter)
--   2. asset_registry.integrity_check_sql of bg_transit_engine AND of bg_transit_rules: the engine sha256 literal
--        e2dafc84d7fef9b8a05ad01b98b036686e8ec0af9694a4d43ac4b2b8c425797b -> e5c09a112502b241cbd4aecf5ae30cfb2a93423f928c84a94dee37e6818b8c3d
--      (the bg_transit_rules check embeds the engine digest as its first conjunct, so it must be re-sealed too; the
--      rules' own digest 1dbdd265... and the moorti digest b411c02a... are untouched).
--   3. asset_registry.english_description of bg_transit_engine (drops "Source: BPHS Ch.22.").
--   4. COMMENT ON TABLE + three COMMENT ON COLUMN (metadata): what the columns are and the measured identity gaps.
--
-- CONCERN (design doc, measured read-only 2026-10-03)
--   Every row cites 'BPHS Ch.22 (Graha Gati)'. In the served corpus bphs page 22 (PG22:C1) is the avatara passage
--   ("From the Sun God the incarnation of Rama ..."), and `chapter` is a page number: the citation is refuted for all
--   nine rows (same family as 'BPHS Ch.29'). Searching all 16 texts for a classical statement of each value finds ONE:
--   Jupiter spends about a year in each sign (yavana_jataka PG900:C1 "Jupiter spends approximately one year in each
--   sign", PG662:C1 "(at the rate of one sign a year)"; bphs PG933:C1 "Jupiter stays in one sign for one year"), and only
--   as the round figure (361.05 is a modern mean). Every other number is a modern astronomical mean (or an uncited
--   traditional figure). Migration 565 already records 'BPHS Ch.22 Graha Gati' as "not confirmed in corpus: honest gap
--   per B.10" in bg_gochara_citation_resolution; this file brings the engine rows in line with that.
--   The stored values are also mutually inconsistent in three of the nine rows beyond rounding (|motion| vs
--   360/period, residence vs period/12): mercury motion 1.3833 vs 4.0923 (-66.2%) and residence 14 vs 7.33 (+91.0%);
--   venus 1.2 vs 1.6021 (-25.1%) and 23 vs 18.72 (+22.8%); mars residence 45 vs 57.25 (-21.4%); saturn/rahu/ketu within
--   2-3%. The table comment lists all nine.
--
-- WHY NO VALUE IS CHANGED (SS instruction: unsourced values get an honest marker, not an invented figure)
--   The design's Part B (mercury 1.3833 -> 4.0923, venus 1.2 -> 1.6021, residences -> 30.44) is only meaningful after
--   SS/acharya fix ONE convention for the columns (Part A), and the design itself lists the geocentric alternative as
--   "equally defensible" for a transit table. Further, 1.3833 and 1.2000 are exactly 1 deg 23 min and 1 deg 12 min
--   (sexagesimal round figures), which suggests the two motion values come from a traditional table of average
--   apparent daily motion rather than from an error; if so the defect is the UNDECLARED CONVENTION (the periods are
--   heliocentric), not the value, and "correcting" the motion to 360/period would replace a traditional figure by a
--   different convention. That is not verified in the corpus (acharya to confirm), so it is recorded in the table
--   comment, not acted on. Mars 45, saturn 913.37 and rahu/ketu 548 days are likewise left as stored.
--
-- LOCKSTEP WITH THE WRITER (same PR): platform/python-sidecar/brahmagyan/l0_transit.py BG_TRANSIT_ENGINE carries the
-- SAME nine citation strings. The writer converges the rows to that module on every dispatch of bg_transit_rules /
-- bg_transit_engine (ON CONFLICT (graha) DO UPDATE ... classical_citation), so WITHOUT the module change the next
-- dispatch would REVERT this file and the re-sealed digest would read false (loud, but a build-blocking surprise). The
-- test proves module rows == the rows this migration writes == the re-sealed digest. Editing the module stales
-- platform/src/generated/nirmana-writer-digests.json, a file owned by PR #2984: THIS PR IS KNOWN RED on
-- `provenance_inventory --check` until #2984 lands and the inventory is regenerated (the #3015/#3016 precedent). Do not
-- dispatch bg_transit_rules / bg_transit_engine between applying this migration and deploying the sidecar image built
-- from this PR.
--
-- SERVING / FRESHNESS EFFECT AT APPLY
--   * integrity_check_sql is a trigger column of nirmana_registry_receipt_invalidation. Fires for:
--       bg_transit_engine  : no asset_freshness row exists -> nothing to stale.
--       bg_transit_rules   : asset_freshness row (fresh, 2026-10-01) -> STALE, reason registry_changed. It has SIX
--                            declared dependents (ka_moorti_nirnaya, ka_gochara, ka_sangam, ka_yojaka,
--                            ka_vedha_gochara, ka_gochara_resonance); asset_runner.deps_unsatisfied requires a data
--                            dependency's freshness to be 'fresh', so a dispatch of any of them reads
--                            "bg_transit_rules(receipt:stale)" and is BLOCKED until bg_transit_rules is rebuilt (the
--                            rebuild with the module from this PR is idempotent: it writes the same rows and a fresh
--                            receipt). Sequence with SS: apply, deploy the sidecar, dispatch bg_transit_rules, THEN
--                            dispatch the L3 assets.
--     Assets that go stale: bg_transit_rules ONLY (bg_transit_engine has no freshness row).
--   * english_description is not a trigger column. The served tool query_transit_engine returns classical_citation
--     per row, so the served TEXT of the citation changes (numbers do not); its description/disclaimer
--     ("classical ... BPHS Ch.22") is in the generated capability census (a #2984 file) and is NOT edited here.
--   * Cockpit: nothing reads the new comments at serve time.
--
-- GUARDS (every one raises rather than skip; an empty bg_transit_engine = fresh bootstrap = NOTICE skip)
--   * the table content must hash EXACTLY to the audited digest (the registry's own recipe, e2dafc84...), all nine
--     citations must be the old string; or already hash to the new digest with the new registry text (then skipped);
--   * md5 of bg_transit_engine's integrity_check_sql (9c1b1f5b6792fc4643d689e5124fa554), of its english_description
--     (3ffe36c1c59b3bfac653fd198ce3cf46) and of bg_transit_rules's integrity_check_sql
--     (a3ded694827457ffaf640d24ff1e4057), read live 2026-10-03; each text must contain the old digest EXACTLY ONCE;
--   * nine rows updated, the new table digest recomputed in-migration must equal the pinned e5c09a112502b241cbd4aecf5ae30cfb2a93423f928c84a94dee37e6818b8c3d,
--     and BOTH stored integrity_check_sql texts are EXECUTED after the update and must return true.
--
-- PRIVILEGE (P2 rule, W1_PRIVILEGE_AUDIT): runs as amjis_app, OWNER of bg_transit_engine (UPDATE and COMMENT) and of
-- asset_registry / asset_freshness / the trigger function. No CREATE, no GRANT, no DDL beyond COMMENT. Proven as
-- amjis_app (NOSUPERUSER, NOINHERIT, no CREATE on schema public).
--
-- IDEMPOTENT: a second run finds the new digest in table and registry and changes nothing (the COMMENTs re-apply
-- identically).
--
-- NOT DONE HERE
--   * Any numeric value (above); the SS decision on one convention (strict identity vs declared traditional figures
--     for mars/saturn/rahu; geocentric vs heliocentric for mercury/venus); an external source for the non-Jupiter
--     values ([EXTERNAL_COMPUTATION_REQUIRED] / external source required: Surya Siddhanta mean motions, BPHS gochara
--     durations or IAU/JPL periods, with the edition, from the acharya or SS; none is invented here).
--   * The generated capability census / served tool text (#2984), the seed literal english_description in
--     platform/scripts/seed/asset_registry_seed.ts (#2984; the seed's ON CONFLICT rewrites english_description from the
--     literal, so a routine re-seed would restore the text 'Source: BPHS Ch.22.' until that literal is edited), the
--     writer-digest inventory regeneration (#2984), the failing-first invariant test of the design (the three identities
--     cannot pass until a convention is chosen), a machine-readable attribution_state on this table (TI-L0-09 covers
--     four other tables).
--
-- ROLLBACK (ops reference, not executed): restore the nine old citations, the old digest literal in both
-- integrity_check_sql texts and the old english_description with a new reviewed migration against the then-current
-- state; never edit this file after apply.
--
-- VERIFY AFTER APPLY by production structure, not the deploy log (Trap 103):
--   SELECT graha, left(classical_citation, 28) FROM bg_transit_engine ORDER BY graha;     -- UNSOURCED... x8, PARTLY SOURCED... jupiter
--   SELECT asset_id FROM asset_registry WHERE asset_id IN ('bg_transit_engine','bg_transit_rules')
--      AND integrity_check_sql LIKE '%e5c09a112502b241cbd4aecf5ae30cfb2a93423f928c84a94dee37e6818b8c3d%';                                          -- both
--   SELECT integrity_check_sql FROM asset_registry WHERE asset_id = 'bg_transit_engine' \gexec     -- t
--   SELECT integrity_check_sql FROM asset_registry WHERE asset_id = 'bg_transit_rules' \gexec      -- t
--   SELECT freshness_state, reasons FROM asset_freshness WHERE asset_id = 'bg_transit_rules';      -- stale, ["registry_changed"]
--
-- Transaction ownership belongs to platform/scripts/migrate.ts (BEGIN/COMMIT around this file).

SET LOCAL lock_timeout = '5s';

DO $m1271$
DECLARE
    old_cit    constant text := 'BPHS Ch.22 (Graha Gati ' || chr(8212) || ' Planetary Motion)';
    cit_unsourced constant text := $c$UNSOURCED - modern mean value; no classical statement of this figure was found in the served corpus (searched across the 16 texts of classical_text_chunks on 2026-10-03). The former citation 'BPHS Ch.22 (Graha Gati)' is refuted: corpus BPHS page 22 is the avatara passage. Column convention undeclared; internal checks in COMMENT ON TABLE bg_transit_engine.$c$;
    cit_jupiter   constant text := $c$PARTLY SOURCED - 'about one year per sign' is classical (yavana_jataka PG900:C1 and PG662:C1; bphs PG933:C1); the stored 0.0831 deg/day, 4332.59 days and 361.05 days are modern mean values, not stated in the corpus. The former citation 'BPHS Ch.22 (Graha Gati)' is refuted: corpus BPHS page 22 is the avatara passage. Column convention undeclared; internal checks in COMMENT ON TABLE bg_transit_engine.$c$;
    new_desc      constant text := $c$L0 average graha motion parameters - daily motion, zodiac period, sign residence. Modern mean values, NOT corpus-sourced: only Jupiter's 'about one year per sign' is (yavana_jataka PG900:C1, PG662:C1; bphs PG933:C1); the former citation 'BPHS Ch.22' is refuted. See COMMENT ON TABLE bg_transit_engine.$c$;
    old_hash   constant text := 'e2dafc84d7fef9b8a05ad01b98b036686e8ec0af9694a4d43ac4b2b8c425797b';
    new_hash   constant text := 'e5c09a112502b241cbd4aecf5ae30cfb2a93423f928c84a94dee37e6818b8c3d';
    old_desc_md5     constant text := '3ffe36c1c59b3bfac653fd198ce3cf46';
    engine_sql_md5   constant text := '9c1b1f5b6792fc4643d689e5124fa554';
    rules_sql_md5    constant text := 'a3ded694827457ffaf640d24ff1e4057';
    hash_sql   constant text := $q$SELECT encode(sha256(convert_to(COALESCE(string_agg(jsonb_build_array(graha,avg_daily_motion_deg,zodiac_period_days,sign_residence_days,classical_citation)::text, E'\n' ORDER BY graha COLLATE "C"),''),'UTF8')),'hex') FROM bg_transit_engine$q$;
    v_n        bigint;
    v_hash     text;
    v_engine_sql text;
    v_rules_sql  text;
    v_desc       text;
    v_rows       bigint;
    v_ok         boolean;
BEGIN
    EXECUTE 'SELECT count(*) FROM bg_transit_engine' INTO v_n;
    IF v_n = 0 THEN
        RAISE NOTICE '1271: bg_transit_engine is empty (fresh bootstrap, rows come from the writer); skipped';
        RETURN;
    END IF;
    EXECUTE hash_sql INTO v_hash;

    SELECT integrity_check_sql, english_description INTO v_engine_sql, v_desc
      FROM asset_registry WHERE asset_id = 'bg_transit_engine' FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION '1271: bg_transit_engine is not in asset_registry; refusing (registry contract unknown)';
    END IF;
    SELECT integrity_check_sql INTO v_rules_sql
      FROM asset_registry WHERE asset_id = 'bg_transit_rules' FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION '1271: bg_transit_rules is not in asset_registry; refusing (registry contract unknown)';
    END IF;

    -- already applied: table, both checks and the description are all at the new state
    IF v_hash = new_hash AND v_desc = new_desc
       AND strpos(v_engine_sql, new_hash) > 0 AND strpos(v_engine_sql, old_hash) = 0
       AND strpos(v_rules_sql, new_hash) > 0 AND strpos(v_rules_sql, old_hash) = 0 THEN
        RAISE NOTICE '1271: bg_transit_engine citations and digests are already at the new state; skipped';
        RETURN;
    END IF;

    -- otherwise it must be EXACTLY the audited pre-state
    IF v_hash IS DISTINCT FROM old_hash
       OR md5(v_engine_sql) IS DISTINCT FROM engine_sql_md5 OR md5(v_rules_sql) IS DISTINCT FROM rules_sql_md5
       OR md5(v_desc) IS DISTINCT FROM old_desc_md5
       OR (length(v_engine_sql) - length(replace(v_engine_sql, old_hash, ''))) <> length(old_hash)
       OR (length(v_rules_sql)  - length(replace(v_rules_sql,  old_hash, ''))) <> length(old_hash)
       OR (SELECT count(*) FROM bg_transit_engine WHERE classical_citation = old_cit) <> 9 THEN
        RAISE EXCEPTION '1271: bg_transit_engine has drifted from the audited state (table sha256=%, md5(engine check)=%, md5(rules check)=%, md5(description)=%); refusing',
            v_hash, md5(v_engine_sql), md5(v_rules_sql), md5(v_desc);
    END IF;

    -- 1. the nine citations (numbers untouched)
    UPDATE bg_transit_engine
       SET classical_citation = CASE WHEN graha = 'jupiter' THEN cit_jupiter ELSE cit_unsourced END
     WHERE classical_citation = old_cit;
    GET DIAGNOSTICS v_rows = ROW_COUNT;
    IF v_rows <> 9 THEN
        RAISE EXCEPTION '1271: citation update touched % rows, expected 9', v_rows;
    END IF;
    EXECUTE hash_sql INTO v_hash;
    IF v_hash IS DISTINCT FROM new_hash THEN
        RAISE EXCEPTION '1271: the recomputed table digest % is not the pinned %', v_hash, new_hash;
    END IF;

    -- 2. re-seal both integrity checks (text patch of the one digest literal) and 3. the description
    UPDATE asset_registry
       SET integrity_check_sql = replace(integrity_check_sql, old_hash, new_hash), english_description = new_desc
     WHERE asset_id = 'bg_transit_engine' AND md5(integrity_check_sql) = engine_sql_md5;
    GET DIAGNOSTICS v_rows = ROW_COUNT;
    IF v_rows <> 1 THEN
        RAISE EXCEPTION '1271: bg_transit_engine registry update touched % rows, expected 1', v_rows;
    END IF;
    UPDATE asset_registry
       SET integrity_check_sql = replace(integrity_check_sql, old_hash, new_hash)
     WHERE asset_id = 'bg_transit_rules' AND md5(integrity_check_sql) = rules_sql_md5;
    GET DIAGNOSTICS v_rows = ROW_COUNT;
    IF v_rows <> 1 THEN
        RAISE EXCEPTION '1271: bg_transit_rules registry update touched % rows, expected 1', v_rows;
    END IF;

    -- Post-check: the two re-sealed checks themselves must read true, never trust a silent no-op.
    FOR v_engine_sql IN SELECT integrity_check_sql FROM asset_registry
                         WHERE asset_id IN ('bg_transit_engine', 'bg_transit_rules') ORDER BY asset_id LOOP
        EXECUTE v_engine_sql INTO v_ok;
        IF v_ok IS DISTINCT FROM true THEN
            RAISE EXCEPTION '1271: a re-sealed integrity check does not read true after the update';
        END IF;
    END LOOP;
    IF EXISTS (SELECT 1 FROM asset_registry
                WHERE asset_id IN ('bg_transit_engine', 'bg_transit_rules')
                  AND (strpos(integrity_check_sql, old_hash) > 0 OR strpos(integrity_check_sql, new_hash) = 0)) THEN
        RAISE EXCEPTION '1271: an integrity_check_sql does not carry exactly the new digest after the update';
    END IF;
END
$m1271$;

COMMENT ON TABLE bg_transit_engine IS $c$WAVE-1 (migration 1271). The three numeric columns are MODERN MEAN values and are NOT corpus-sourced; the only classical statement the served corpus supports is Jupiter's 'about one year per sign' (yavana_jataka PG900:C1 and PG662:C1; bphs PG933:C1). The former citation 'BPHS Ch.22' is refuted (corpus BPHS page 22 is the avatara passage). No single convention is declared for the columns. Internal identities, measured from the stored values and NOT corrected (SS/acharya decision pending); per graha: |avg_daily_motion_deg| vs 360/zodiac_period_days (error), sign_residence_days vs zodiac_period_days/12 (error): sun 0.9856 vs 0.9856 (-0.0%), 30.44 vs 30.44 (+0.0%); moon 13.1764 vs 13.1772 (-0.0%), 2.28 vs 2.28 (+0.1%); mars 0.524 vs 0.5240 (-0.0%), 45 vs 57.25 (-21.4%); mercury 1.3833 vs 4.0923 (-66.2%), 14 vs 7.33 (+91.0%); jupiter 0.0831 vs 0.0831 (+0.0%), 361.05 vs 361.05 (+0.0%); venus 1.2 vs 1.6021 (-25.1%), 23 vs 18.72 (+22.8%); saturn 0.0335 vs 0.0335 (+0.1%), 913.37 vs 896.60 (+1.9%); rahu 0.0529 vs 0.0530 (-0.2%), 548 vs 566.12 (-3.2%); ketu 0.0529 vs 0.0530 (-0.2%), 548 vs 566.12 (-3.2%). Mercury 1.3833 and Venus 1.2000 equal 1 deg 23 min and 1 deg 12 min exactly (sexagesimal round figures), which suggests a traditional table rather than a computed rate; NOT verified in the corpus (acharya to confirm). This table is an average-motion reference, not an ephemeris.$c$;
COMMENT ON COLUMN bg_transit_engine.avg_daily_motion_deg IS $c$Mean angular rate in degrees per day (negative for the retrograde nodes). Modern mean value, not corpus-sourced; convention undeclared (see the table comment).$c$;
COMMENT ON COLUMN bg_transit_engine.zodiac_period_days IS $c$Days for one zodiac traversal. The stored values are the modern sidereal orbital periods (87.97 and 224.70 days are the HELIOCENTRIC periods of mercury and venus). Not corpus-sourced.$c$;
COMMENT ON COLUMN bg_transit_engine.sign_residence_days IS $c$Average days spent per sign. Equals zodiac_period_days/12 for sun, moon and jupiter only; for mars, mercury, venus, saturn, rahu and ketu it does not (see the table comment). Not corpus-sourced, except Jupiter's 'about one year per sign'.$c$;
COMMENT ON COLUMN bg_transit_engine.classical_citation IS $c$Attribution in words: UNSOURCED, or PARTLY SOURCED for jupiter. The former 'BPHS Ch.22' citation is refuted. Machine-readable attribution_state (TI-L0-09) is not carried by this table.$c$;
