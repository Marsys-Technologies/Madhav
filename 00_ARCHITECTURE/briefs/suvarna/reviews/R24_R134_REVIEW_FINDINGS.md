# Independent review: evidence for Nikasha register rows R24 and R134

Reviewer scope: read-only. Scratch worktree detached at 191cb1f474e1c1a4e104ee8c5a66984abaad3702 (PR #3133), removed afterwards. No database or production access; no credential or env files read. All numbers below were recomputed by script from the six JSON files and from the repo at that commit.

Evidence reviewed: `00_ARCHITECTURE/control/census/asset_census_2026-10-04T{193639,194909,195251,195534,195644,195749}+0530.json`.

## Verdicts

ROW R24: ACCEPT_WITH_CORRECTIONS
Judged against (register line 160): "Exercised on L1-L5 (T4) ... OPEN - census executed L1-L5 during campaign; remaining: production L3 census (R134) and clean re-runs after fixes". Plan P10 wording: "R24 (T4 exercise closed by the post-fix clean re-runs)".

ROW R134: ACCEPT_WITH_CORRECTIONS
Judged against (register line 317): "Production row counts via own count_sql - the census is sandbox; live_rows null x23; L3_prod_20260926.json missing (only its log). Clause (T3 s1.1): 'the production probe (asset_elevation_tracker.py --layer <L> --env-file)' -> The L3 production census must exist".

Both are accepted on the content of the evidence; the corrections are about how the closure is worded and recorded (see MED-1 to MED-4), not about the numbers.

## Claim-by-claim result

1. Layer files, 127 assets, revision and fingerprint: CONFIRMED.
   - One layer key per file (L0, L1, L2, L3, L4, L5; plus `rollup`, `rollup_excluded`). Asset counts 40/19/23/21/9/15 = 127; `n_assets == len(assets) == population_active` in each file; `set(rollup.layers[Lk]) == set(assets ids)` for each.
   - `registry_revision` = 25 in every layer head and in each `rollup`; `registry_fingerprint` = 0e78e228d140d04920cb12bcd8b5bd9c8b33ca59ac8f9105853a139b8289d698 everywhere (also stamped on every gate cell). Importing `platform/scripts/governance/asset_census.py` from the scratch worktree gives `REGISTRY_REVISION == 25` and `registry_fingerprint()` == that same value. There is no module attribute named `ACTIVE` in asset_census.py; the "active population" is carried as `population_active` in the files and is internally consistent, so the comparison that can be made is revision + fingerprint (equal).
   - asset_census.py is byte-identical between 400c8556c and 191cb1f47 (empty diff), so the fingerprint computed at the merge commit is the fingerprint at the tool commit.
   - `declarations_sha256` 2ae16d8449730f4424183d37db29f9b477415641af4c2e34dcb4802460e9ccbb, version 1.15.0, equal in all six; equals the sha256 of `asset_declarations.json` at 400c8556c and at 191cb1f47 (recomputed).
2. Tool commit: CONFIRMED. All six carry `tool_commit` 400c8556c205dfde0a386504eef837e710df9a13, `tool_dirty` false. `git cat-file -t` = commit; `merge-base --is-ancestor` to 191cb1f47 = yes. Commit is "E1.7 prerequisites: census db_identity head stamp ..." (#3088), 2026-10-04 13:47 UTC; the runs are 19:36-19:57 IST (14:06-14:27 UTC), about 20-40 minutes later. Caveat in LOW-2.
3. Identity stamp: CONFIRMED. All six carry `db_identity` {schema nikasha_db_identity/1, database amjis, system_id_sha256 dc44e645...1731}; byte-equal to the `production` entry of `00_ARCHITECTURE/control/REGISTERED_DB_IDENTITIES.json` (role production, database amjis, same hash, two evidence reads dated 2026-10-03). Secrets scan (regex over all six files for IPv4, hostnames/domains, postgres://, password, sslmode, host/port/user/dbname keys, URLs, emails, api-key/secret/bearer, hex of 32+ chars): no IP, host, port, user, password, URL, email, or connection string. The only long hex strings are the registry fingerprint (hundreds of repetitions, one per gate cell), the declarations sha, the identity sha, tool_commit, and per-text-chunk content sha256 fields from L0 (phaladeepika hunks etc.); the single UUID outside chart_id is a bodha_cgm_nodes node_id inside an old build-error message. "token" hits are the phrase "raw-token lint". Two findings from the scan are in LOW-1 (local filesystem paths).
4. L3 is a measured census: CONFIRMED (with the qualification in MED-3). `chart_scope` = 482012f1-710e-4a25-994a-93821f5871aa; `chart_scoped_count_sql` = 17 of 21; `population_active` 21, `population_registry_total` 25 (4 inactive: ka_gochara_sweep RETIRED; ka_gochara_v3_century_materialize, ka_gochara_v4_41_candidate, ka_gochara_v5 inactive/phantom); `registry_has_writer` 21; `never_exercised_with_writer` empty. 17 of 21 assets have `live_rows` non-null, every one with `live_rows_basis` = "count_sql over the target table". The 4 nulls (ka_dasha_kala, ka_graha_sancara, ka_muhurta_seva, ka_tulana) are `asset_kind: service` with `count_sql_declared: false`, no target table, and Build.completion = N/A "no count_sql and nothing to count": null by declaration, not a failed measurement. No asset is ERRORED: no per-asset error field exists in any of the 127 asset records, and no cell of any layer carries a census-query exception (the nearest are 4 deliberate "integrity not measurable" cells, MED-2). Values: ka_avadhi 1169, ka_bhavishya_lekha 0, ka_gochara 87, ka_gochara_resonance 623, ka_jivana_parva 100, ka_kala_darshana 0, ka_kalasutra 0, ka_kota_chakra 585, ka_kshetra 8,570,075, ka_moorti_nirnaya 74, ka_sangam 0, ka_sudarshana_varsha 120, ka_taranga 92,412, ka_tithi_pravesha 120, ka_vedha_gochara 171, ka_vighnakara 0, ka_yojaka 50,678.
   - Across all six layers, only 6 assets have null `live_rows` (L0: bg_ephemeris_engine, bg_panchanga; L3: the four above), all declared services. The "x23" in R134 does not reproduce even in the earlier rev-10 censuses of 2026-10-02 (6 nulls) - it describes a still earlier sandbox census.
5. Internal consistency: CONFIRMED, exactly.
   - Every one of 127 assets has exactly the 9 gates Ldgr, Idem, Earn, Null, Vocab, Carr, Narr, Dens, Build.
   - 127 x 9 = 1,143 cells: PASS 215, N/A 12, PARTIAL 152, NO_DETECTOR 662, FAIL 102 (sum 1,143). Matches the author's numbers exactly.
   - Zero-FAIL assets: 54 of 127 (L0 16/40, L1 17/19, L2 13/23, L3 5/21, L4 0/9, L5 3/15). Assets with all nine gates PASS: 0.
   - Per layer cells (PASS/PARTIAL/NO_DETECTOR/FAIL/N/A): L0 74/25/215/35/11; L1 52/41/76/2/0; L2 38/48/109/11/1; L3 23/13/126/27/0; L4 17/8/43/13/0; L5 11/17/93/14/0.
   - Gate-vs-check rules over 1,143 cells and 3,175 checks: every FAIL gate has at least one FAIL check; no PASS gate has a non-PASS/N-A check; no non-FAIL gate carries a FAIL check; every cell carries revision 25 and the file's fingerprint. 0 inconsistencies.
   - L3 contribution to the 102 FAILs is 27 cells (23 PASS, 13 PARTIAL, 126 NO_DETECTOR).
6. Provenance caveats: see MED-1 and LOW section.
7. Closure support: see verdicts and corrections below.

## Findings

### HIGH
None. Nothing in the files contradicts the author's claims, and no number failed to recompute.

### MED
MED-1. The identity stamp proves cluster lineage, not that the primary was read. REGISTERED_DB_IDENTITIES.json states this itself: a physical replica or physical restore of production carries the same `system_identifier`; the registration evidence is two reads by two sessions through the same role (suvarna_reader) against one target, so they attest the value, and "that the target is production" is the operators' recorded decision (SS N-119 / E1.7(b)). The six files contain no field recording the DB role, read-only mode, replication state (`pg_is_in_recovery`), or the time of the stamp. So "measured on production" rests on: the identity match + the operators' decision + the tool's read-only design (`psql_read_only`, `SET default_transaction_read_only`). Read-replica staleness would be undetectable from these files. Correction: the closure note should say "cluster lineage amjis / dc44e645...1731; role and replica state not recorded".

MED-2. "Clean re-run" is true for the tool, not for every cell. No layer aborted and no asset is ERRORED, and the T4 census defects R40-R51 are all CLOSED on 2026-09-27 (R41 per-asset fault isolation, R46 view counts, R49 latest-error text all visibly working in the files). But four cells could not be measured under the census role and read NO_DETECTOR/PARTIAL: L1 ga_structural Build.completion (integrity_check_sql 207,968 bytes, too large for psql -c; PARTIAL), L2 bo_laksana (42501 permission denied for function bodha_signal_identity), L3 ka_jivana_parva (42501 permission denied for table charts), plus L2 bo_samvada (view, stub count_sql; NO_DETECTOR). These are recorded honestly by the tool (never PASS), but R24 should say "clean" means "no tool failure, no ERRORED asset", and carry these four cells forward (the messages themselves point at "Track I: rewrite the check"). Also 662 of 1,143 cells (58%) are NO_DETECTOR: the T4 exercise ran, but it shows that most gates still lack detectors on L1-L5; that is a finding of the exercise, not a defect in the re-run.

MED-3. The literal R134 clause names a different tool. T3 §1.1 / LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md:165 says "the production probe (asset_elevation_tracker.py --layer <L> --env-file)"; the evidence is `asset_census.py` output (the census), not an elevation-tracker run, and the file is named `asset_census_2026-10-04T195534+0530.json`, not `L3_prod_20260926.json`. The register row's own conclusion ("The L3 production census must exist") is what the evidence meets. Correction: the R134 closure note should say the clause is met by the census, name the file, and state that no `asset_elevation_tracker.py --layer L3 --env-file` run is evidenced here (R30 makes the tracker consume the census JSON, so the two are linked, but that run is not part of this evidence). Also: the earlier rev-10 L3 census (2026-10-02T101208) has identical live_rows for all 17 non-null L3 assets and no identity stamp, so the files cannot show whether the old census was sandbox or production; what is now provable is only that this one is stamped.

MED-4. The register is not yet updated. PR #3133 adds only the six JSON files; R24 and R134 still read OPEN in NIKASHA_CHANGE_REGISTER_v2_0.md at 191cb1f47. Closure needs its own register edit citing commit 191cb1f47, the six file names, revision 25 / fingerprint 0e78e228..., and the caveats above. R24 is BLOCKS_FREEZE (header counts it with R39 and R71), so the freeze criterion ("all five tests pass in production tooling", T4 is only "run" today) also needs the native's reading that "run + clean re-runs" is the T4 pass condition.

MED-5. Revision bump means a rerun. `REGISTRY_REVISION = 25` is marked "(provisional)" in the source (N-99). Any further bump (the plan's pre-J1 changes) changes `registry_fingerprint`, and these six files then no longer describe the live census rules; they stay a valid dated record of rev 25 only. R24/R134 can close on rev 25 only if no rule that decides a cell changes before the point where the freeze gate reads them; otherwise the freeze run must be repeated (the tool stamps revision and fingerprint, so a stale file is detectable, not silently accepted).

### LOW
LOW-1. Two files embed local operator paths in stored build-error text: L1 (1 occurrence) and L3 (2 occurrences) contain `/Users/Dev/Vibe-Coding/Apps/Madhav/platform/...` inside traceback strings (historical writer errors quoted by Build.history). Not a credential or connection detail, but it discloses the operator's account name and checkout path in a committed file.

LOW-2. `tool_dirty:false` covers only the tool file and its declared runtime files (`git status --untracked-files=no` over those paths), not the writer files the census statically scans and not the checkout as a whole. Migrations 1262, 1275 and 1288 and several writers (ka_gochara_v5.py, ph_pramana.py, ph_rectification) landed after 400c8556c; whether production had them applied when the census ran (19:36-19:57 IST on 2026-10-04) is not stated. Example: ph_pramana reads FAIL (rows_written 139 vs live 4 for the canonical chart), and migration 1288 (HELD at the time) changes its integrity check, so the cell describes pre-1288 behaviour.

LOW-3. Timing: one run per layer, 19:36:39 to 19:57:49 IST, 21 minutes end to end; layers were not read at one instant. Row counts drift (L1 ga_strength moved 14,141 to 17,011 between 2026-10-02 and 2026-10-04). They are point-in-time measurements; they do not prove current rows.

LOW-4. Four L3 registry rows are inactive and outside the census population (ka_gochara_sweep, ka_gochara_v3_century_materialize, ka_gochara_v4_41_candidate, ka_gochara_v5); `local_map_candidates` is -1 (unknown). The L3 census therefore says nothing about ka_gochara_v5 despite its writer changing after the tool commit.

LOW-5. Real measured defects that this evidence now makes visible (not evidence defects): five L3 assets have live_rows 0 and FAIL Count.floor and Build.completion (ka_bhavishya_lekha, ka_kala_darshana, ka_kalasutra, ka_sangam, ka_vighnakara); ka_kshetra Idem FAIL (rebuild refused when target populated). These belong to their own register rows, not to R24/R134 closure.

## What the files do NOT prove
- That the primary (not a replica or physical restore) was read; that role = suvarna_reader; that the session was read-only (only tool design and the operator record say so).
- That production state is unchanged since 19:36-19:57 IST 2026-10-04, or that the six layers are mutually consistent at one instant.
- That migrations 1262/1275/1288 and post-400c8556c writer changes are reflected in the measured cells.
- That any NO_DETECTOR cell is healthy (662 cells are "no detector", not "pass"); that the 54 zero-FAIL assets are good, only that no detector returned FAIL.
- That a rule change after revision 25 would leave the verdicts valid.
- That the tracker (`asset_elevation_tracker.py`) was run on L3 against production.

## R24 "clean re-runs after fixes": decision
Rev-25 reruns of all six layers satisfy it: same tool commit and fingerprint, no aborted layer, no ERRORED asset, post-dating the closure of R40-R51 (2026-09-27), L0-L5 all present. What is missing for an unqualified close: (a) the register edit recording closure with the caveats (MED-4); (b) explicit carry-forward of the four unmeasurable integrity cells (MED-2); (c) the native's confirmation that rev 25 is the revision to freeze against, or a rerun after any further bump (MED-5); (d) optionally, a recorded role / pg_is_in_recovery read to remove MED-1.

Final:
ROW R24: ACCEPT_WITH_CORRECTIONS
ROW R134: ACCEPT_WITH_CORRECTIONS
