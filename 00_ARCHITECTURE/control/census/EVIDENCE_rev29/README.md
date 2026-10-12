# Rev-29 census evidence (baseline only, no ledger records)

This folder and the three `asset_census_*.json` files next to it are the committed evidence for the registry revision 29 certification census. They are a hash-anchored baseline. They are NOT per-criterion ledger records: `asset_certs.jsonl` is not touched (owner decision N-152, SS ruling D1 / N-529).

## What was measured

| Item | Value |
|---|---|
| Backup id | 1791769727082 |
| Backup time | 2026-10-12T01:50:08.186Z |
| Instance (evaluation copy) | amjis-ri02-validation-c720f1832 |
| Source instance | amjis-postgres |
| Census target | `evaluation_copy` (not the live production database) |
| Tool / code tree | fbecd9387 (`fbecd93873292c6e3a1a2954f1192bb27a3b0c75`), tool_dirty false |
| Registry | revision 29, fingerprint `834aff17dbef83ddc90ba743e23b83831187c860d2c6cad0f3369cff3120fb79` |
| Declarations | 1.76.0, sha256 `7bd69d89c12dc5654ed78a4ee2431268f43f24a3dbf7883e5f129c9f1881c9ee` |
| Scope | chart `482012f1-710e-4a25-994a-93821f5871aa` plus the global L0 reference layer; layers L0, L1, L2 (39 + 20 + 23 = 82 assets) |
| Limits | statement cap 600 s per census read, lock timeout 5 s, integrity runner 900 s (exempt from the statement cap); a cancelled read reads NO_DETECTOR; layers were run staggered, at most two at a time: L1 and L0 together, L2 started when L0 finished (see `run_L*.log`, `read_timings_L*.txt`, `timeouts.txt`) |

Census files, one per layer, archived byte-identically with `nikasha_certify.py --archive-census` (names are the tool's own, from each file's `generated` stamp):

| Layer | Committed file | Source file | Assets |
|---|---|---|---|
| L0 | `../asset_census_2026-10-12T082909+0530.json` | `census_L0.json` | 39 |
| L1 | `../asset_census_2026-10-12T092313+0530.json` | `census_L1.json` | 20 |
| L2 | `../asset_census_2026-10-12T092857+0530.json` | `census_L2.json` | 23 |

The `census_Lx.json#sha12` references inside `lists/CERTIFIED_LIST.*` are the first 12 hex digits of the sha256 of these files (see `SHA256SUMS.txt`).

## Result

* Owner bar N-268 (named ceilings and disclosure gaps allowed): **76 of 82 CERTIFIED** (L0 38 of 39, L1 18 of 20, L2 20 of 23).
* Strict bar (every criterion PASS or a ruled N/A): **13 of 82 CERTIFIED**.
* "Certified" here means: listed in the census `CERTIFIED_LIST` on the owner bar for registry revision 29, measured on the named backup. It does not mean ledger records exist, and it does not mean every check passed: 69 of the 76 sit at a declared ceiling.
* Not certified (6): `bg_sky_calendar` (L0); `ga_structural`, `ga_vichara` (L1); `bo_laksana`, `bo_laksana_rerank`, `bo_samskara` (L2). Reasons per asset: `lists/BLOCKERS_BY_CLASS.md`, `lists/FIX_LIST.md`, `OWNER_SUMMARY_rev29.md`.
* Information-only failures that block nothing: Count.floor on `bg_parihara_rules`, `ga_vichara`, `ga_yoga`; Cost.baseline on `bg_ephemeris_engine`, `bg_panchanga`.

## Known gaps

* No semantic fingerprints exist for 37 of the certified assets, so a ledger could not have been written for them.
* `Carr.D2` has no detector: it reads N/A by ruling on every asset.
* No CI job runs `nikasha_certify.py --verify-census-hashes` (the tool's docstring says one does). With no ledger records the command has nothing to check; byte-identity of the committed census files is verified by `SHA256SUMS.txt` against the source files.
* The census measured an evaluation copy of production, not production itself.

## Contents

* `lists/CERTIFIED_LIST.*`, `lists/BLOCKERS_BY_CLASS.*`, `lists/FIX_LIST.*`: owner-bar lists. `lists/strict_*`: the same for the strict bar (copied from the source `strict/` folder).
* `postprocess.log`, `postprocess_strict.log`: post-processing summaries. `run_L0.log`, `run_L1.log`, `run_L2.log`: census run logs.
* `EVAL_COPY.json`: the evaluation-copy marker. `read_timings_L*.txt`, `timeouts.txt`: read timings and retries.
* `OWNER_SUMMARY_rev29.md`: the owner-facing summary.
* `SHA256SUMS.txt`: sha256 of every committed file in this folder and of the three census files (paths relative to `00_ARCHITECTURE/control/census/`). Check with `cd 00_ARCHITECTURE/control/census && shasum -a 256 -c EVIDENCE_rev29/SHA256SUMS.txt`.

Never edit these files after merge: the census files are bound to their names by the tool (`census_path_reused`).
