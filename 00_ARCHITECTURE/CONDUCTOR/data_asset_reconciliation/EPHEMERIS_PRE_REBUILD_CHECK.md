---
created: 2026-05-25
session: DAR-P6-S21
---

# Ephemeris Pre-Rebuild Check

current_node_type: TRUE_NODE  # per DAR-P2-S6 baseline (node_type column absent = legacy TRUE_NODE default)
current_row_count: UNKNOWN  # DATABASE_URL not set in local env; DB unreachable from this session
bhava_chalit_null_count: UNKNOWN  # DB unreachable; DAR-P2-S6 noted bhava_chalit_house IS NULL = majority of rows
bootstrap_script_node_type: MEAN_NODE
bootstrap_script_flag: HARDCODED  # swe.MEAN_NODE is hardcoded at line 252; §4.B fix 2026-05-19; no CLI flag or env var — baked in unconditionally
bootstrap_script_path: platform/python-sidecar/pipeline/bootstrap_ephemeris.py
rebuild_required: true
rebuild_reason: "TRUE_NODE → MEAN_NODE migration required per FORENSIC v8.0 and Jyotish tradition"
expected_row_count_post_rebuild: 657450  # 73,050 days (1900-01-01..2100-12-31) × 9 planets

## Findings

### Node Type Status

The bootstrap script (line 248–252) carries this comment:

```
# §4.B 2026-05-19 fix: bootstrap previously used TRUE_NODE, which is
# osculating and occasionally turns briefly direct (contradicts the
# Jyotish always-retrograde convention). All other compute paths in this
# codebase use MEAN_NODE — bootstrap is now consistent.
r_node = swe.calc_ut(jd, swe.MEAN_NODE, flags)
```

This means the script already produces MEAN_NODE rows. The production `ephemeris_daily` table,
however, was populated by a prior run (before the §4.B fix) and therefore contains TRUE_NODE
values. The rebuild is required to bring the live table into alignment.

### Row Count Expectation

- DATE_START = 1900-01-01, DATE_END = 2100-12-31
- Days = 73,050 (verified from script constants)
- Planets per day = 9 (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu)
- Expected rows = 73,050 × 9 = 657,450

### Staging Write Path

Bootstrap writes to `ephemeris_daily_staging`. The atomic swap is performed by a separate script:
`platform/python-sidecar/pipeline/swap_ephemeris_staging.py`

The live `ephemeris_daily` table is untouched until the swap. This means a failed bootstrap leaves
production intact — only discard or re-run staging.

### No CLI Flag for Node Type

Unlike some bootstrap scripts that accept `--node-type MEAN|TRUE`, this script uses `swe.MEAN_NODE`
unconditionally as a hardcoded constant. Operator does not need to pass any special argument.
The standard invocation is sufficient (see RUNBOOK_EPHEMERIS_REBUILD_v1_0.md §2).

## Pre-Rebuild Operator Checklist

- [ ] DATABASE_URL is set and `psql "$DATABASE_URL" -c "SELECT 1;"` returns successfully
- [ ] `ephemeris_daily_staging` is empty or truncated before running bootstrap
- [ ] Disk space >= 10 GB free on the machine running the bootstrap
- [ ] pyswisseph installed: `python -c "import swisseph; print(swisseph.version)"`
- [ ] psycopg2 or psycopg installed: `python -c "import psycopg2"`
- [ ] Swiss Ephemeris data files present: `ls platform/python-sidecar/ephe/`
