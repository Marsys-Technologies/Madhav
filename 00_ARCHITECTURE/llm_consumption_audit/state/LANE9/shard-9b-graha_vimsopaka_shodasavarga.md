# shard-9b-graha_vimsopaka_shodasavarga

Lane: 9b MSR ingestion. Charts: Abhisek `482012f1`, Abhinandan `1c826d5a`.

## Reproducible call
9b 5-cell recipe with `<CAT>='graha_vimsopaka_shodasavarga'`. chart_facts denominator: **35 / 35**.

## Verbatim results
- cell1: 1c826d5a=**35**, 482012f1=**35**
- cell2_salience: 1c826d5a="background=6, major=29"; 482012f1="major=35"
- cell5_type: composite_state (35 / 35)
- cell3_attr: "35/35", "35/35"
- cell4_domains: both "character|career"

## 5-cell verdicts
1. Consumed? **YES** — 35 / 35 (1:1).
2. Salience: **482012f1 = 100% major (35/35)**; 1c826d5a = 29 major + 6 background. No discrimination.
3. Attribution: **100%** (35/35, 35/35). PASS.
4. Domain: uniform "character|career".
5. Emergence: composite_state, 1:1.

## design_correctness_verdict: WEAK
Identical profile: fully attributed, salience maximally inflated (100% major on 482012f1), uniform domain, one of four redundant vimsopaka schemes. Shodasavarga (16-varga) is the most comprehensive of the four and the only one strictly needed; the other three duplicate it at reduced varga counts.

## Findings
- **F1 (class 7 DROWNED, HIGH):** 100% major on 482012f1 (35/35) for a shodasavarga dignity average. Evidence: cell2_salience 482012f1="major=35".
- **F2 (class 7 DROWNED, HIGH — cross-category):** four-scheme vimsopaka redundancy wall (~140 near-duplicate major signals across dasavarga/saptavarga/shadvarga/shodasavarga). Flag for conductor merge.
- **F3 (class 2 WRONG, MED):** uniform character|career domain default.
