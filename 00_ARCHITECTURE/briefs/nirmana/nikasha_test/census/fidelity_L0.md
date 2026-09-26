# Fidelity diff: production vs sandbox census

- prod: census/L0_prod_baseline_20260926.json
- sandbox: census/L0_sandbox2_20260926.json
- sampled tables (count-dependent diffs expected): bg_muhurta_lattice, bg_synthetic_cohort_md, bodha_grounding_matches, bodha_msr_signals, bodha_signal_embeddings, chart_dashas, chart_facts, ephemeris_daily, kala_activation, kala_activation_predicates, kala_field, kala_taranga, mimamsa_fact_adjustment, mimamsa_signal_adjustment

| asset | check | prod | sandbox | class |
|---|---|---|---|---|
| bg_cohort | Count.floor | PASS | FAIL | EXPECTED (sampled — count_sql reads both bg_synthetic_cohort (full) and bg_synthetic_cohort_md (sampled); classifier only sees target_table) |
| bg_ephemeris | Count.floor | PASS | FAIL | EXPECTED (sampled) |
| bg_muhurta_lattice | Count.floor | PASS | FAIL | EXPECTED (sampled) |

**Totals:** 3 differing cells; 0 UNEXPECTED; 0 MISSING-CHECK. All three are count-dependent verdicts on sampled tables (bg_cohort's count_sql spans two tables, one of them sampled). **FIDELITY: PASS** — every full-copy verdict equals production; every diff is sampling-induced.
