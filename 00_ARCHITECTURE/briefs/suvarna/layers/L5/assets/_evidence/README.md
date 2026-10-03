# A.L5 evidence (read-only lane track-a-l5)

All queries run through `q.sh` (role `suvarna_reader`, `SET default_transaction_read_only=on`) against the canonical chart 482012f1. No write, migration, proxy start/stop, or test/writer execution.

- `facts.py` -> `facts.json`, `facts2.py` -> `facts2.json`: every database number in the briefs (each entry holds its SQL and rows, read 2026-10-03). Query ids in backticks in the briefs are keys here.
- `collect.py`, `tables.py` -> `data/`: per-asset registry/throughput/run records and per-table profiles (columns, constraints, per-column non-null counts). Not copied into the repo.
- `offline_rollup_L5.py` -> `rollup_saved_L5.json`: main's `asset_census.py` rollup rules (REGISTRY_REVISION 16) applied to the saved census_L5.json; run with cwd = a checkout of main.
- `gen/verify_cites.py`: range-checks every `file:N` citation in the briefs against main adb0db29d; the line-content spot checks (about 150 patterns) were run ad hoc.
- `gen/`: generator for the briefs (content_*.py, render.py, build.py, index_data.py); not committed.
