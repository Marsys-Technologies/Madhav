# Rev-30 census evidence, RUN 1 (75 of 82): stated evidence, secondary

This is the FIRST measurement of registry revision 30. It is kept as stated evidence and is NOT the result of record. The result of record is run 2 (77 of 82) in `../EVIDENCE_rev30/`; read its `README.md` and `OWNER_SUMMARY_rev30.md` first. The two runs measured the same code tree on two different copies of the database and are never mixed.

## What was measured

| Item | Value |
|---|---|
| Backup id | 1791835965446 |
| Backup time | 2026-10-12T20:15:07.308Z |
| Instance (evaluation copy) | amjis-ri02-validation-c720f1832; source instance amjis-postgres; census target `evaluation_copy` |
| Tool / code tree | `7e63cc872eda2da19eed3b484c6e36569e03bf50`, `tool_dirty` false |
| Registry | revision 30, fingerprint `b1acb3f678b5c8fbe343b93d96d8f2db24e2d024b15412aa960056b98bc5f23c`; declarations 1.77.0, sha256 `cda70d03b86bf61a365b89d3752af868e04b3b41296adec009565c71eced2f62` |
| Run (UTC) | 2026-10-12T20:26:03Z to 22:22:50Z; exit 0; no timeouts |
| Command (no secret) | `EVAL_BACKUP_ID=1791835965446 EVAL_BACKUP_TIME=2026-10-12T20:15:07.308Z CENSUS_ASSETS_EXPECTED=82 CENSUS_OUT_DIR=<run dir> /bin/bash run_census_on_copy.sh <census-run-rev30 checkout>` (see `RUN_RECORD.md`) |
| Post-process | cwd `/Users/Dev/worktrees.noindex/madhav/claude/census-run-rev30/platform/scripts/governance`; `git rev-parse --show-toplevel` there = `/Users/Dev/worktrees.noindex/madhav/claude/census-run-rev30` |
| Walls | L0 3512 s, L1 6397 s, L2 3488 s (reads and slowest in `read_timings_L*.txt`) |
| Result | N-268: **75 of 82 CERTIFIED** (L0 37 of 39, L1 19 of 20, L2 19 of 23); strict 13 of 82 (same 13 assets as run 2 and rev 29) |

Census files (archived byte-identically with `nikasha_certify.py --archive-census`, tool-given names, in `../`):

| Layer | Committed file | Assets | `#sha12` in the lists |
|---|---|---|---|
| L0 | `asset_census_2026-10-13T025440+0530.json` | 39 | cca13ab8b230 |
| L1 | `asset_census_2026-10-13T034245+0530.json` | 20 | 3d4aaae1c7da |
| L2 | `asset_census_2026-10-13T035247+0530.json` | 23 | f416f533a706 |

## Why run 1 read 75 and run 2 read 77 (the causes, stated)

Run 1 versus revision 29 (76): gained `bg_sky_calendar` and `ga_vichara`; lost `bg_ephemeris_engine`, `bg_panchanga` and `bo_chart_gestalt`. Not certified (7): `bg_ephemeris_engine`, `bg_panchanga`, `bo_chart_gestalt`, `ga_structural`, `bo_laksana`, `bo_laksana_rerank`, `bo_samskara`.

1. **`bg_ephemeris_engine` and `bg_panchanga`** (Earn.service_state NO_DETECTOR, basis "wired-stale"): their last recorded health probe was 34.94 to 34.96 hours old against the 24-hour freshness window. Time, not code. In run 2 the probe was fresh (0.7 hours) and both certify.
2. **`bo_chart_gestalt`** (Null.blank_rows and Null.schema_default PARTIAL): one database connection failed to open (libpq timeout, 10.03 s, the single `outcome: error` read in `census_L2.json`, label "Narr/Null (prose checks)") and the census swallowed it into "not read". This is a detector weakness (a failed connect must be retried and must say so). A read-only confirm of the data on this run's copy shows it would pass: `gestalt_confirm.txt` (SQL: `gestalt_confirm.sql`) lists, for each of the six closed entries, one distinct stored value equal to a declared literal, no stray values, "closure WOULD PASS". In run 2 there was no failed connection and the asset certifies.
3. **`bo_laksana`**: Build.completion reads NO_DETECTOR because the census role cannot EXECUTE the database function `bodha_signal_identity` (permission denied). Identical in revision 29 and in run 2. It is not the blocker (Vocab.alias PARTIAL is).

`ga_vichara` was CERTIFIED in this run on release tree 7e63cc872 and fails Build.dag in run 2 on the same tree, only because of later registry edits (Kala migrations 1353-1356, applied to the database at 2026-10-12 22:28Z, between the two backups) acting through a detector flaw (the table-ownership map attributes the shared `build_runs` table to three Kala assets). Confirmed facts: `../EVIDENCE_rev30/OWNER_SUMMARY_rev30.md` ("ga_vichara: a plain statement").

## Verification

`cd 00_ARCHITECTURE/control/census && shasum -a 256 -c EVIDENCE_rev30_run1_75/SHA256SUMS.txt` (every file in this folder plus this run's three census files). Copies were compared with the sources byte for byte (`cmp`) and the archive was written by the same tool as run 2 (`write_rev29_certs.sh --no-records` at tree 7e63cc872), which passed its own guard for this run (`OK: 75 certified assets`; see `../EVIDENCE_rev30/README.md`). No ledger record exists for this run (owner decision N-152).

## Contents

`lists/` (owner-bar lists and `strict_*`), `postprocess*.log`, `run_L*.log`, `read_timings_L*.txt`, `timeouts.txt` (empty), `RUN_RECORD.md`, `EVAL_COPY.json`, `gestalt_confirm.txt` and `gestalt_confirm.sql` (read-only data confirm for cause 2, taken on this run's copy), `SHA256SUMS.txt`.

Never edit these files after merge.
