Evidence for the A.L4 briefs (Track A). NOT runnable from the repository.
The scripts here (collect.py, tables.py, upstream_receipts.py, rect_diag.py, offline_rollup_L4.py, offline_checks.py, q.sh, readers.sh, gen/) hard-code
/Users/Dev/suvarna-evidence/ and /Users/Dev/suvarna-al4/ paths and a local ~/.config/suvarna/pgenv.sh read-only database environment.
They were run once by the author (SELECT-only, role suvarna_reader). The JSON and text files in this directory are the receipts and are the evidence.
Do not wire any script here into CI or a test runner.
