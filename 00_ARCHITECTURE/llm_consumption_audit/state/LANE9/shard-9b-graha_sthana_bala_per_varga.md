# shard-9b-graha_sthana_bala_per_varga

Lane: 9b MSR ingestion. Charts: Abhisek `482012f1`, Abhinandan `1c826d5a`.

## Reproducible call
9b 5-cell recipe with `<CAT>='graha_sthana_bala_per_varga'`. chart_facts denominator: **735 / 735**.

## Verbatim results
- cell1: 1c826d5a=**378**, 482012f1=**385**
- cell2_salience: 1c826d5a="background=70, major=123, supporting=185"; 482012f1="major=194, supporting=191"
- cell5_type: composite_state (378 / 385)
- cell3_attr: "378/378", "385/385"
- cell4_domains: both "character|career"

## 5-cell verdicts
1. Consumed? **YES** — massive: 378–385 signals per chart (largest in shard).
2. Salience: on 482012f1, **194 major + 191 supporting, 0 background** — half of a 385-signal granular per-varga bala decomposition promoted to major tier.
3. Attribution: **100%** (378/378, 385/385). PASS.
4. Domain: uniform "character|career" for all ~380 signals.
5. Emergence: 735 chart_facts → ~380 signals, all composite_state, character|career. A per-varga sthana-bala decomposition (Shadbala positional-strength component, sliced per divisional chart) is among the lowest decision-weight technical scores, yet emerges as the single largest signal population in this shard.

## design_correctness_verdict: WEAK
Consumed and fully attributed, but three compounding defects: (a) DROWNED-by-volume — ~380 near-uniform signals from one technical decomposition swamp the funnel; (b) salience inflation — ~50% at major tier for granular per-varga bala; (c) uniform character|career domain default.

## Findings
- **F1 (class 7 DROWNED, HIGH):** 378–385 signals (largest population in shard) from a single per-varga positional-strength decomposition, half at major tier (482012f1: major=194). A per-varga sthana-bala figure is background-grade technical detail; promoting ~190 of them to major buries chart-defining findings. Evidence: cell1=385, cell2 "major=194, supporting=191". Rationale: an acharya would weigh aggregate Shadbala once per graha, not 385 per-varga slices at co-equal major tier.
- **F2 (class 2 WRONG, MED):** uniform character|career domain mapping; per-varga strength of a domain-specific lord never surfaces under its own domain filter. Evidence: cell4="character|career" both charts.
