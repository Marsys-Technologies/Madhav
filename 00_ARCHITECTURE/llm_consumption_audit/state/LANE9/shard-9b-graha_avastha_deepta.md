# Shard 9b — graha_avastha_deepta

**Shard id:** `9b-graha_avastha_deepta`
**Charts:** Abhisek `482012f1`, Abhinandan `1c826d5a`

## Exact SQL run
9b 5-cell recipe with `f.fact_category = 'graha_avastha_deepta'`; plus chart_facts COUNT.

## Verbatim results
- chart_facts rows: both 45.
- cell1: Abhisek 25, Abhinandan 16 → CONSUMED.
- cell2 salience: Abhisek `chart_defining=5, major=18, supporting=2`; Abhinandan `background=5, chart_defining=5, major=5, supporting=1`.
- cell3 attribution: Abhisek 25/25, Abhinandan 16/16 → 100%.
- cell4 domains: both `character|career`.
- cell5 type: both `composite_state`.

## Five-cell verdicts
1. Consumed? YES.
2. Salience: HEAVILY inflated for Abhisek — 5 chart_defining + 18 major of 25 signals (92% at major-or-above) for a descriptive deeptaadi dignity/mood state.
3. Attribution: 100%. PASS.
4. Domain: mono `character|career`.
5. Emergence: 16–25 signals, all composite_state.

## design_correctness_verdict: WEAK
Salience inflation (defect b): deeptaadi avastha (deepta/swastha/mudita/deena/khala…) is a descriptive dignity-mood state; 5 chart_defining + 18 major for Abhisek promotes descriptive state facts to chart-defining tier. Attribution exemplary.

## Findings
- **F1 (class 7 DROWNED / salience inflation) — MED.** graha_avastha_deepta: 23/25 (Abhisek) signals at major-or-above incl. 5 chart_defining. Evidence: cell2 Abhisek `chart_defining=5, major=18, supporting=2`. Repro: 5-cell recipe, fact_category='graha_avastha_deepta'. Suspected layer: ranking.
- **F2 (class 3 INCONSISTENT — cross-chart tier divergence) — LOW.** Same category tiers very differently across charts: Abhisek 23/25 major+, Abhinandan 10/16 major+ with a background floor of 5. Evidence: cell2 both charts. May be chart-genuine but the chart_defining=5 constant across both suggests a fixed top-5 heuristic rather than chart-sensitive weighting.
- **F3 (class 2 domain mis-mapping) — MED (shared).** Mono `character|career`.
