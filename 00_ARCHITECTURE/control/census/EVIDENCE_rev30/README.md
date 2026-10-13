# Rev-30 census evidence (baseline only, no ledger records)

This folder, the three `asset_census_2026-10-13T120326+0530.json`, `...T125017+0530.json`, `...T130122+0530.json` files next to it, and the sibling folder `EVIDENCE_rev30_run1_75/` (with its own three census files) are the committed evidence for the registry revision 30 certification census. They are a hash-anchored baseline. They are NOT per-criterion ledger records: `asset_certs.jsonl` is not touched (owner decision N-152, SS ruling D1 / N-529), the same mode as rev 29 (PR #3447).

## Two runs, one result of record

| | Run 2 (RESULT OF RECORD) | Run 1 (stated evidence, kept) |
|---|---|---|
| Folder | `EVIDENCE_rev30/` (this one) | `EVIDENCE_rev30_run1_75/` |
| Backup id | 1791868791537 | 1791835965446 |
| Backup time | 2026-10-13T05:21:32.951Z | 2026-10-12T20:15:07.308Z |
| Census wall time (UTC) | 2026-10-13 05:33 to 07:31:25 (about 1 h 58 min) | 2026-10-12T20:26:03 to 22:22:50 |
| N-268 (owner bar) | **77 of 82 CERTIFIED** | 75 of 82 CERTIFIED |
| Strict bar | 13 of 82 | 13 of 82 (same 13 assets, and the same 13 as rev 29) |
| Exit / timeouts | 0 / none (`timeouts.txt` empty) | 0 / none |
| Census files (generated stamp) | L0 `2026-10-13T12:03:26+05:30`, L1 `12:50:17`, L2 `13:01:22` | L0 `2026-10-13T02:54:40+05:30`, L1 `03:42:45`, L2 `03:52:47` |

Run 2 is the result. Run 1 is kept, not hidden: it measured the same tree on an earlier copy of the database and read 75; its three causes are stated in `../EVIDENCE_rev30_run1_75/README.md`. The two runs are never mixed and the revision-28 (66), revision-29 (76) counts are separate measurements.

## What was measured (both runs)

| Item | Value |
|---|---|
| Instance (evaluation copy) | amjis-ri02-validation-c720f1832; source instance amjis-postgres |
| Census target | `evaluation_copy` (not the live production database) |
| Tool / code tree | `7e63cc872eda2da19eed3b484c6e36569e03bf50` (short `7e63cc872`), `tool_dirty` false, a detached clean checkout, git status empty before and after |
| Registry | revision 30, fingerprint `b1acb3f678b5c8fbe343b93d96d8f2db24e2d024b15412aa960056b98bc5f23c` |
| Declarations | 1.77.0, sha256 `cda70d03b86bf61a365b89d3752af868e04b3b41296adec009565c71eced2f62` (= `platform/scripts/governance/asset_declarations.json` at 7e63cc872) |
| Scope | chart `482012f1-710e-4a25-994a-93821f5871aa` plus the global L0 reference layer; layers L0, L1, L2 (39 + 20 + 23 = 82 assets) |
| Limits | statement cap 600 s per census read, lock timeout 5 s, integrity runner 900 s (exempt from the cap); a cancelled read reads NO_DETECTOR; layers ran staggered, at most two at a time: L1 and L0 together, L2 started when L0 finished |
| Command (no secret) | `EVAL_BACKUP_ID=1791868791537 EVAL_BACKUP_TIME=2026-10-13T05:21:32.951Z CENSUS_ASSETS_EXPECTED=82 CENSUS_OUT_DIR=<run dir> /bin/bash run_census_on_copy.sh <census-run-rev30 checkout>` (full text in `RUN_RECORD.md`) |
| Post-process | run from `platform/scripts/governance` of the release tree: cwd `/Users/Dev/worktrees.noindex/madhav/claude/census-run-rev30/platform/scripts/governance`, `git rev-parse --show-toplevel` there = `/Users/Dev/worktrees.noindex/madhav/claude/census-run-rev30` (both runs; see the two `RUN_RECORD.md`) |

Census files, one per layer, archived byte-identically with `nikasha_certify.py --archive-census` (names are the tool's own, from each file's `generated` stamp; no suffix is added, as in rev 29):

| Run | Layer | Committed file (in `../`) | Source file | Assets | `census_Lx.json#sha12` in the lists |
|---|---|---|---|---|---|
| 2 | L0 | `asset_census_2026-10-13T120326+0530.json` | `census_L0.json` | 39 | 7f9c53786923 |
| 2 | L1 | `asset_census_2026-10-13T125017+0530.json` | `census_L1.json` | 20 | f4a3131036ef |
| 2 | L2 | `asset_census_2026-10-13T130122+0530.json` | `census_L2.json` | 23 | c7b49c719c34 |
| 1 | L0 | `asset_census_2026-10-13T025440+0530.json` | `census_L0.json` | 39 | cca13ab8b230 |
| 1 | L1 | `asset_census_2026-10-13T034245+0530.json` | `census_L1.json` | 20 | 3d4aaae1c7da |
| 1 | L2 | `asset_census_2026-10-13T035247+0530.json` | `census_L2.json` | 23 | f416f533a706 |

The `#sha12` references inside `lists/CERTIFIED_LIST.*` are the first 12 hex digits of the sha256 of these files (see the `SHA256SUMS.txt` of each folder).

## Result (run 2)

* Owner bar N-268 (named ceilings and disclosure gaps allowed): **77 of 82 CERTIFIED** (L0 39 of 39, L1 18 of 20, L2 20 of 23).
* Strict bar (every criterion PASS or a ruled N/A): **13 of 82 CERTIFIED**.
* "Certified" means: listed in the census `CERTIFIED_LIST` on the owner bar for registry revision 30, measured on the named backup. It does not mean ledger records exist, and not that every check passed: 69 of the 77 sit at a declared ceiling.
* Against rev 29 (76): gained `bg_sky_calendar`; lost none. Against run 1 (75): gained `bg_ephemeris_engine`, `bg_panchanga`, `bo_chart_gestalt`; lost `ga_vichara`.
* Not certified (5): `ga_structural` (L1), `ga_vichara` (L1), `bo_laksana`, `bo_laksana_rerank`, `bo_samskara` (L2). Reasons per asset: `lists/BLOCKERS_BY_CLASS.md`, `lists/FIX_LIST.md`, `OWNER_SUMMARY_rev30.md`.
* Information-only failures that block nothing: Cost.baseline on `bg_ephemeris_engine` and `bg_panchanga` still reads FAIL in the raw L0 log (it does not block certification under N-268).
* `ga_vichara` Build.dag FAIL in run 2: diagnosed as a detector flaw triggered by later registry edits (migrations 1353-1356, applied between the two backups); see `OWNER_SUMMARY_rev30.md`. The 77 is the measured result; a fix and a revision-31 count are with the owner's decision.

## Per-layer timings (wall seconds from `run_L*.log`; reads from `read_timings_L*.txt`)

| Layer | Run 2 wall | Run 2 reads (total s, slowest) | Run 1 wall | Run 1 reads (total s, slowest) |
|---|---|---|---|---|
| L0 | 3608 s | 967 (3515.9 s; 572.0 s bg_ephemeris) | 3512 s | 967 (3420.6 s; 562.0 s bg_ephemeris) |
| L1 | 6420 s | 1047 (6354.5 s; 416.8 s ga_dashas) | 6397 s | 1049 (6331.1 s; 405.7 s ga_dashas) |
| L2 | 3477 s | 497 (3433.1 s; 385.8 s bo_drishti) | 3488 s | 497 (3444.9 s; 391.7 s bo_drishti) |

Run 2: every retained read ended `ok`, zero retries, zero timeouts. Run 1 had one `error` read (L2, `bo_chart_gestalt` prose checks, 10.03 s); not repeated in run 2.

## Verification

* `shasum -a 256 -c EVIDENCE_rev30/SHA256SUMS.txt` (and the same for `EVIDENCE_rev30_run1_75/SHA256SUMS.txt`), run from `00_ARCHITECTURE/control/census`: every file in each folder plus that run's three census files.
* **Which tool wrote the archive:** the procedure script `write_rev29_certs.sh` (kept outside the repository in the SS evidence folder, described in its rev-29 certificates procedure; it calls the repo's own `platform/scripts/governance/nikasha_certify.py`), run in `--no-records` mode from a worktree cut exactly at the census tree 7e63cc872 (this branch's base), once per run, calling `nikasha_certify.py --archive-census` for each layer file. Both runs passed the script's own guard: layer heads equal this tree's registry (revision 30, fingerprint `b1acb3f678b5c8fb...`), `declarations_sha256` equals the committed declarations at this tree (`cda70d03b86b...`), `tool_commit` is an ancestor of HEAD with `tool_dirty` false, the three layer files agree on tool, database identity and target, and every `census_Lx.json#sha12` in `CERTIFIED_LIST` equals its file's sha256 (guard line: `OK: 77 certified assets` for run 2, `OK: 75 certified assets` for run 1). The copies were also compared byte for byte (`cmp`) with the source files; `--archive-census` never overwrites.
* The census files are the only content the tool wrote; the other files in the two folders are copies of the run's own outputs plus the README and owner summary.
* `nikasha_certify.py --verify-census-hashes --repo . --ref HEAD` returns NO_DETECTOR (exit 3, "ledger holds no gate record: nothing was verified") because the ledger has no records; the sha256 manifests are the byte-identity evidence.

## Known gaps

* No semantic fingerprints exist for 37 of the certified assets, so a ledger could not have been written for them.
* `Carr.D2` has no detector: it reads N/A by ruling on every asset.
* No CI job runs `nikasha_certify.py --verify-census-hashes`.
* The census measured an evaluation copy of production, not production itself.
* `ga_vichara` Build.dag: a full registry diff between the two copies was not made; the diagnosis found no other changed Build.dag cell and no other change in the bookkeeping-table owner map.

## Contents

* `lists/CERTIFIED_LIST.*`, `lists/BLOCKERS_BY_CLASS.*`, `lists/FIX_LIST.*`: owner-bar lists. `lists/strict_*`: the same for the strict bar (copied from the source `strict/` folder).
* `postprocess.log`, `postprocess_strict.log`: post-processing summaries. `run_L0.log`, `run_L1.log`, `run_L2.log`: census run logs. `read_timings_L*.txt`, `timeouts.txt`: read timings and retries.
* `RUN_RECORD.md`: the run record of this run (command, tree, cwd and toplevel of the post-process, walls, scans). `EVAL_COPY.json`: the evaluation-copy marker.
* `OWNER_SUMMARY_rev30.md`: the owner-facing summary.
* `SHA256SUMS.txt`: sha256 of every committed file in this folder and of this run's three census files (paths relative to `00_ARCHITECTURE/control/census/`). Check with `cd 00_ARCHITECTURE/control/census && shasum -a 256 -c EVIDENCE_rev30/SHA256SUMS.txt`.

Never edit these files after merge: the census files are bound to their names by the tool (`census_path_reused`).
