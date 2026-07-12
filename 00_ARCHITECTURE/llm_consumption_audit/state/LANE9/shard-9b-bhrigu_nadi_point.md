# Shard 9b — fact_category: bhrigu_nadi_point

Charts: 482012f1 (A), 1c826d5a (B)

## Exact SQL run
9b 5-cell recipe with WHERE f.fact_category='bhrigu_nadi_point' AND ms.chart_id IN (A,B); plus cell0_cf.

## Verbatim results
- cell0_cf: A=280, B=280
- cell1: A=245, B=245
- cell2_salience: A=`supporting=245`, B=`supporting=245`
- cell5_type: A=`composite_state=245`, B=`composite_state=245`
- cell3_attr: A=`245/245`, B=`245/245`
- cell4_domains: A=`character|relationship`, B=`character|relationship`

## Five-cell verdicts
1. Consumed? YES (245 both charts, 88% of cf).
2. Salience: 100% `supporting`.
3. Attribution: 100% (245/245).
4. Domain: fixed `character|relationship` for all 245 rows.
5. Emergence: 280 cf → 245 signals (88%), all `composite_state`.

## design_correctness_verdict: WEAK

## Findings
- **F1 (class 7 salience-flattening, MED):** Bhrigu Nadi is a self-contained predictive system (planet-in-sign Bhrigu points drive event timing); collapsing all 245 of its points to a single `supporting` tier (cell2) means no Bhrigu point is ever surfaced as chart-defining, deflating an entire methodology to background weight. No discrimination among 245 co-tied rows (§7.4 metric 2).
- **F2 (class 2 WRONG / domain mono-map, MED):** all 245 points tagged `character|relationship` (cell4). Bhrigu Nadi points speak to career, progeny, wealth and longevity too; a career or wealth query cannot retrieve any Bhrigu point.

completion: DONE
