# Suvarna Track A step 1 - Nikasha census (read-only, all layers)
Inspector commit: 2a78ec64d88e59438bd6527b4c99826432102c57 (/Users/Dev/suvarna-census). Chart scope: 482012f1-710e-4a25-994a-93821f5871aa.
Login: suvarna_reader via proxy 127.0.0.1:5433. No --emit-gaps. NIKASHA_CENSUS_TIMEOUT_SECONDS=900 (R40 env var exists; not edited). Run order L0,L1,L2,L4,L5,L3, one at a time under lock.

| Layer | Exit | Assets | FAIL | PARTIAL | NO_DETECTOR | ERRORED | PASS | N/A | NOT_GENERIC | Runtime | Output |
|---|---|---|---|---|---|---|---|---|---|---|---|
| L0 | 2 | 40 | 42 | 24 | 123 | 0 | 440 | 68 | 80 | 58s | /Users/Dev/suvarna-evidence/census/census_L0.json |
| L1 | 2 | 19 | 7 | 27 | 62 | 1 | 232 | 3 | 38 | 66s | .../census_L1.json |
| L2 | 2 | 23 | 13 | 46 | 70 | 6 | 266 | 5 | 46 | 63s | .../census_L2.json |
| L3 | 2 | 21 | 42 | 42 | 63 | 0 | 195 | 13 | 42 | 84s | .../census_L3.json |
| L4 | 2 | 9 | 18 | 25 | 27 | 0 | 89 | 0 | 18 | 19s | .../census_L4.json |
| L5 | 2 | 15 | 28 | 19 | 53 | 0 | 125 | 29 | 30 | 21s | .../census_L5.json |

Cell counts are tallied from each JSON's assets[].measurements[].v. Exit 2 = FAIL rows present = MEASURED. All six layers measured; none UNMEASURED.
Assets measured = registry active population in every layer (L0 40, L1 19, L2 23, L3 21, L4 9, L5 15; total 127).

Anomalies
- No timeouts, no connection errors, no exit 4/5/75. L3 (kala_field) ran in 84s.
- 7 ERRORED cells, all "permission denied" for suvarna_reader (grant gap, not an inspector fault):
  L1 ga_prashna Build.completion (table ga_prashna_lagna);
  L2 bo_anveshana Build.completion + Count.floor (bodha_anomalies);
  L2 bo_sangati Build.completion + Count.floor (bodha_triangulation);
  L2 bo_upaya Build.completion + Count.floor (bodha_rm_remedy_prescriptions).
  Those assets' completion/floor are unmeasured, not PASS. A SELECT grant on those 4 tables would clear them.
- L0: registered ids 36 vs 34 has_writer; bg_sign_medical registered with a writer and NEVER run by the orchestrator; 61 global runs, 0 touched L0.
- L3: 22 registered ids vs 21; ka_gochara_v3_century_materialize is registered but absent from the registry; registry has 23 L3 rows, 2 excluded as inactive/dead (ka_gochara_sweep, ka_gochara_v3_century_materialize).
- L5: 14 registered ids vs 15 assets (inspector-printed; which asset lacks a registered id was not identified; lel_events is the one non-mi_ asset). No phantoms, none excluded.
- Global runs: 61 (touched L1 519, L2 565, L3 503, L4 328, L5 422 - as printed by the inspector).
- Per-layer FAIL criteria (from logs): L0 Build.completion 14, Dens.served 23, Build.registered 2, Build.exercised 1, Count.floor 1, Vocab.alias 1; L3 Dens.served 19, Build.completion 10, Count.floor 9, Build.history 2, Build.dep_liveness 1, Idem.pattern 1; L4 Build.completion 6, Count.floor 3, Dens.served 9; L5 Build.completion 10, Build.dep_liveness 10, Build.history 8 (+others in log). Full lists in census_<L>.log beside each JSON.
- Lock /tmp/suvarna-census.lock removed after each run.
