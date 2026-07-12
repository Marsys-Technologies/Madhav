# shard-9b-graha_vimsopaka_dasavarga

Lane: 9b MSR ingestion. Charts: Abhisek `482012f1`, Abhinandan `1c826d5a`.

## Reproducible call
9b 5-cell recipe with `<CAT>='graha_vimsopaka_dasavarga'`. chart_facts denominator: **35 / 35**.

## Verbatim results
- cell1: 1c826d5a=**35**, 482012f1=**34**
- cell2_salience: 1c826d5a="background=6, major=29"; 482012f1="major=34"
- cell5_type: composite_state (35 / 34)
- cell3_attr: "35/35", "34/34"
- cell4_domains: both "character|career"

## 5-cell verdicts
1. Consumed? **YES** — 34–35 signals (1:1 with 35 chart_facts).
2. Salience: **482012f1 = 100% major (34/34)**, 1c826d5a = 29 major + 6 background. Zero discrimination — a Vimsopaka Dasavarga bala (average dignity across 10 vargas) is a background-grade technical score, yet every one is major on Abhisek's chart.
3. Attribution: **100%** (35/35, 34/34). PASS.
4. Domain: uniform "character|career".
5. Emergence: composite_state, 1:1 (no narrowing) — every vimsopaka fact becomes a major-tier signal.

## design_correctness_verdict: WEAK
Consumed and fully attributed, but salience is maximally inflated (100% major on 482012f1, no gradation) for one of the lowest decision-weight technical scores, plus uniform character|career domain, and this is one of FOUR near-duplicate vimsopaka schemes (see cross-category note) that together wall the major tier.

## Findings
- **F1 (class 7 DROWNED, HIGH):** 100% of graha_vimsopaka_dasavarga signals at major tier on 482012f1 (34/34), zero supporting/background gradation. Evidence: cell2_salience 482012f1="major=34". Rationale: vimsopaka bala is a summary dignity average an acharya treats as background context; blanket major tier is an un-justified promotion with no discrimination.
- **F2 (class 7 DROWNED, HIGH — cross-category):** dasavarga/saptavarga/shadvarga/shodasavarga are four schemes computing the SAME concept (average varga dignity) over different varga-set sizes; each emerges as ~35 major-tier signals, ~140 near-duplicate major signals total. Flag for conductor merge. Evidence: all four categories show identical cell2 "major=34/35" on 482012f1.
- **F3 (class 2 WRONG, MED):** uniform character|career domain default.
