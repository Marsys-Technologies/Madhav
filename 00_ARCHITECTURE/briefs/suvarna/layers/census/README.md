# Track A census evidence (2026-09-30)

Read-only censuses of all six layers, taken with the Nikaṣa inspector `platform/scripts/governance/asset_census.py` at commit
`2a78ec64d88e59438bd6527b4c99826432102c57` (branch `campaign/nikasha-test`), canonical chart
`482012f1-710e-4a25-994a-93821f5871aa`, as the read-only login `suvarna_reader`, never with `--emit-gaps`.

- `census_L0..L5.json` / `.log` and `SUMMARY.md`: the first run of every layer. The layer drafts under `../L*/` cite these paths
  as `/Users/Dev/suvarna-evidence/census/…` (the working location); the same files are here.
- `after_reader_grant/census_L1.*`, `census_L2.*`: L1 and L2 re-run after `suvarna_reader` was granted SELECT on four L1/L2 tables
  (`ga_prashna_lagna`, `bodha_anomalies`, `bodha_triangulation`, `bodha_rm_remedy_prescriptions`), which turned the 7 ERRORED cells
  of the first run into measured cells (working location `/Users/Dev/suvarna-evidence/census2/`). All other cells are identical.
