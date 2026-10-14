# Owner summary: certification census after the vocabulary round (registry revision 30)

Written for: the owner (non-technical). This is the third measurement. Earlier ones are kept apart and never mixed: revision 28 (66 of 82), revision 29 (76 of 82). Revision 30 was measured twice on the same code; both runs are kept. Detail files are next to this one: `lists/CERTIFIED_LIST.md`, `lists/BLOCKERS_BY_CLASS.md`, `lists/FIX_LIST.md`, `lists/strict_*`. The first run is in `../EVIDENCE_rev30_run1_75/`.

## Bottom line
**77 of the 82 data assets are certified** on the agreed bar (named limits and disclosed gaps allowed): up from 76 at revision 29. On the stricter bar, where every check must pass or be formally "not applicable", **13 of 82** (unchanged, the same 13 assets as at revision 29).

**Result of record: the second run (77).** The first run of the same code read 75. Both are kept; the differences are explained below and are not defects of the data: the one that remains (ga_vichara) is a confirmed detector flaw triggered by later registry edits.

**What "certified" means here:** the census's certified list on the agreed bar (N-268), for registry revision 30, measured on a copy of production restored from backup 1791868791537 (taken 13 Oct 2026 05:21 UTC, 10:51 India time) for the native's chart plus the shared reference data. It is **not** a set of formal per-check ledger records: you dropped that ceremony (decision N-152), and this round keeps to that. The measurement files are committed in the repository as a hash-verified baseline.

## By layer (certified / total), second run
| Layer | Certified | Not certified |
|---|---|---|
| Reference data (L0) | 39 of 39 | none |
| Chart facts (L1) | 18 of 20 | ga_structural, ga_vichara |
| Synthesis (L2) | 20 of 23 | bo_laksana, bo_laksana_rerank, bo_samskara |

69 of the 77 sit at a *declared limit* (single derivation 45, unverified transcription of a classical text 20, unsourced by declaration 3, ratified judgement 4). They are stated openly, not hidden. Certified does not mean every check passed.

## Gained and lost
**Against revision 29 (76):** gained **bg_sky_calendar** (eclipse timings: a measured, class-based tolerance replaced one blanket limit; 25 shallow-partial eclipses out of 622 have a wider bound, ordinary eclipses stay at 180 seconds). Lost: none. Net 77. (ga_vichara was not certified at revision 29 and is not certified now, but for a different reason; see below.)

**Against the first run of revision 30 (75):**
| Change | Asset | Why |
|---|---|---|
| gained | bg_ephemeris_engine, bg_panchanga | Run 1 found their last health check 35 hours old against a 24-hour rule (time, not code). In run 2 the health checks were fresh (last self-test 0.7 hours before the read) and report healthy. |
| gained | bo_chart_gestalt | Run 1 read two checks as partial because one database connection timed out after 10 seconds and the census recorded it as "not read" without saying why (a weakness in the census, not in the data). The data confirm shows it would have passed (`../EVIDENCE_rev30_run1_75/gestalt_confirm.txt`). Run 2 made no failed connection. |
| lost | ga_vichara | Certified in run 1; the Build.dag check fails in run 2. See the plain statement below. |

## The 5 not certified, and what each needs
| Asset | What it needs |
|---|---|
| ga_structural | Vocab.alias PARTIAL: the spelling mix cleaned up at retrieval time (planet codes JUP next to names Jupiter, and sign names, in the same columns of the chart-facts table). A separate item surfaced once its registry row named its table: four columns it never fills (salience_formula_ver, tolerance_arcsec, cross_ayanamsha_divergence_arcsec, formula_id). Each needs the builder to fill it, the column dropped, or a declared "empty by design" ruling. |
| bo_laksana | Vocab.alias PARTIAL: mixed spelling families in the signal columns (copied values from the chart-facts layer): needs the designed engine change for copied values (one spelling check at the source, not repeated in every layer above) plus the spelling cleanup and a ruling on the prose columns. Also its Build.completion check cannot run (NO_DETECTOR): the census account may not call the database function `bodha_signal_identity`, same as revision 29; the fix is to rewrite that check without the function, or accept it. Not the blocker on its own. |
| bo_laksana_rerank | Vocab.alias PARTIAL: the same mixed spelling families, plus 8 JSON paths in the signal table that hold vocabulary and are not declared (fact_key, fact_subject, fact_value_text, l1_formula_id, member_sample_keys, nakshatra, nakshatras, neecha_bhanga rules; part of them is the nakshatra spelling change) and 6 paths that hold none and are not declared as such. |
| bo_samskara | Narr.agree, Null.blank_rows and Null.schema_default PARTIAL: the census checker cannot follow the builder's insert (an unresolved write path and an unbalanced column list in its scan). Needs the checker changes (about 300 lines across two files) and one small builder change; deferred with your sign-off. |
| ga_vichara | Build.dag FAIL in run 2; see the next section. |

## ga_vichara: a plain statement
**ga_vichara was certified on the release in run 1** (the evidence for the daridra dosha slice worked: the builder records proof that it checked and found none for this chart, and the census credits the empty result only when that proof is present, belongs to the right run and chart, and is consistent). **In run 2 it shows Build.dag FAIL**, on the same code tree (7e63cc872), the same declarations (1.77.0) and the same census version. The census says: ga_vichara's builder reads the table `build_runs` (ga_vichara_writer.py:1002), `build_runs` is now attributed as a product of `ka_jivana_parva`, `ka_kala_darshana` and `ka_kalasutra`, and those already depend on ga_vichara (chain ka_jivana_parva -> ka_sangam -> bo_laksana -> ga_vichara), so no dependency edge can be added without a cycle.

**The diagnosis is finished. Confirmed facts** (source: read-only sessions on the second copy, backup 1791868791537, plus a trace of the census code):
1. Migrations 1353, 1354, 1355 and 1356 are recorded in `_migrations_applied` on the second copy and were applied to the database at 2026-10-12 22:28:21 to 22:28:25Z: **applied between the two backups** (first backup 20:15Z, second 13 Oct 05:21Z). Merge time is not apply time: #3404 merged at 20:13:59Z, about one minute before the first backup, but its migrations were applied at 22:28Z.
2. The census builds table ownership from the active, writer-backed `asset_registry` rows: `build_table_owners` (asset_census.py:20774-20788) gives a row its `target_table` plus every FROM/JOIN relation of its `count_sql` (`_count_tables`, :14558). On the second copy `ka_jivana_parva`, `ka_kala_darshana` and `ka_kalasutra` each have a `count_sql` joining `public.build_runs` (their `integrity_check_sql`, which starts `WITH k6_target AS (... FROM public.build_runs ...)`, is ignored by the ownership map). `ga_vichara` has no `build_runs` in its registry text.
3. `ga_vichara_writer.py:1002` is `SELECT created_at FROM build_runs WHERE id = %s`. In run 1 `build_runs` had no owner and the read was skipped (`_reads_clause`, :20917-20918). In run 2 it has three owners, the read counts as a back-read, and the cell shows the chain ka_jivana_parva -> ka_sangam -> bo_laksana -> ga_vichara = FAIL.
4. **It is a detector flaw:** `BOOKKEEPING_TABLES` (:15332) is used only by Build.completion and the event-stream check, not by the product (ownership) map, so a shared run-history table is attributed to three assets as a "product".
5. Exposure: Build.dag compared across all 82 assets between the two runs differs in exactly one cell (ga_vichara PASS to FAIL). The census's reads scan over all 82 writers finds ga_vichara the only writer reading a bookkeeping table. A fix that skips bookkeeping tables in the owner map changes only the owner set of `build_runs` (tables 159 to 158) and no other run-2 cell.
6. Not established: the diagnosis found no other changed Build.dag cell and no other change in the bookkeeping-table owner map; **a full registry diff between the two copies was not made.**

**What this means for the record.** The 77 is the measured result of record. ga_vichara was certified on the same release tree (7e63cc872) in run 1 and failed Build.dag in run 2 only because of the later registry edits (the four Kala migrations above), through the detector flaw in point 4. A fix is proposed (a separate pull request, held; it needs a registry revision 31). The fix and a revision-31 count are with the owner's decision. Until then ga_vichara stays "not certified" in this record; it is not shown as a pass, and run 1's certification is kept as stated evidence, not as the result.

## What was settled this round
- bg_rules, bg_ontology, bg_concordance were fixed and re-sealed last round; this round re-sealed the nakshatra and other stored checks: ga_structural's registry entry now names its table and its 82 data categories; three stale count floors were set to the measured counts (information only).
- Kāla's nakshatra spelling package (canonical spellings in the chart-facts layer) went in with a safety check that stops the migration if the stored text is not what was expected.
- Two bugs found and fixed on the way: the birth-star lookup of one timing module asked for "Moon" while the data stores "MOON" (so it silently used the first star), and a lookup for the star Mrigashira stopped matching after the spelling change.

## The spelling inventory: what the data actually contains
The question was whether the reference list of accepted spellings covers everything in the data. We read every table that can hold a planet, sign, nakshatra or house name, across all layers, on the restored copy of the first backup (read-only; 13 minutes; 427 of 459 reads complete).
- **68 spellings in the data are unknown to the reference list** (28 planet forms, 30 nakshatra forms, 9 sidereal-frame (ayanamsha) names, 1 division name).
- **31 spellings are known only if capital letters are ignored**: house_1 to house_9, "Dhanishta" (2,604 rows) and "Karka" (3,002 rows). A lookup that cares about capitals would miss them.
- **704 composed labels** such as "a planet in a house" or "cycle and nakshatra", used as identifiers. They need a pattern rule, not a list.
- **The alias sources disagree on 201 spellings**, including 29 graha aliases the ontology cannot resolve.
- **Only one place in the code is live-wrong**: a remedy loader looks up "Saturn" where the data stores "saturn" (38 rows). The other ten flagged places are stale line numbers, comments or harmless arguments.
- **Top ten fixes, by rows affected:** 1) add a sidereal-frame class to the reference list (about 1.5 million rows); 2) make the front-end lookup find dasha-system names (about 200,000 rows); 3) settle the "lagna" and "D9" ambiguities; 4) classify the non-planet words in planet columns; 5) fix "Karka"; 6) "Dhanishta"; 7) house_1 to house_9; 8) standardise chart-facts subject codes; 9) register the CamelCase nakshatra spellings in the timing tables; 10) the Saturn loader check.
- **Coverage gaps, stated plainly:** 14 reads were refused to the census's read-only account (12 gochara tables and 2 conversation reads); 4 tables do not exist on the copy (bg_sky_events, ganita_positions, bodha_signals, kala_timeline); 18 reads skipped for that reason; forms hidden inside long sentences are not covered; "never used" means "not used in this chart plus the reference layer".
- The inventory files themselves are not part of this folder (they are working files outside the repository).

## Lessons (standing operational rules)
1. **Build windows**: rebuild only after the last change that names an asset; one release, one rebuild, one count.
2. **A changed writer needs its stored checks re-sealed in the same release**, and the sweep must follow dependencies (a stale fingerprint lock and a revision-pinned fixture both surfaced only when the full test list was run).
3. **The test list must be the one the automated checks collect**, not a hand-written one; and the database-backed tests must be run on a local throwaway database before arming.
4. **A health check's freshness is measured at read time** (24-hour window): take the checks, then the backup, then the census within a few hours. Run 2 confirms it: the same two services certify when the probe is fresh.
5. **A failed connection must never read as "not read" silently**: the census needs a retry and the error text (approved, to follow the evidence).
6. **The counting tool depends on the folder it is run from**: run the post-process from the governance folder of the release tree, and record it (both run records do).
7. **When an action is refused, stop and report**: no workaround route (SS rule N-587).
8. **Revision labels**: counts at revisions 28 (66), 29 (76) and 30 (75 first run, 77 second run) are never mixed.
9. **Registry edits made by another campaign between two copies can flip a cell** on unchanged code (ga_vichara). A census measures the code and the registry rows on its copy; when two copies of one release differ, diff the registry rows before reading a change as progress or regression. Both runs are kept for that reason.

## What was not covered
Kāla (timing layers), Mimāṃsā and Phala are not part of these counts. The other two charts are out of scope until all six layers succeed on the native's chart. The bo_samskara checker work, bo_laksana declarations, the probe-record declaration (it goes stale at the next probe) and the ga_structural option are on the after-round list.

## What I need from you
- The close-out choice for this evidence pull request (it is held, not armed): merge both runs as written, merge now (the ga_vichara diagnosis is closed), or hold until the fix and a revision-31 count exist.
- Your decision on ga_vichara: the diagnosis confirms a detector flaw. Whether the detector fix (held pull request, registry revision 31) goes ahead and a third run (revision 31) is taken, or the result stays at 77 with ga_vichara listed as not certified and the cause stated.
- Your sign-off, later, on the after-round designs (templated-identifier form for copied values; bo_samskara checker work; the spelling retrieval layer).
- Two confirmations SS carries: who edited the project settings file and when (it is not part of the release), and your approval of creating migration 1364.
