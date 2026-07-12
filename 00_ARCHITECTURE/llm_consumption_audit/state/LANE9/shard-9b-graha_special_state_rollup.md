# shard-9b-graha_special_state_rollup

Lane: 9b MSR ingestion. Charts: Abhisek `482012f1`, Abhinandan `1c826d5a`.

## Reproducible call
9b 5-cell recipe with `<CAT>='graha_special_state_rollup'`. chart_facts denominator: **225 / 225**.

## Verbatim results
- cell1: 1c826d5a=**45**, 482012f1=**34**
- cell2_salience: 1c826d5a="background=10, chart_defining=7, major=24, supporting=4"; 482012f1="chart_defining=6, major=26, supporting=2"
- cell5_type: composite_state (45 / 34)
- cell3_attr: "45/45", "34/34"
- cell4_domains: both "character|career"

## 5-cell verdicts
1. Consumed? **YES** (45 / 34 signals from 225 chart_facts each — heavy funnel narrowing 225→~40).
2. Salience: **major/chart_defining heavy** — on 482012f1, 32 of 34 (94%) sit at major(26)+chart_defining(6), only 2 supporting. Special-state rollup (avastha/combustion/etc.) mixes genuinely decision-weight states (combustion, retro) with descriptive ones; blanket major/chart_defining tiering does not discriminate.
3. Attribution: **100%** (45/45, 34/34). PASS.
4. Domain: uniform "character|career" — a combust/afflicted 2nd or 11th lord (wealth), a 7th-lord special state (marriage) etc. all collapse to character|career. Domain-blind.
5. Emergence: composite_state only; 225→~40 narrowing.

## design_correctness_verdict: WEAK
Consumed and fully attributed, but (a) salience inflation — ~94% at major/chart_defining with almost no supporting/background gradation on 482012f1; (b) domain mis-mapping — special states of domain-specific karakas/lords are all mapped to character|career, so they are UNREACHABLE under a wealth/marriage/health domain filter.

## Findings
- **F1 (class 2 WRONG, HIGH):** graha_special_state_rollup signals uniformly domain-mapped to character|career regardless of which graha's special state it is; a combust/debilitated wealth-lord special state cannot surface in a wealth-domain query. Evidence: cell4_domains="character|career" for all 34/45 signals both charts. Rationale for exceeding acharya tolerance: special-state of a bhava-lord is precisely the evidence a domain reading needs; uniform default suppresses it.
- **F2 (class 7 DROWNED, MED):** salience inflation — 482012f1 shows 32/34 at major+chart_defining, 2 supporting, 0 background; no discrimination between combustion (weighty) and benign special states. Evidence: cell2 "chart_defining=6, major=26, supporting=2".
