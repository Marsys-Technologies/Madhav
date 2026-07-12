# Shard 9b — graha_avastha_lifetime_exposure_summary

**Shard id:** `9b-graha_avastha_lifetime_exposure_summary`
**Charts:** Abhisek `482012f1`, Abhinandan `1c826d5a`

## Exact SQL run
9b 5-cell recipe with `f.fact_category = 'graha_avastha_lifetime_exposure_summary'`; plus chart_facts COUNT.

## Verbatim results
- chart_facts rows: both 45.
- cell1: Abhisek 40, Abhinandan 32 → CONSUMED.
- cell2 salience: Abhisek `chart_defining=5, major=30, supporting=5`; Abhinandan `background=8, chart_defining=5, major=16, supporting=3`.
- cell3 attribution: Abhisek 40/40, Abhinandan 32/32 → 100%.
- cell4 domains: both `character|career`.
- cell5 type: both `composite_state`.

## Five-cell verdicts
1. Consumed? YES.
2. Salience: inflated — Abhisek 35/40 (5 chart_defining + 30 major) at major-or-above.
3. Attribution: 100%. PASS.
4. Domain: mono `character|career`.
5. Emergence: 32–40 signals, all composite_state.

## design_correctness_verdict: WEAK
Salience inflation (defect b): a lifetime-exposure SUMMARY is more decision-relevant than granular avastha, so elevated tier is partly defensible — but 35/40 (Abhisek) at major-or-above with 5 chart_defining over-weights an aggregate descriptor. Attribution exemplary.

## Findings
- **F1 (class 7 DROWNED / salience inflation) — MED.** graha_avastha_lifetime_exposure_summary: Abhisek 35/40 at major-or-above incl. 5 chart_defining. Evidence: cell2 Abhisek `chart_defining=5, major=30, supporting=5`. Repro: 5-cell recipe, fact_category='graha_avastha_lifetime_exposure_summary'. Suspected layer: ranking.
- **F2 (class 3 cross-chart tier divergence) — LOW.** Abhisek 35/40 major+ vs Abhinandan 21/32 major+ with background floor of 8; chart_defining=5 constant across both (fixed top-5 heuristic suspected). Evidence: cell2 both charts.
- **F3 (class 2 domain mis-mapping) — MED (shared).** Mono `character|career`.
