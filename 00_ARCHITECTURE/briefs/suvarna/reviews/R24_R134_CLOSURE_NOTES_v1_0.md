# Closure notes for register rows R24 and R134 (corrections required by the independent review)

Source: R24_R134_REVIEW_FINDINGS.md (reviewed commit 191cb1f47, PR #3133). These notes are the corrections the reviewer asked for; they are the
wording every closure of R24 or R134 must carry.

## What is claimed
Six read-only censuses (L0 to L5) at registry revision 25, registry fingerprint 0e78e228d140d04920cb12bcd8b5bd9c8b33ca59ac8f9105853a139b8289d698,
tool commit 400c8556c, committed under `00_ARCHITECTURE/control/census/` as `asset_census_2026-10-04T{193639,194909,195251,195534,195644,195749}+0530.json`,
each stamped with the production database identity (database `amjis`, `system_id_sha256` dc44e645...1731, equal to the production entry of
`00_ARCHITECTURE/control/REGISTERED_DB_IDENTITIES.json`). 127 assets, 1,143 gate cells: 215 PASS, 12 N/A, 152 PARTIAL, 662 NO_DETECTOR, 102 FAIL;
54 of 127 assets have no FAIL cell; no asset has all nine gates PASS.

## Qualifications that must travel with the closure (review findings)
1. MED-1 (lineage only): the identity stamp proves cluster lineage, not that the live primary was read; a physical replica or restore carries the
   same system identifier. Read-only mode and the reader role are facts of the operator record, not of the files.
2. MED-2 (clean re-run is true for the tool, not for every cell): no layer aborted and no asset is ERRORED, but four integrity checks could not run
   under the census role (ga_structural too large for psql; bo_laksana and ka_jivana_parva permission denied; bo_samvada is a view with a stub
   count_sql) and 662 cells are NO_DETECTOR, which is "no detector", not "pass". These carry forward as known gaps, not as closed.
   "Clean" means no layer aborted and no asset is ERRORED; it does not mean every cell was measured.
3. MED-3 (different tool named): the R134 clause names `asset_elevation_tracker.py --layer L3 --env-file`; the evidence is `asset_census.py` output
   for L3 (17 of 21 assets with live_rows from count_sql, the 4 nulls are declared services with no count_sql). The closure says so: no run of the named tracker probe is evidenced; the evidence file is
   `asset_census_2026-10-04T195534+0530.json`, not `L3_prod_20260926.json`; the earlier unstamped rev-10 L3 census (2026-10-02T101208) has identical
   live_rows for all 17 measured assets, so whether it was sandbox or production cannot be told from the files.
4. MED-5 (revision is provisional): a revision bump before J1 changes the registry fingerprint and means one more rerun of the six layers (about
   21 minutes: the six files' generation timestamps span 19:36:39 to 19:57:49 IST); the closure holds only while revision 25 stands.
5. Point-in-time: one run per layer, 19:36 to 19:57 IST on 2026-10-04; migrations 1262, 1275 and 1288 and later writer changes may post-date the tool commit.
6. LOW-1: two census files quote local operator paths inside stored build-error text (not credentials).
7. MED-4 (register state): PR #3133 added only the six census files; R24 and R134 still read OPEN until the register fold, which is a separate step that
   follows these notes. R24 is BLOCKS_FREEZE: the native must confirm that 'run + clean re-runs' is the T4 pass condition. Optional: record the DB role and
   `pg_is_in_recovery` to remove the lineage-only limit.

## Closure wording (to be used in the register `--reason`)
R24: "T4 exercise closed by post-fix re-runs: six-layer read-only census at registry rev 25 on main (191cb1f47, PR #3133); 'clean' = no layer aborted, no asset ERRORED; db_identity stamped (cluster lineage, not primary proof); four integrity checks unmeasurable under the census role and 662 NO_DETECTOR cells carried forward as open gaps; point-in-time 2026-10-04; closure holds only while revision 25 stands (a bump means a rerun)."
R134: "L3 census at production cluster lineage exists: asset_census.py L3 at rev 25 (asset_census_2026-10-04T195534+0530.json; 17 of 21 assets measured by count_sql on chart 482012f1, 4 declared services without count_sql), db_identity stamped (cluster lineage, not primary proof); no run of the named asset_elevation_tracker.py probe is evidenced, the census tool was run; point-in-time 2026-10-04; holds only while revision 25 stands."
