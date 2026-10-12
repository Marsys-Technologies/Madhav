# L1 offline re-runs (A.L1)

Read-only, no database. Run from anywhere; `LANE` (default: the repo root inferred from this path) is the checkout whose `platform/scripts/governance/asset_census.py` (REGISTRY_REVISION 6 at base 3311b0a06) is imported.

- `offline_rollup_L1.py`: main's `rollup_census` over the saved L1 census (`census_L1.json`, with the `ga_prashna` cells from `after_reader_grant/`) and main's Dens.served rev-4 scan over the source tree -> `rollup_saved_L1.json`.
- `offline_narr_null_L1.py`: main's Null/Narr graders (`prose_checks`) over the declarations file 1.6.0 plus a DDL-derived column stand-in (`ddl_c.py`, from the E6.1 lane; best effort, renames/drops not followed) -> `narr_null_offline_L1.json`. `*` = INCONCLUSIVE (no row data).
- Both outputs mix OLD measurements with NEW rules: they are labelled "not a re-measure" wherever cited. Note the saved `ga_vargas` cells are reader-side artefacts (RLS, CF-16); the Dens re-scan is static and unaffected.
- Paths inside the saved JSON files point at the lane checkout that produced them.
